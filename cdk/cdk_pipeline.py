import aws_cdk as cdk
from constructs import Construct
from aws_cdk.pipelines import CodePipeline, CodePipelineSource, ShellStep
from .cdk_application import CdkApplication

source_arn = "arn:aws:codestar-connections:us-east-1:694795848632:connection/81ecfe62-c1d4-49f4-bd33-9ee83d1568c9"

AWS_ACCOUNT = "694795848632"
AWS_REGION = "us-east-1"

class CdkPipeline(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pipeline = CodePipeline(self, "cdk-pipeline",
                        pipeline_name="cdk-pipeline",
                        synth=ShellStep("Synth",
                            input=CodePipelineSource.connection("roncotten/aws_pipeline_test", "main", connection_arn=f"{source_arn}"),
                            commands=["npm install -g aws-cdk",
                                "python -m pip install -r requirements.txt",
                                "cdk synth"]
                        )
                    )

        pipeline.add_stage(
          CdkApplication(
              self,"DeployApplication",
              env=cdk.Environment(
                 account=f"{AWS_ACCOUNT}",
                 region=f"{AWS_REGION}" 
              ),
              sns_topic='my_topic'
          )
        )


