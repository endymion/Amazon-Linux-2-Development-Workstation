import os

from aws_cdk import (
    core,
    aws_imagebuilder as imagebuilder,
    aws_iam as iam,
    aws_ec2 as ec2
)

vpcID="vpc-0da4018aa2f868eff"
instanceName="ryan-dev-cdk-test"
instanceType="t2.micro" # t3.xlarge
amiName="AmazonLinux2-x86-Development-Workstation-Recipe*"

class DevelopmentWorkstation(core.Stack):

    def __init__(self,
        scope: core.Construct,
        id: str,
        bucket_name: str,
        components_prefix: str,
        instance_type: str,
        **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        bucket_uri = "s3://" + bucket_name + "/" + components_prefix

        # lookup existing VPC
        vpc = ec2.Vpc.from_lookup(
            self,
            "vpc",
            vpc_id=vpcID,
        )
        
        # create a new security group
        sec_group = ec2.SecurityGroup(
            self,
            "sec-group-allow-ssh",
            vpc=vpc,
            allow_all_outbound=True,
        )

        # add a new ingress rule to allow port 22 to internal hosts
        sec_group.add_ingress_rule(
            peer=ec2.Peer.ipv4('0.0.0.0/0'),
            description="Allow SSH connection", 
            connection=ec2.Port.tcp(22)
        )

        # define a new ec2 instance
        ec2_instance = ec2.Instance(
            self,
            "ec2-instance",
            instance_name=instanceName,
            instance_type=ec2.InstanceType(instanceType),
            machine_image=ec2.MachineImage().lookup(name=amiName),
            vpc=vpc,
            security_group=sec_group,
            availability_zone='us-east-1e'
        )

        # ec2.CfnVolumeAttachment(
        #     self,
        #     "projects-volume",
        #     instance_id=ec2_instance.instance_id,
        #     volume_id="vol-05fe4c91de077f230",
        #     device="/dev/sdh"
        # )