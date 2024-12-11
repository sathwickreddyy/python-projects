import boto3
import logging

class SNSManager:
    def __init__(self, sns_topic_arn, region_name='ap-southeast-2'):
        self.sns_client = boto3.client('sns', region_name=region_name)
        self.sns_topic_arn = sns_topic_arn

    def send_message(self, subject, message):
        """
        Publish a message to the SNS topic.
        """
        try:
            response = self.sns_client.publish(
                TopicArn=self.sns_topic_arn,
                Message=message,
                Subject=subject
            )
            logging.info(f"SNS message sent. Message ID: {response['MessageId']}")
        except Exception as e:
            logging.error(f"Failed to send SNS message: {e}")
