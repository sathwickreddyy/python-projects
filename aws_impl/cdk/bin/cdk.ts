#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { CdkStack } from '../lib/cdk-stack';
import {Environment} from "aws-cdk-lib";
import {ACCOUNT, APP_NAME, AWS_REGION, REGION} from "../lib/constants/constants";

const app = new cdk.App();

const env: Environment = {
    account: ACCOUNT,
    region: AWS_REGION
}

const stackPrefix = `${APP_NAME}-${REGION}-`

new CdkStack(app, stackPrefix+'CdkStack', {
    env: env,
    stackName: stackPrefix+'CdkStack'
  /* If you don't specify 'env', this stack will be environment-agnostic.
   * Account/Region-dependent features and context lookups will not work,
   * but a single synthesized template can be deployed anywhere. */

  /* Uncomment the next line to specialize this stack for the AWS Account
   * and Region that are implied by the current CLI configuration. */
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },

  /* Uncomment the next line if you know exactly what Account and Region you
   * want to deploy the stack to. */
  // env: { account: '123456789012', region: 'us-east-1' },

  /* For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html */
});