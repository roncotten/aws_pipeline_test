import aws_cdk as cdk
from constructs import Construct
from aws_cdk.pipelines import CodePipeline, CodePipelineSource, ShellStep, CodeBuildStep
import aws_cdk.aws_codebuild as codebuild 
import aws_cdk.aws_ecr as ecr
from .cdk_application import CdkApplication

source_arn = "arn:aws:codestar-connections:us-east-1:694795848632:connection/81ecfe62-c1d4-49f4-bd33-9ee83d1568c9"

AWS_ACCOUNT = "694795848632"
AWS_REGION = "us-east-1"

class CdkPipeline(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #ecr_repo = ecr.Repository(self, "cdk-repo")

        build_spec=codebuild.BuildSpec.from_object({
            "version": "0.2",
            "env": {
                "exported-variables": [
                 ]
            },
            "phases": {
                "build": {
                    "commands": [
                      "pwd",
                      "ls -lsF"
                    ]
                }
            }
        })

        pipeline = CodePipeline(self, "cdk-pipeline",
                        pipeline_name="cdk-pipeline",
                        synth=CodeBuildStep("Synth",
                            input=CodePipelineSource.connection("roncotten/aws_pipeline_test", "main", connection_arn=f"{source_arn}"),
                            build_environment=codebuild.BuildEnvironment(
                              build_image=codebuild.LinuxBuildImage.STANDARD_5_0
                            ),
                            partial_build_spec=build_spec,
                            commands=[]
                        )
                    )

        pipeline.add_stage(
          CdkApplication(
              self,"DeployApplication",
              env=cdk.Environment(
                 account=f"{AWS_ACCOUNT}",
                 region=f"{AWS_REGION}"
              )
          )
        )

