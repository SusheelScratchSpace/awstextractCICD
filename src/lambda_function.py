import boto3
import json

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TextractData')

    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        object_key = record['s3']['object']['key']

        # Example: Save S3 object details to DynamoDB
        table.put_item(
            Item={
                'DocumentId': object_key,
                'BucketName': bucket_name
            }
        )

    return {
        'statusCode': 200,
        'body': json.dumps('Processed S3 event successfully!')
    }