import os
import json
import base64
import logging

# Read environment variables
STREAM_NAME = os.environ['STREAM_NAME']
LOG_LEVEL = os.environ['LOG_LEVEL']

logger = logging.getLogger()
if logging._checkLevel(LOG_LEVEL):
    logger.setLevel(LOG_LEVEL)
else:
    logger.setLevel(logging.INFO)
 
logging.info(f'Setting Logger Level to {logging.getLevelName(logger.level)}')

import boto3

print(f'boto3 version: {boto3.__version__}')

try:
    kinesis_client = boto3.client('kinesis')
except:
    logging.error('Failed to instantiate kinesis client!')

logging.info(f'Lambda will forward data to Kinesis name: {STREAM_NAME}')

def lambda_handler(event, context):
    logging.debug('Received event: {}'.format(json.dumps(event, indent=2)))

    records = []
    for rec in event['records'].values():
        for part in rec:
            # Each record has separate eventID, etc.
            topic = part['topic']
            partition = part['partition']
            offset = part['offset']
            logging.debug(f'topic: {topic}, partition: {partition}, offset: {offset}')
    
            agg_data_bytes = base64.b64decode(part['value'])
            decoded_data = agg_data_bytes.decode(encoding="utf-8")
            records.append({
                'Data': decoded_data,
                'PartitionKey': 'shard1'
            })
    
    response = kinesis_client.put_records(StreamName = STREAM_NAME, Records = records)
    if (response['ResponseMetadata']['HTTPStatusCode'] != 200):
        logger.error("ERROR: Kinesis put_record failed: \n{}".format(json.dumps(response)))
        return {'statusCode': 500, 'body': "ERROR: Kinesis put_record failed: \n{}".format(json.dumps(response))}

    logging.info(f'Number of records forwarded to stream {STREAM_NAME}: {len(records)}')

    return {'statusCode': 200}