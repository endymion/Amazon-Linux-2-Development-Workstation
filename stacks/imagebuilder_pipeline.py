import os

from aws_cdk import (
    core,
    aws_imagebuilder as imagebuilder,
    aws_iam as iam,
    aws_ec2 as ec2
)

class ImageBuilderPipeline(core.Stack):

    def __init__(self,
        scope: core.Construct,
        id: str,
        bucket_name: str,
        components_prefix: str,
        base_image_arn: str,
        image_pipeline_name: str,
        instance_type: str,
        **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        bucket_uri = "s3://" + bucket_name + "/" + components_prefix

        # NOTE: when creating components, version number is supplied manually. If you update the components yaml and
        # need a new version deployed, version need to be updated manually.

        component_tools_uri = bucket_uri + '/common-tools.yml'
        component_tools = imagebuilder.CfnComponent(self,
            "common-tools",
            name="Common Tools",
            platform="Linux",
            version="1.0.1",
            uri=component_tools_uri
        )

        component_cdk_uri = bucket_uri + '/cdk.yml'
        component_cdk = imagebuilder.CfnComponent(self,
            "cdk",
            name="AWS CDK",
            platform="Linux",
            version="1.0.0",
            uri=component_cdk_uri
        )

        component_ruby_uri = bucket_uri + '/ruby.yml'
        component_ruby = imagebuilder.CfnComponent(self,
            "Ruby - rbenv",
            name="rbenv",
            platform="Linux",
            version="1.0.0",
            uri=component_ruby_uri
        )

        component_docker_uri = bucket_uri + '/docker-compose.yml'
        component_docker = imagebuilder.CfnComponent(self,
            "Docker",
            name="docker",
            platform="Linux",
            version="1.0.0",
            uri=component_docker_uri
        )

        component_sam_uri = bucket_uri + '/sam.yml'
        component_sam = imagebuilder.CfnComponent(self,
            "SAM",
            name="sam",
            platform="Linux",
            version="1.0.1",
            uri=component_sam_uri
        )

        recipe = imagebuilder.CfnImageRecipe(self,
            "AmazonLinux2-x86-Development-Workstation-Recipe",
            name="AmazonLinux2-x86-Development-Workstation-Recipe",
            version="1.0.1",
            components=[
                {"componentArn": "arn:aws:imagebuilder:us-east-1:aws:component/chrony-time-configuration-test/1.0.0"},
                {"componentArn": "arn:aws:imagebuilder:us-east-1:aws:component/amazon-cloudwatch-agent-linux/1.0.0"},
                {"componentArn": "arn:aws:imagebuilder:us-east-1:aws:component/python-3-linux/1.0.2"},
                {"componentArn": "arn:aws:imagebuilder:us-east-1:aws:component/nodejs-12-lts-linux/1.0.1"},
                {"componentArn": component_tools.attr_arn},
                {"componentArn": component_ruby.attr_arn},
                {"componentArn": component_cdk.attr_arn},
                {"componentArn": component_docker.attr_arn},
                {"componentArn": component_sam.attr_arn}
            ],
            parent_image=base_image_arn
        )

        # below role is assumed by ec2 instance
        role = iam.Role(self, "AmazonLinux2-x86-Development-Workstation-Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("EC2InstanceProfileForImageBuilder"))

        # Create an instance profile to attach the role
        instanceprofile = iam.CfnInstanceProfile(self,
            "AmazonLinux2-x86-Development-Workstation-InstanceProfile",
            instance_profile_name="AmazonLinux2-x86-Development-Workstation-InstanceProfile",
            roles=[role.role_name])

        # Create a VPC and security group
        vpc = ec2.CfnVPC(self,
            'AmazonLinux2-x86-Development-Workstation-VPC',
            cidr_block="10.0.0.0/16",
            enable_dns_hostnames=True,
            enable_dns_support=True)

        # Create routing table for public subnet
        route_table_public = ec2.CfnRouteTable(
            self,
            "AmazonLinux2-x86-Development-Workstation-RouteTable",
            vpc_id=vpc.ref
        )

        public_subnet = ec2.CfnSubnet(
            self,
            "AmazonLinux2-x86-Development-Workstation-Subnet",
            cidr_block="10.0.0.0/24",
            vpc_id=vpc.ref,
            availability_zone="us-east-1e",
            map_public_ip_on_launch=True
        )

        # Create Elastic ip
        eip = ec2.CfnEIP(
            self,
            "AmazonLinux2-x86-Development-Workstation-ElasticIP",
            domain='vpc'
        )
        # Add a dependency on the VPC to encure allocation happens before the VPC is created.
        vpc.node.add_dependency(eip)

        # Create internet gateway
        inet_gateway = ec2.CfnInternetGateway(
            self,
            "rds-igw",
            tags=[core.CfnTag(key="Name",value="rds-igw")]
        )

        # Attach internet gateway to vpc
        ec2.CfnVPCGatewayAttachment(
            self,
            "igw-attachment",
            vpc_id=vpc.ref,
            internet_gateway_id=inet_gateway.ref
        )

        # Create NAT gateway, attach elastic-ip, public subnet
        nat_gateway = ec2.CfnNatGateway(
            self,
            "natgateway",
            allocation_id=eip.attr_allocation_id,
            subnet_id=public_subnet.ref
        )

        ec2.CfnSubnetRouteTableAssociation(
            self,
            "rtb-assoc-public",
            route_table_id=route_table_public.ref,
            subnet_id=public_subnet.ref
        )

        # Create a new public route to use the internet gateway
        ec2.CfnRoute(
            self,
            "public-route",
            route_table_id=route_table_public.ref,
            gateway_id=inet_gateway.ref,
            destination_cidr_block="0.0.0.0/0"
        )

        webserver_sec_group = ec2.CfnSecurityGroup(
            self,
            "development-workstation-security-group",
            group_description="development workstation security group",
            vpc_id=vpc.ref
        )

        # Restrict SSH port access to only yourself
        ssh_ingress = ec2.CfnSecurityGroupIngress(
            self,
            "sec-group-ssh-ingress",
            ip_protocol="tcp",
            cidr_ip="0.0.0.0/0",
            from_port=22,
            to_port=22,
            group_id=webserver_sec_group.ref
        )
        # Allow http to internet
        http_ingress = ec2.CfnSecurityGroupIngress(
            self,
            "sec-group-http-ingress",
            ip_protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_ip="0.0.0.0/0",
            group_id=webserver_sec_group.ref
        )
        # Allow https to internet
        https_ingress = ec2.CfnSecurityGroupIngress(
            self,
            "sec-group-https-ingress",
            ip_protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_ip="0.0.0.0/0",
            group_id=webserver_sec_group.ref
        )

        webserver_sec_group.tags.set_tag(key="Name",value="sg-amazon-linux-2-development-workstation")

        # Create infrastructure configuration to supply instance type
        infraconfig = imagebuilder.CfnInfrastructureConfiguration(self,
            "AmazonLinux2-x86-Development-Workstation-InfrastructureConfig",
            name="AmazonLinux2-x86-Development-Workstation-InfrastructureConfig",
            instance_types=[instance_type],
            instance_profile_name="AmazonLinux2-x86-Development-Workstation-InstanceProfile",
            subnet_id=public_subnet.ref,
            security_group_ids=[webserver_sec_group.ref],
            terminate_instance_on_failure=False
        )

        # infrastructure need to wait for instance profile to complete before beginning deployment.
        infraconfig.add_depends_on(instanceprofile)

        # build the imagebuilder pipeline
        pipeline = imagebuilder.CfnImagePipeline(self,
            "AmazonLinux2-x86-Development-Workstation-ImagePipeline",
            name=image_pipeline_name,
            image_recipe_arn=recipe.attr_arn,
            infrastructure_configuration_arn=infraconfig.attr_arn
        )

        pipeline.add_depends_on(infraconfig)
