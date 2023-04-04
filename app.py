#!/usr/bin/env python3

import aws_cdk as cdk

from cdk.cdk_pipeline import CdkPipeline

AWS_ACCOUNT = "694795848632"
AWS_REGION = "us-east-1"

app = cdk.App()

CdkPipeline(
  app, "cdk-pipeline",
  env=cdk.Environment(
      account=f"{AWS_ACCOUNT}",
      region=f"{AWS_REGION}"          
))

app.synth()
