import boto3
import json

# Initialize AWS clients
s3_client = boto3.client('s3')
textract_client = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    # DynamoDB table name
    table_name = 'TextractData'
    table = dynamodb.Table(table_name)

    # Process each record in the S3 event
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']

        try:
            # Call Textract to extract text from the PDF
            response = textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': bucket_name,
                        'Name': object_key
                    }
                },
                FeatureTypes=['TABLES', 'FORMS']
            )

            # Extract text blocks from the Textract response
            extracted_text = []
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    extracted_text.append(block['Text'])

            # Save extracted text to DynamoDB
            table.put_item(
                Item={
                    'DocumentId': object_key,
                    'BucketName': bucket_name,
                    'ExtractedText': '\n'.join(extracted_text)
                }
            )

            print(f"Successfully processed {object_key} and saved data to DynamoDB.")

        except Exception as e:
            print(f"Error processing {object_key}: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps('Processed S3 event and extracted data successfully!')
    }