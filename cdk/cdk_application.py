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
        super().__init__(scope, construct_id, **kwargs)

        app_stack = CdkApplicationStack(self, "DeployApplication")

class CdkApplicationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #sns_topic_name = kwargs.pop('sns_topic_name')
        #print(sns_topic_name)
        topic = sns.Topic( self, 'cdk-topic' )
