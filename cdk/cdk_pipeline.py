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
source_repo = 'aws_pipeline_test'
source_branch = 'main'
source_repo_owner = 'roncotten'
source_arn = 'arn:aws:codestar-connections:us-east-1:694795848632:connection/81ecfe62-c1d4-49f4-bd33-9ee83d1568c9'
ecr_repo_name = 'ecosphere'
vpc_id='vpc-0c3094b44d23a611a'


class CdkPipeline(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #########################################################################################################
        # stack resources 
        #########################################################################################################

        # get context variables
        common = self.node.try_get_context('COMMON')
        aws_account = common.get('AWS_ACCOUNT')
        aws_region = common.get('AWS_REGION')
        client = common.get('client')
        application = common.get('application')
        environments = self.node.try_get_context('ENVIRONMENTS')
        environment = environments.get('dev')
        environment_label = environment.get('label')
        stack = common.get('stack')
        deployment = client + '-' + application + '-' + environment_label + '-' + stack

        # create ecr repo
        ecr_repo = ecr.Repository(self, deployment+"-ecr", repository_name=deployment, image_scan_on_push=True, removal_policy=cdk.RemovalPolicy.DESTROY)

        # create ecs cluster
        vpc = ec2.Vpc.from_lookup(self, deployment+"-vpc", vpc_id=vpc_id)
        ecs_cluster = ecs.Cluster(self, deployment+"-ecs", cluster_name=deployment, container_insights=True, vpc=vpc)

        # create fargate alb service
        execution_policy = iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name = "service-role/AmazonECSTaskExecutionRolePolicy")
        ecs_role = iam.Role(self, deployment+"-ecs_role",
                                  assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
                                  managed_policies=[execution_policy], role_name=deployment+"-ecs_role"
                                  )
        ecs_image = ecs.ContainerImage.from_registry("694795848632.dkr.ecr.us-east-1.amazonaws.com/doi-ecosphere-d-1:latest")
        ecs_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, 
            deployment+"-ecs_service",
            service_name = deployment+"-service",
            #task_definition=alb_task_definition,
            task_image_options= {
                "image": ecs_image,
                "container_name": deployment+"-app",
                "container_port": 80,
                "execution_role": ecs_role,
                "enable_logging": True
                #"execution_role": ""
                #"task_role": ""
            },
            assign_public_ip=True,
            desired_count = 1,
            listener_port = 80,
            cluster=ecs_cluster
        )
        fargateservice = alb_fargate_service.service


        #########################################################################################################
        # codebuild project
        #########################################################################################################

        codebuild_project = codebuild.PipelineProject(self, "Build", project_name=deployment,
            environment=codebuild.BuildEnvironment(
                privileged=True
            ),
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "build": {
                        "commands": [
                            "$(aws ecr get-login --region $AWS_REGION --no-include-email)",
                            "cd build",
                            "docker build -t $REPOSITORY_URI:latest .",
                            "docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "docker push $REPOSITORY_URI:latest",
                            "docker push $REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION",
                            "export imageTag=$CODEBUILD_RESOLVED_SOURCE_VERSION",
                            "cd ..",
                            "pwd",
                            "printf '[{\"name\":\"app\",\"imageUri\":\"%s\"}]' $REPOSITORY_URI:$imageTag > imagedefinitions.json",
                            "ls -lsF"
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
                    value=aws_region
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
          branch=source_branch,
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
        deploy_action = codepipeline_actions.EcsDeployAction(
          action_name="Deploy",
          service=ecs_service,
          input=codepipeline.Artifact("imagedefinitions")
        )

        # create pipeline 
        codepipeline.Pipeline(self, deployment+"-pipeline", pipeline_name=deployment,
            stages=[
              {
                "stageName": "source",
                "actions": [source_action]
              }, 
              {
                "stageName": "build",
                "actions": [build_action]
              }, 
              {
                "stageName": "deploy",
                "actions": [deploy_action]
              }
            ]
        )

