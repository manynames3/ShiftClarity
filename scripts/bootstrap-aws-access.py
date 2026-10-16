"""Establish only the authorized deployment role, then save temporary role credentials privately."""
import json
from pathlib import Path
import boto3

ROOT=Path(__file__).resolve().parent.parent
session=boto3.Session(profile_name="default",region_name="us-east-1")
sts=session.client("sts")
identity=sts.get_caller_identity()
account="636305658578"
assert identity["Account"]==account,"Unexpected AWS account"
name="shiftclarity-deployer"
iam=session.client("iam")
trust={"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":[identity["Arn"],f"arn:aws:iam::{account}:root"]},
       "Action":"sts:AssumeRole"}]}
def allow(actions,resources):
    return {"Effect":"Allow","Action":actions,"Resource":resources}
policy={"Version":"2012-10-17","Statement":[
    allow(["sts:GetCallerIdentity"],"*"),
    allow(["s3:CreateBucket","s3:DeleteBucket","s3:Get*","s3:List*","s3:Put*","s3:DeleteObject"],
          ["arn:aws:s3:::shiftclarity-*","arn:aws:s3:::shiftclarity-*/*"]),
    allow(["ecr:GetAuthorizationToken","ecr:DescribeRegistry"],"*"),
    allow(["ecr:CreateRepository","ecr:DescribeRepositories","ecr:TagResource","ecr:ListTagsForResource",
           "ecr:GetRepositoryPolicy","ecr:SetRepositoryPolicy","ecr:GetLifecyclePolicy","ecr:PutLifecyclePolicy",
           "ecr:BatchCheckLayerAvailability","ecr:InitiateLayerUpload","ecr:UploadLayerPart","ecr:CompleteLayerUpload",
           "ecr:PutImage","ecr:DescribeImages","ecr:DescribeImageScanFindings","ecr:BatchGetImage","ecr:GetDownloadUrlForLayer"],
          f"arn:aws:ecr:us-east-1:{account}:repository/shiftclarity-*"),
    allow(["secretsmanager:CreateSecret","secretsmanager:DescribeSecret","secretsmanager:GetSecretValue",
           "secretsmanager:PutSecretValue","secretsmanager:TagResource","secretsmanager:UpdateSecret",
           "secretsmanager:GetResourcePolicy","secretsmanager:DeleteSecret"],
          f"arn:aws:secretsmanager:us-east-1:{account}:secret:shiftclarity-*"),
    allow(["iam:CreateRole","iam:GetRole","iam:TagRole","iam:ListRolePolicies","iam:ListAttachedRolePolicies",
           "iam:PutRolePolicy","iam:GetRolePolicy","iam:DeleteRolePolicy","iam:DeleteRole","iam:PassRole"],
          f"arn:aws:iam::{account}:role/shiftclarity-synthetic-*"),
    allow(["cognito-idp:CreateUserPool","cognito-idp:DescribeUserPool","cognito-idp:UpdateUserPool","cognito-idp:DeleteUserPool",
           "cognito-idp:TagResource","cognito-idp:UntagResource","cognito-idp:ListTagsForResource",
           "cognito-idp:GetUserPoolMfaConfig","cognito-idp:SetUserPoolMfaConfig",
           "cognito-idp:CreateUserPoolClient","cognito-idp:DescribeUserPoolClient","cognito-idp:UpdateUserPoolClient",
           "cognito-idp:DeleteUserPoolClient","cognito-idp:CreateUserPoolDomain","cognito-idp:DescribeUserPoolDomain",
           "cognito-idp:DeleteUserPoolDomain","cognito-idp:AdminCreateUser","cognito-idp:AdminSetUserPassword","cognito-idp:AdminGetUser","cognito-idp:AdminSetUserMFAPreference","cognito-idp:GetUICustomization","cognito-idp:SetUICustomization"],
          ["*"]),
    allow(["lambda:CreateFunction","lambda:GetFunction","lambda:GetFunctionConfiguration","lambda:UpdateFunctionCode",
           "lambda:UpdateFunctionConfiguration","lambda:DeleteFunction","lambda:ListVersionsByFunction",
           "lambda:GetPolicy","lambda:AddPermission","lambda:RemovePermission","lambda:TagResource",
           "lambda:UntagResource","lambda:ListTags","lambda:GetFunctionConcurrency","lambda:InvokeFunction"],
          f"arn:aws:lambda:us-east-1:{account}:function:shiftclarity-*"),
    allow(["lambda:CreateEventSourceMapping","lambda:GetEventSourceMapping","lambda:UpdateEventSourceMapping",
           "lambda:DeleteEventSourceMapping","lambda:ListEventSourceMappings","lambda:TagResource","lambda:ListTags"],"*"),
    allow(["sqs:CreateQueue","sqs:GetQueueAttributes","sqs:GetQueueUrl","sqs:SetQueueAttributes",
           "sqs:TagQueue","sqs:ListQueueTags","sqs:DeleteQueue","sqs:SendMessage","sqs:ReceiveMessage","sqs:DeleteMessage"],
          f"arn:aws:sqs:us-east-1:{account}:shiftclarity-*"),
    allow(["apigateway:GET","apigateway:POST","apigateway:PUT","apigateway:PATCH","apigateway:DELETE","apigateway:TagResource","apigateway:UntagResource"],
          ["arn:aws:apigateway:us-east-1::/apis","arn:aws:apigateway:us-east-1::/apis/*","arn:aws:apigateway:us-east-1::/tags/*"]),
    allow(["logs:CreateLogGroup","logs:DescribeLogGroups","logs:ListTagsLogGroup","logs:ListTagsForResource",
           "logs:TagResource","logs:TagLogGroup","logs:PutRetentionPolicy","logs:DeleteLogGroup",
           "logs:FilterLogEvents","logs:DescribeLogStreams","logs:GetLogEvents"],
          [f"arn:aws:logs:us-east-1:{account}:log-group:/aws/lambda/shiftclarity-*",f"arn:aws:logs:us-east-1:{account}:log-group:/aws/lambda/shiftclarity-*:*"]),
    allow(["logs:DescribeLogGroups"],"*"),
    allow(["cognito-idp:DescribeUserPoolDomain"],"*"),
    allow(["budgets:ViewBudget","budgets:ModifyBudget","budgets:TagResource","budgets:ListTagsForResource"],f"arn:aws:budgets::{account}:budget/shiftclarity-*"),
    allow(["sns:CreateTopic","sns:DeleteTopic","sns:GetTopicAttributes","sns:SetTopicAttributes","sns:Subscribe","sns:Unsubscribe","sns:ListSubscriptionsByTopic","sns:GetSubscriptionAttributes","sns:TagResource","sns:UntagResource","sns:ListTagsForResource"],
          f"arn:aws:sns:us-east-1:{account}:shiftclarity-synthetic-alerts"),
    allow(["cloudwatch:PutMetricAlarm","cloudwatch:DescribeAlarms","cloudwatch:DeleteAlarms","cloudwatch:ListTagsForResource","cloudwatch:TagResource"],
          f"arn:aws:cloudwatch:us-east-1:{account}:alarm:shiftclarity-*")
]}
outputs_file=ROOT/".local/aws-outputs.json"
if outputs_file.exists():
    values=json.loads(outputs_file.read_text())
    for statement in policy["Statement"]:
        if "cognito-idp:CreateUserPool" in statement["Action"]:
            statement["Action"].remove("cognito-idp:CreateUserPool")
            statement["Resource"]=[f"arn:aws:cognito-idp:us-east-1:{account}:userpool/"+values["cognito_pool"]["value"]]
        if "apigateway:POST" in statement["Action"]:
            api_id=values.get("gateway_origin",values["app_origin"])["value"].split("://",1)[1].split(".",1)[0]
            statement["Resource"]=[f"arn:aws:apigateway:us-east-1::/apis/{api_id}",f"arn:aws:apigateway:us-east-1::/apis/{api_id}/*",f"arn:aws:apigateway:us-east-1::/tags/arn:aws:apigateway:us-east-1::/apis/{api_id}*"]
try:
    role=iam.get_role(RoleName=name)["Role"]
    assert {tag["Key"]:tag["Value"] for tag in role.get("Tags",[])}.get("Product")=="ShiftClarity","Unrelated existing role"
    iam.update_assume_role_policy(RoleName=name,PolicyDocument=json.dumps(trust))
except iam.exceptions.NoSuchEntityException:
    role=iam.create_role(RoleName=name,AssumeRolePolicyDocument=json.dumps(trust),MaxSessionDuration=3600,
                         Tags=[{"Key":"Product","Value":"ShiftClarity"},{"Key":"Environment","Value":"synthetic-pilot"}])["Role"]
    iam.get_waiter("role_exists").wait(RoleName=name)
iam.put_role_policy(RoleName=name,PolicyName="shiftclarity-synthetic-deployment",PolicyDocument=json.dumps(policy))
credentials=sts.assume_role(RoleArn=role["Arn"],RoleSessionName="shiftclarity-deployment",DurationSeconds=3600)["Credentials"]
path=ROOT/".local/aws-deploy-credentials"
path.write_text("[shiftclarity-deploy]\naws_access_key_id="+credentials["AccessKeyId"]+"\naws_secret_access_key="+credentials["SecretAccessKey"]+"\naws_session_token="+credentials["SessionToken"]+"\n")
path.chmod(0o600)
metadata={"account":account,"role_arn":role["Arn"],"expires":credentials["Expiration"].isoformat(),
          "bootstrap_identity":identity["Arn"],"no_long_lived_keys_created":True}
(ROOT/"artifacts/aws-deployment-role.json").write_text(json.dumps(metadata,indent=2))
print(json.dumps(metadata))
