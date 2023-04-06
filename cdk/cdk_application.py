import os
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

        app_stack = CdkApplicationStack(self, "CdkApplicationStack")

class CdkApplicationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
       
        topic = sns.Topic(self, 'my-topic-1')
        topic = sns.Topic(self, 'my-topic-2')
        topic = sns.Topic(self, 'my-topic-3')
