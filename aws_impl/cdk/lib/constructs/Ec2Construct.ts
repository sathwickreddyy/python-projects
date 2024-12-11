import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as autoscaling from 'aws-cdk-lib/aws-autoscaling';
import * as elb from 'aws-cdk-lib/aws-elasticloadbalancingv2';

interface Ec2ConstructProps {
  vpc: ec2.Vpc;
}

export class Ec2Construct extends Construct {
  constructor(scope: Construct, id: string, props: Ec2ConstructProps) {
    super(scope, id);

    // Security Group for EC2 instances
    const securityGroup = new ec2.SecurityGroup(this, 'Ec2SecurityGroup', {
      securityGroupName: "leader-election-ec2-sg",
      vpc: props.vpc,
      allowAllOutbound: true,
    });

    // User Data to install dependencies on EC2 instances
    const userData = ec2.UserData.forLinux();
    userData.addCommands(
      `#!/bin/bash`,
      `yum update -y`,
      `yum install -y python3 pip`,
      `pip install boto3 redis`
    );

    // Auto Scaling Group
    const asg = new autoscaling.AutoScalingGroup(this, 'AutoScalingGroup', {
      autoScalingGroupName: "leader-election-asg",
      vpc: props.vpc,
      instanceType: new ec2.InstanceType('t3.micro'),
      machineImage: ec2.MachineImage.latestAmazonLinux2(),
      minCapacity: 1,
      maxCapacity: 3,
      securityGroup,
      userData,
    });

    // Application Load Balancer
    const alb = new elb.ApplicationLoadBalancer(this, 'ALB', {
      loadBalancerName: "leader-election-alb",
      vpc: props.vpc,
      internetFacing: true,
    });

    alb.addListener('Listener', {
      port: 80,
      defaultTargetGroups: [
        new elb.ApplicationTargetGroup(this, 'TargetGroup', {
          vpc: props.vpc,
          targets: [asg],
          port: 80,
        }),
      ],
    });
  }
}
