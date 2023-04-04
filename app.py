#!/usr/bin/env python3

import aws_cdk as cdk

from cdk.cdk_stack_1 import CdkStack1
from cdk.cdk_stack_2 import CdkStack2

AWS_ACCOUNT = "694795848632"
AWS_REGION = "us-east-1"

app = cdk.App()

CdkStack1(
  app, "cdk-stack-1",
  env=cdk.Environment(
      account=f"{AWS_ACCOUNT}",
      region=f"{AWS_REGION}"          
))

'''
CdkStack2(
  app, "cdk-stack-2",
  env=cdk.Environment(
      account=f"{AWS_ACCOUNT}",
      region=f"{AWS_REGION}"
  ),
  sns_topic_name="test"
)
'''

app.synth()
