#!/usr/bin/env python3
import aws_cdk as cdk
from cdk.cdk_pipeline import CdkPipeline

app = cdk.App()

# get context variables
stack_context = app.node.try_get_context('environment')
if stack_context == None:
  print('\nusage: cdk [synth|deploy] --context environment=[environment] --context deploy=[true|false]')
  print('  --context environment=[environment] required')
  exit(1)
common = app.node.try_get_context('COMMON')
client = common.get('client')
application = common.get('application')
stacks = app.node.try_get_context('STACKS') 
stack = stacks.get(stack_context)
aws_account = stack.get('aws_account')
aws_region = stack.get('aws_region')
environment = stack.get('environment')
stack_number = stack.get('stack')
deployment = client + '-' + application + '-' + environment + '-' + stack_number

# create pipeline
CdkPipeline(
  app, deployment,
  env=cdk.Environment(
      account=aws_account,
      region=aws_region
))

app.synth()
