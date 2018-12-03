# Serverless Janitor for Amazon Machine Images(AMI)
Automated AMI creation is essential for continuous delivery. If you are using my [Serverless AMI Baker](https://github.com/miztiik/Serverless-AMI-Baker/blob/master/README.MD) or any other automation, clean up of AMIs that are past the rentention date is important to keeps costs under control.

![Fig : Serverless-Janitor-for-AMI](https://raw.githubusercontent.com/miztiik/serverless-janitor-for-ami/master/images/serverless-janitor-for-ami.png)

This AWS Lambda function will help you to automatically de-register AMIs beyond retention date and remove the corresponding EBS Snapshots.

You can also follow this article in **[Youtube](https://www.youtube.com/watch?v=tCeK7sEgjvw&t=0s&list=PLxzKY3wu0_FKok5gI1v4g4S-g-PLaW9YD&index=24)**

## Pre-Requisities
We will need the following pre-requisites to successfully complete this activity,
- Few `AMIs` with a Tag Key:`DeleteOn` and Value as `Date` in this format `YYYY-MM-DD`
- IAM Role - _i.e_ `Lambda Service Role` - _with_ below mentioned policy

_The image above shows the execution order, that should not be confused with the numbering of steps given here_

## Step 0: IAM Policy
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:*"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": "ec2:Describe*",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:CreateImage",
        "ec2:DeregisterImage",
        "ec2:CreateSnapshot",
        "ec2:DeleteSnapshot",
        "ec2:CreateTags",
        "ec2:ModifySnapshotAttribute",
        "ec2:ResetSnapshotAttribute",
        "iam:Get*"
      ],
      "Resource": [
        "*"
      ]
    }
  ]
}
```

## Step 1 - Configure Lambda Function- `Serverless Janitor`
The python script is written(_and tested_) in `Python 3.6`. Remember to choose the same in AWS Lambda Functions.

### Customisations
- _Change the global variables at the top of the script to suit your needs._
  - `globalVars['findNeedle']` - My AMIs have tag `DeleteOn`, Set this to the value to suit your requirements
  - `globalVars['RetentionDays']` - Set the value you desire, by default it is set to 30 days

- `Copy` the code from `serverless-janitor-for-ami.py` in this repo to the lambda function
  - If you have a lot of AMIs, then consider increasing the lambda run time, the default is `3` seconds.
 - `Save` the lambda function


## Step 2 - Configure Lambda Triggers
We are going to use Cloudwatch Scheduled Events to take backup everyday.
```
rate(1 minute)
or
rate(5 minutes)
or
rate(1 day)
# The below example creates a rule that is triggered every day at 12:00pm UTC.
cron(0 12 * * ? *)
```
_If you want to learn more about the above Scheduled expressions,_ Ref: [CloudWatch - Schedule Expressions for Rules](http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html#RateExpressions)

## Step 3 - Testing the solution
Create few AMIs and add the Tag `DeleteOn` with Value as `<TODAYS-DATE-IN-YYYY-MM-DD-FORMAT>`.
If you dont have any, considering trying out my [Serverless AMI Baker](https://github.com/miztiik/Serverless-AMI-Baker/blob/master/README.MD).

### Summary
We have demonstrated how you can automatically identify and delete old and unused AMIs along with their Snapshots.
