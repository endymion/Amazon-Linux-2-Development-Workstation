#!/usr/bin/env python3
import configparser

from aws_cdk import core

from stacks.s3_ops import S3Ops
from stacks.imagebuilder_pipeline import ImageBuilderPipeline
from stacks.code_pipeline import CodePipeline
from stacks.development_environment import DevelopmentEnvironment
from stacks.development_workstation import DevelopmentWorkstation

config = configparser.ConfigParser()
config.read('parameters.properties')

app = core.App()

param_aws_account = config['DEFAULT']['awsAccount']

param_aws_region = config['DEFAULT']['awsRegion']

# AWS bucket where component configurations will be stored.
param_bucket_name = config['DEFAULT']['componentBucketName']

# Arn for base image that will be used to build developer workstation
# Example: "arn:aws:imagebuilder:us-west-2:aws:image/ubuntu-server-18-lts-x86/2020.8.10"
param_base_image_arn = config['DEFAULT']['baseImageArn']

# Code commit repo name on which CI pipeline need to be setup
param_code_commit_repo = config['DEFAULT']['codeCommitRepoName']

# imagebuilder pipeline will be built with this name
param_image_pipeline = config['DEFAULT']['imagePipelineName']

# A personal name that will be appended to resource names.
personal_name = config['DEFAULT']['personalName']

# s3 prefix/key for storing components
components_prefix = "components"

# Instance types/
build_instance_type = config['DEFAULT']['buildInstanceType']
development_instance_type = config['DEFAULT']['developmentInstanceType']

deploy_environment = core.Environment(region=param_aws_region, account=param_aws_account)

name_prefix = f'development-environment-{personal_name}'

# creates s3 bucket to store all components used in recipe
s3ops_stack = S3Ops(app,
    "s3ops",
    bucket_name=param_bucket_name,
    components_prefix=components_prefix,
    env=deploy_environment)

# builds the image builder pipeline
ImageBuilderPipeline(app,
    f'{name_prefix}-image-builder-pipeline',
    bucket_name=param_bucket_name,
    components_prefix=components_prefix,
    base_image_arn=param_base_image_arn,
    image_pipeline_name=param_image_pipeline,
    instance_type=build_instance_type,
    env=deploy_environment).add_dependency(s3ops_stack)

# a ci deployment pipeline is created only if source code is part of codecommit and repo details are supplied as
# parameters
param_branch_name = config['DEFAULT']['codeRepoBranchName']
CodePipeline(app,
    f'{name_prefix}-deployment-pipeline',
    code_commit_repo=param_code_commit_repo,
    env=deploy_environment,
    default_branch=param_branch_name)

DevelopmentEnvironment(app,
    f'{name_prefix}-VPC',
    bucket_name=param_bucket_name,
    components_prefix=components_prefix,
    instance_type=development_instance_type,
    personal_name=personal_name,
    env=deploy_environment
    )

DevelopmentWorkstation(app,
    f'{name_prefix}-workstation',
    bucket_name=param_bucket_name,
    components_prefix=components_prefix,
    instance_type=development_instance_type,
    env=deploy_environment)

app.synth()
