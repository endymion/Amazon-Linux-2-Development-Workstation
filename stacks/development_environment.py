import os

from aws_cdk import (
    core,
    aws_imagebuilder as imagebuilder,
    aws_iam as iam,
    aws_ec2 as ec2
)

class DevelopmentEnvironment(core.Stack):

    def __init__(self,
        scope: core.Construct,
        id: str,
        bucket_name: str,
        components_prefix: str,
        instance_type: str,
        personal_name: str,
        **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        bucket_uri = "s3://" + bucket_name + "/" + components_prefix

        name_prefix = f'Development-Environment-{personal_name}'

        # Create a VPC and security group
        name = f'{name_prefix}-VPC'
        vpc = ec2.CfnVPC(self,
            name,
            cidr_block = "10.0.0.0/16",
            enable_dns_hostnames = True,
            enable_dns_support = True,
            tags=[core.CfnTag(key="Name", value=name)])

        # Create routing table for public subnet
        route_table_public = ec2.CfnRouteTable(
            self,
            f'{name_prefix}-RouteTable',
            vpc_id=vpc.ref
        )

        # Create a subnet to each viable availability zone.
        # TODO: DRY
        public_subnet = ec2.CfnSubnet(
            self,
            f'{name_prefix}-Subnet-B',
            cidr_block="10.0.1.0/24",
            vpc_id=vpc.ref,
            availability_zone="us-east-1b",
            map_public_ip_on_launch=True
        )
        ec2.CfnSubnetRouteTableAssociation(
            self,
            f'{name_prefix}-Route-Table-Association-public-B',
            route_table_id=route_table_public.ref,
            subnet_id=public_subnet.ref
        )
        public_subnet = ec2.CfnSubnet(
            self,
            f'{name_prefix}-Subnet-C',
            cidr_block="10.0.2.0/24",
            vpc_id=vpc.ref,
            availability_zone="us-east-1c",
            map_public_ip_on_launch=True
        )
        ec2.CfnSubnetRouteTableAssociation(
            self,
            f'{name_prefix}-Route-Table-Association-public-C',
            route_table_id=route_table_public.ref,
            subnet_id=public_subnet.ref
        )
        public_subnet = ec2.CfnSubnet(
            self,
            f'{name_prefix}-Subnet-D',
            cidr_block="10.0.3.0/24",
            vpc_id=vpc.ref,
            availability_zone="us-east-1d",
            map_public_ip_on_launch=True
        )
        ec2.CfnSubnetRouteTableAssociation(
            self,
            f'{name_prefix}-Route-Table-Association-public-D',
            route_table_id=route_table_public.ref,
            subnet_id=public_subnet.ref
        )
        public_subnet = ec2.CfnSubnet(
            self,
            f'{name_prefix}-Subnet-E',
            cidr_block="10.0.4.0/24",
            vpc_id=vpc.ref,
            availability_zone="us-east-1e",
            map_public_ip_on_launch=True
        )
        ec2.CfnSubnetRouteTableAssociation(
            self,
            f'{name_prefix}-Route-Table-Association-public-E',
            route_table_id=route_table_public.ref,
            subnet_id=public_subnet.ref
        )
        public_subnet = ec2.CfnSubnet(
            self,
            f'{name_prefix}-Subnet-F',
            cidr_block="10.0.5.0/24",
            vpc_id=vpc.ref,
            availability_zone="us-east-1f",
            map_public_ip_on_launch=True
        )
        ec2.CfnSubnetRouteTableAssociation(
            self,
            "rtb-assoc-public-F",
            route_table_id=route_table_public.ref,
            subnet_id=public_subnet.ref
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

