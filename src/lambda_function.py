import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    # Initialize AWS clients
    textract = boto3.client('textract')
    dynamodb = boto3.resource('dynamodb')
    s3 = boto3.client('s3')
    
    # Get environment variables
    table_name = os.environ['DYNAMODB_TABLE']
    table = dynamodb.Table(table_name)
    
    try:
        # Get the S3 bucket and file name from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        document = event['Records'][0]['s3']['object']['key']
        
        # Call Amazon Textract
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': document
                }
            }
        )
        
        # Extract text from Textract response
        extracted_text = []
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                extracted_text.append(item['Text'])
        
        # Store results in DynamoDB
        table.put_item(
            Item={
                'DocumentId': document,
                'Bucket': bucket,
                'ExtractedText': extracted_text,
                'ProcessedTime': datetime.utcnow().isoformat()
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps('Document processed successfully')
        }
        
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing document: {str(e)}')
        }