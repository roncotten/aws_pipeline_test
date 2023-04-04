import aws_cdk as cdk
from constructs import Construct
from aws_cdk.pipelines import CodePipeline, CodePipelineSource, ShellStep
from .cdk_application import CdkApplication
import aws_cdk.aws_ecr as ecr

source_arn = "arn:aws:codestar-connections:us-east-1:694795848632:connection/81ecfe62-c1d4-49f4-bd33-9ee83d1568c9"

AWS_ACCOUNT = "694795848632"
AWS_REGION = "us-east-1"

class CdkPipeline(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ecr_repo = ecr.Repository(self, "cdk-repo")

        pipeline = CodePipeline(self, "cdk-pipeline",
                        pipeline_name="cdk-pipeline",
                        #synth=ShellStep("Synth",
                        #    input=CodePipelineSource.connection("roncotten/aws_pipeline_test", "main", connection_arn=f"{source_arn}"),
                        #    shell_commands = "./build.sh " + ecr_repo.repository_uri
                        #    commands=[ shell_commands ]
                        #)
                    )

        build_project = codebuild.PipelineProject(self, "Build", build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"))

        pipeline.add_stage(
          stage_name="Build",
          actions=[
              codepipeline_actions.CodeBuildAction(
                  action_name="Build",
                  project=build_project,
                  input=source_output,
                  outputs=[build_output],
              )
          ],
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


