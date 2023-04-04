from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_sns as sns,
)


class CdkStack2(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        sns_topic_name = kwargs.pop('sns_topic_name')
        print(sns_topic_name)
        topic = sns.Topic(
            self, sns_topic_name
        )
