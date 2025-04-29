import json
import boto3
import os
import logging
from datetime import datetime
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def validate_s3_bucket(bucket_name):
    """Validate S3 bucket exists and is accessible"""
    s3 = boto3.client('s3')
    try:
        s3.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        logger.error(f"Error checking bucket {bucket_name}: {str(e)}")
        return False

def validate_dynamodb_table(table_name):
    """Validate DynamoDB table exists and is accessible"""
    dynamodb = boto3.client('dynamodb')
    try:
        dynamodb.describe_table(TableName=table_name)
        return True
    except ClientError as e:
        logger.error(f"Error checking table {table_name}: {str(e)}")
        return False

def process_textract_response(response):
    """Process Textract response and extract text"""
    extracted_text = []
    if 'Blocks' in response:
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                extracted_text.append(item['Text'])
    return extracted_text

def lambda_handler(event, context):
    """Main Lambda handler for processing documents with Textract"""
    logger.info("Starting document processing")
    logger.info(f"Event: {json.dumps(event)}")

    # Initialize AWS clients
    textract = boto3.client('textract')
    dynamodb = boto3.resource('dynamodb')
    
    # Get environment variables
    table_name = os.environ.get('DYNAMODB_TABLE', 'TextractData')
    table = dynamodb.Table(table_name)
    
    try:
        # Validate event structure
        if not event.get('Records', []):
            raise ValueError("No records found in event")

        # Get S3 event details
        s3_event = event['Records'][0]['s3']
        bucket = s3_event['bucket']['name']
        document = s3_event['object']['key']
        
        # Validate resources
        if not validate_s3_bucket(bucket):
            raise Exception(f"Invalid S3 bucket: {bucket}")
        
        if not validate_dynamodb_table(table_name):
            raise Exception(f"Invalid DynamoDB table: {table_name}")
        
        logger.info(f"Processing document: {document} from bucket: {bucket}")
        
        # Call Textract
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': document
                }
            }
        )
        
        # Process Textract response
        extracted_text = process_textract_response(response)
        
        # Store results
        item = {
            'DocumentId': document,
            'Bucket': bucket,
            'ExtractedText': extracted_text,
            'ProcessedTime': datetime.utcnow().isoformat(),
            'Status': 'COMPLETED'
        }
        
        table.put_item(Item=item)
        logger.info(f"Successfully processed document: {document}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document processed successfully',
                'documentId': document,
                'textCount': len(extracted_text)
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        error_response = {
            'error': str(e),
            'documentId': document if 'document' in locals() else 'unknown'
        }
        
        # Log error to DynamoDB
        try:
            if validate_dynamodb_table(table_name):
                table.put_item(
                    Item={
                        'DocumentId': error_response['documentId'],
                        'Error': str(e),
                        'ProcessedTime': datetime.utcnow().isoformat(),
                        'Status': 'ERROR'
                    }
                )
        except Exception as db_error:
            logger.error(f"Error logging to DynamoDB: {str(db_error)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps(error_response)
        }