import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_ec2 as ec2 
)
from .cdk_application import CdkApplication


AWS_ACCOUNT = "694795848632"
AWS_REGION = "us-east-1"
source_arn = "arn:aws:codestar-connections:us-east-1:694795848632:connection/81ecfe62-c1d4-49f4-bd33-9ee83d1568c9"

class CdkPipeline(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ecr repo
        ecr_repo = ecr.Repository(self, "cdk-repo")

        # codebuild project
        codebuild_project = codebuild.PipelineProject(self, "codebuild" ,project_name="codebuild",
            environment=codebuild.BuildEnvironment(
                privileged=True
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "build": {
                        "commands": [
                            "pwd",
                            "ls -lsF"
                        ]
                    },
                    "post_build": {
                        "commands": [
                        ]
                    }
                },
                "env": {
                     "exported-variables": ["imageTag"]
                },
                "artifacts": {
                    "files": "imagedefinitions.json",
                    "secondary-artifacts": {
                        "imagedefinitions": {
                            "files": "imagedefinitions.json",
                            "name": "imagedefinitions"
                        }
                    }
                }
            }),
            environment_variables={
                "REPOSITORY_URI": codebuild.BuildEnvironmentVariable(
                    value=ecr_repo.repository_uri
                )
            }
        )

        # source action 
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
          action_name="Clone",
          connection_arn=source_arn,
          owner='roncotten',
          repo='aws_pipeline_test',
          branch='main',
          output=source_output,
          code_build_clone_output=True
        )

        # build action
        build_action = codepipeline_actions.CodeBuildAction(
            action_name="Build",
            project=codebuild_project,
            input=source_output,
            outputs=[codepipeline.Artifact("imagedefinitions")],
            execute_batch_build=False
        )


        # create pipeline 
        codepipeline.Pipeline(self, "codepipeline", pipeline_name="codepipeline",
            stages=[
              {
                "stageName": "source",
                "actions": [source_action]
              }, 
              {
                "stageName": "build",
                "actions": [build_action]
              }, 
              #{
              #  "stageName": "deploy",
              #  "actions": [deploy_action]
              #}
            ]
        )

