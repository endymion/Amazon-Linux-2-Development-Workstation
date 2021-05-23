## Amazon Linux 2 Development Workstation

This project contains code that can create a development environment in an AWS data center and that can manage Amazon Linux 2 workstations that include the things that you need for development, like Git, Python3, Ruby, the CDK, SAM.  Or whatever you need.  Use with VNC is recommended, but you might have better ideas, and you have control.

Your workstations that you create with this code will be based on a custom development image built by a Code Pipeline project watching this project.  The code in this project will set up that pipeline.  

That pipeline will trigger an EC2 Image Builder pipeline that will also be generated from ths project, whichwill use an Image Recipe for setting up your custom development AMI.  It will use a series of Components for installing the packages that you need.  Code Pipeline will build a new custom AMI for your development workstation any time you push changes to your fork of this project to Code Commit.

The development environment that this project will create will include a VPC, so that your development workstations have their own private network.  You can mhave multiple development workstations that can easily reach one another and their shared code folders.

The VPC creates a single shared EFS (NFS) drive that your instances can reach.  And when you run the code in this project to create a new development workstation, it automatically connects the new instance to your shared code drive.  All of your workstations in your VPC will be able to connect to that shared volume.  Even if they're in different availability zones.

This setup keeps your entire development environment predictable and based on versioned code.  Better living through DevOps!

### Background

My motivation for doing development from a cloud VM instance was that I needed more RAM than I could get in a MacBook Pro.  For years, I have tried using things like remove VNC connections and AWS Cloud9 for development.  VS Code plus the AWS CDK is what finally made it workable.

Now I use my Mac for my human interface and it's awesome and reasponsive, and VS Code is well-integrated with my OS.  And I use powerful, well-connected development machines for my code builds.  My entire environment is consistent and predictable and I never install anything manually, where I might forget how I did it months or years later.  And it all seamlessly integrates through the VS Code remote SSH plugin, so that I feel like I'm using VS Code to do local development on my own Mac.  It's faster than doing development on my own Mac through Docker containers.  A lot faster.  And it doesn't consume gigabytes of RAM on my Mac for the Docker VM.

### Tips

#### Burstable instances

The `t3`, and `t3a` instance types are a great value for development.

The Gravitron2 instance types are the best value, and the `t4g` instances would be the ultimate cloud development workstations -- except that it's not always easy to get the toolchains that you need working on those ARM instances.  AWS SAM, for example, just won't work as of this writing.  I'm still using x86 instances that are more expensive until the tools catch up.

Leave a `command` workstation instance running on a `t3a.nano` instance full-time, and use that to run CDK code from this project to spin up other workstations in the same VPC.

### Getting Started

- For setting up CDK follow instructions under "CDK Instructions".
- Create a CodeCommit repository and push the code repo to the newly created repository.
    - By default CodeCommit will create a branch named mainline, by default CI will be triggered on this branch.
    - If you choose to use a different branch (ex. dev), follow instructions below to pass it as a parameter for CI setup
        - Add a property in parameters.properties file
        ```
            codeRepoBranchName=dev
        ```
        - Pass the value as parameter to deployment stack in app.py
        ```
            param_branch_name = config['DEFAULT']['codeRepoBranchName']
            DeploymentPipeline(app,
                   "deploymentPipeline",
                   code_commit_repo=param_code_commit_repo,
                   default_branch=param_branch_name
                   env=deploy_environment)
        ```
- Update parameters.properties with appropriate values
    - componentBucketName - Bucket name where all components will be stored, this bucket will be created.
    - imagePipelineName - Name for image pipeline
    - awsRegion - AWS region in which this deployment will be done
    - baseImageArn - Ubuntu base image ARN to use ex. arn:aws:imagebuilder:us-west-2:aws:image/ubuntu-server-18-lts-x86/2020.8.10
    - codeCommitRepoName - Name of the newly created imagebuilder repo ex. mycdkubuntuimagebuilderrepo
    - Ensure parameter store values are set (refer buildspec for more details).
- Deploy deploymentpipeline stack once above step is complete to setup CI
    ```
    $ make cdk-deploy
    ```
- Once deployment of 'deploymentPipeline' stack is complete CI will deploy imagebuilder pipeline.
- Deploy imagebuilder stack from your developer workstation (use this if you skipped above steps or want to do local deployment)
    ```
    $ make build-deploy
    ```
- Imagebuilder stack can be triggered through cli using:
    ```
    $ aws imagebuilder start-image-pipeline-execution \
            --image-pipeline-arn arn:aws:imagebuilder:<<aws_region>>:<<account_number>>:image-pipeline/<<name_of_pipeline>>
    ```

### CDK Instructions

The `cdk.json` file tells the CDK Toolkit how to execute this app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the .env
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .env/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth (stackname - refer stack documentation to understand which one to use)
```

If you are using MAKEFILE you can synthesize the CloudFormation template for this code.

```
$ make cdk-synth
```

If you are using MAKEFILE you can initiate an imagebuilder pipeline deployment ***with auto approval*** 

```
$ make build-deploy
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

### Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

