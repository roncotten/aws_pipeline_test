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
    aws_ec2 as ec2, 
    aws_sns as sns
)

# global variables
AWS_ACCOUNT = '694795848632'
AWS_REGION = 'us-east-1'
source_repo = 'aws_pipeline_test'
source_branch = 'main'
source_repo_owner = 'rcotten'
source_arn = 'arn:aws:codestar-connections:us-east-1:694795848632:connection/81ecfe62-c1d4-49f4-bd33-9ee83d1568c9'
ecr_repo_name = 'ecosphere'
vpc_id='vpc-0c3094b44d23a611a'


class CdkPipeline(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #########################################################################################################
        # stack resources 
        #########################################################################################################

        # ecr repo
        ecr_repo = ecr.Repository(self, ecr_repo_name)

        # ecs cluster
        vpc = ec2.Vpc.from_lookup(self, "cs-d-1-vpc", vpc_id=vpc_id)
        ecs_cluster = ecs.Cluster.from_cluster_attributes(self,"cs-d-1-ecs" ,cluster_name="cs-d-1",vpc=vpc, security_groups=[])


        #########################################################################################################
        # codebuild project
        #########################################################################################################

        codebuild_project = codebuild.PipelineProject(self, "Build" ,project_name="codebuild",
            environment=codebuild.BuildEnvironment(
                privileged=True
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "build": {
                        "commands": [
                            "$(aws ecr get-login --region $AWS_REGION --no-include-email)",
                            "pwd",
                            "ls -lsR *",
                            "docker build -t $REPOSITORY_URI:latest .",
                            "docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "docker push $REPOSITORY_URI:latest",
                            "docker push $REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION",
                            "export imageTag=$CODEBUILD_RESOLVED_SOURCE_VERSION",
                            "printf '[{\"name\":\"app\",\"imageUri\":\"%s\"}]' $REPOSITORY_URI:$imageTag > imagedefinitions.json"
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
                "AWS_REGION": codebuild.BuildEnvironmentVariable(
                    value=f"{AWS_REGION}"
                ),
                "REPOSITORY_URI": codebuild.BuildEnvironmentVariable(
                    value=ecr_repo.repository_uri
                )
              }
        )

        # grant docker push to ecr_repo
        ecr_repo.grant_pull_push(codebuild_project)


        #########################################################################################################
        # pipeline
        #########################################################################################################

        # source action 
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
          action_name="Clone",
          connection_arn=source_arn,
          repo=source_repo,
          branch="main",
          owner=source_repo_owner,
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

        # deploy action
        #deploy_action = codepipeline_actions.EcsDeployAction(
        #  action_name="Deploy",
        #  service=kc_ecs_service
        #  input=codepipeline.Artifact("imagedefinitions")
        #)

        # create pipeline 
        codepipeline.Pipeline(self, "codepipeline", pipeline_name="cdk-pipeline",
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

