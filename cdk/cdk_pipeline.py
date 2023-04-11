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

'''
TODO

1. Add subnet configuration option
2. Add security configuration option
3. Add task configuration options
4. Add ALB configuration options
5. Add WAF deployment/configuration options
6. Add CloudWatch monitoring and notifications
7. Add Route53 confguration options
8. Add certification configuration option
9. Add http redirect option
10. Add tags
'''

class CdkPipeline(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # get context variables
        stack_context = self.node.try_get_context('environment')
        if stack_context == None:
          print('\nusage: cdk [synth|deploy] --context environment=[environment] --context deploy=[true|false]')
          print('  --context environment=[environment] required')
          exit(1)

        deploy = self.node.try_get_context('deploy')
        common = self.node.try_get_context('COMMON')
        client = common.get('client')
        application = common.get('application')
        source_repo = common.get('source_repo')
        source_repo_owner = common.get('source_repo_owner')
        source_arn = common.get('source_arn')
        stacks = self.node.try_get_context('STACKS')
        stack = stacks.get(stack_context)
        aws_account = stack.get('aws_account')
        aws_region = stack.get('aws_region')
        environment = stack.get('environment')
        stack_number = stack.get('stack')
        vpc_id = stack.get('vpc_id')
        container_port = stack.get('container_port')
        listener_port = stack.get('listener_port')
        task_count = stack.get('task_count')
        task_cpu = stack.get('task_cpu')
        task_memory = stack.get('task_memory')
        public_ip = stack.get('assign_public_ip')

        source_branch = stack.get('source_branch')
        deployment = client + '-' + application + '-' + environment + '-' + stack_number

        # create ecr repo
        ecr_repo = ecr.Repository(self, deployment+"-ecr", repository_name=deployment, image_scan_on_push=True)

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
                          "cd ..",
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
                  value=aws_region
              ),
              "REPOSITORY_URI": codebuild.BuildEnvironmentVariable(
                  value=ecr_repo.repository_uri
              )
            }
        )

        # grant docker push to ecr_repo
        ecr_repo.grant_pull_push(codebuild_project)

        # create ecs cluster
        vpc = ec2.Vpc.from_lookup(self, deployment+"-vpc", vpc_id=vpc_id)
        ecs_cluster = ecs.Cluster(self, deployment+"-ecs", cluster_name=deployment, container_insights=True, vpc=vpc)
        execution_policy = iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name = "service-role/AmazonECSTaskExecutionRolePolicy")
        ecs_role = iam.Role(self, deployment+"-ecs_role",
                                assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
                                managed_policies=[execution_policy], role_name=deployment+"-ecs_role"
                              )
        #ecs_image = ecs.ContainerImage.from_registry("694795848632.dkr.ecr.us-east-1.amazonaws.com/doi-ecosphere-d-1:latest")
        ecs_image = ecs.ContainerImage.from_registry(aws_account + ".dkr.ecr." + aws_region + ".amazonaws.com/" + deployment + ":latest")

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

        # create pipeline
        pipeline = codepipeline.Pipeline(self, deployment+"-pipeline", pipeline_name=deployment,
            stages=[
              {
                "stageName": "source",
                "actions": [source_action]
              },
              {
                "stageName": "build",
                "actions": [build_action]
              },
            ]
          )

        if deploy == 'true':

          # create fargate task execution policy and role
          '''
          task_policy = iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name = "service-role/AmazonECSTaskExecutionRolePolicy")
          task_role = iam.Role(self, deployment+"-ecs_role",
                                 assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
                                 managed_policies=[task_execution_policy], role_name=deployment+"-task_execution_role"
                               )
          '''
          # create fargate service
          alb_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            deployment+"-ecs_service",
            cluster=ecs_cluster,
            service_name = deployment+"-service",
            task_image_options= {
                "image": ecs_image,
                "container_name": "app",
                "container_port": container_port,
                "execution_role": ecs_role,
                #"task_role": task_role,
                "enable_logging": True
            },
            load_balancer_name=deployment,
            desired_count = task_count,
            cpu = task_cpu,
            memory_limit_mib = task_memory,
            listener_port = listener_port,
            assign_public_ip = public_ip
          )
          fargate_service = alb_fargate_service.service

          deploy_action = codepipeline_actions.EcsDeployAction(
            action_name="Deploy",
            service=fargate_service,
            input=codepipeline.Artifact("imagedefinitions")
          )

          pipeline.add_stage(
            stage_name="deploy",
            actions=[deploy_action]
          )

