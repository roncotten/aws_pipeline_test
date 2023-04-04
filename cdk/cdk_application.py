import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_sns as sns,
)

class CdkApplication(cdk.Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, sns_topic, **kwargs)

        app_stack = CdkApplicationStack(self, "CdkApplicationStack",  sns_topic, **kwargs)

class CdkApplicationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, sns_topic, **kwargs) -> None:
        super().__init__(scope, construct_id, sns_topic, **kwargs)
       
        #sns_topic = kwargs.get('sns_topic')
        topic = sns.Topic(self, sns_topic)
