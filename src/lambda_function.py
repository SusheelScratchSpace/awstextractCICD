import boto3
import json
import os

s3 = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')

# DynamoDB table name from environment variables
TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    # Log the event
    print("Event: ", json.dumps(event))

    # Get bucket name and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    try:
        # Call Textract to analyze the document
        response = textract.analyze_document(
            Document={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': object_key
                }
            },
            FeatureTypes=["TABLES", "FORMS"]
        )

        # Extract data from Textract response
        extracted_data = extract_data_from_textract(response)

        # Store the extracted data in DynamoDB
        table.put_item(Item={
            'DocumentId': object_key,
            'ExtractedData': extracted_data
        })

        print(f"Successfully processed {object_key} and stored data in DynamoDB.")
    except Exception as e:
        print(f"Error processing {object_key}: {str(e)}")
        raise

def extract_data_from_textract(response):
    # Extract relevant data from Textract response
    extracted_data = []
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            extracted_data.append(block['Text'])
    return extracted_data