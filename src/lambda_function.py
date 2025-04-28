import json
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    # Initialize AWS clients
    textract = boto3.client('textract')
    dynamodb = boto3.resource('dynamodb')
    
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
        
        # Process the response
        text_blocks = []
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                text_blocks.append(block['Text'])
                
        # Store results in DynamoDB
        table.put_item(
            Item={
                'DocumentId': f"{document}-{datetime.now().isoformat()}",
                'Bucket': bucket,
                'Document': document,
                'TextBlocks': text_blocks,
                'ProcessedAt': datetime.now().isoformat()
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