"""Create isolated encrypted state/image containers through the deployment role."""
import json
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
ROOT=Path(__file__).resolve().parent.parent
session=boto3.Session(region_name="us-east-1")
identity=session.client("sts").get_caller_identity()
assert identity["Account"]=="636305658578" and ":assumed-role/shiftclarity-deployer/" in identity["Arn"]
tags=[{"Key":"Product","Value":"ShiftClarity"},{"Key":"Environment","Value":"synthetic-pilot"}]
bucket="shiftclarity-tfstate-636305658578"
s3=session.client("s3")
try:
    s3.head_bucket(Bucket=bucket)
    assert {tag["Key"]:tag["Value"] for tag in s3.get_bucket_tagging(Bucket=bucket)["TagSet"]}.get("Product")=="ShiftClarity"
except ClientError as error:
    if error.response["Error"]["Code"] not in ("404","NoSuchBucket"):
        raise
    s3.create_bucket(Bucket=bucket)
    s3.put_bucket_tagging(Bucket=bucket,Tagging={"TagSet":tags})
s3.put_public_access_block(Bucket=bucket,PublicAccessBlockConfiguration={key:True for key in ("BlockPublicAcls","IgnorePublicAcls","BlockPublicPolicy","RestrictPublicBuckets")})
s3.put_bucket_encryption(Bucket=bucket,ServerSideEncryptionConfiguration={"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]})
s3.put_bucket_versioning(Bucket=bucket,VersioningConfiguration={"Status":"Enabled"})
s3.put_bucket_policy(Bucket=bucket,Policy=json.dumps({"Version":"2012-10-17","Statement":[{"Effect":"Deny","Principal":"*","Action":"s3:*","Resource":[f"arn:aws:s3:::{bucket}",f"arn:aws:s3:::{bucket}/*"],"Condition":{"Bool":{"aws:SecureTransport":"false"}}}]}))
ecr=session.client("ecr")
repository="shiftclarity-synthetic"
try:
    metadata=ecr.describe_repositories(repositoryNames=[repository])["repositories"][0]
except ecr.exceptions.RepositoryNotFoundException:
    metadata=ecr.create_repository(repositoryName=repository,imageTagMutability="IMMUTABLE",imageScanningConfiguration={"scanOnPush":True},encryptionConfiguration={"encryptionType":"AES256"},tags=tags)["repository"]
ecr.put_lifecycle_policy(repositoryName=repository,lifecyclePolicyText=json.dumps({"rules":[{"rulePriority":1,"description":"Keep three untagged build layers","selection":{"tagStatus":"untagged","countType":"imageCountMoreThan","countNumber":3},"action":{"type":"expire"}}]}))
result={"account":identity["Account"],"role":identity["Arn"],"state_bucket":bucket,"repository_uri":metadata["repositoryUri"]}
(ROOT/".local/aws-bootstrap.json").write_text(json.dumps(result,indent=2))
(ROOT/".local/aws-bootstrap.json").chmod(0o600)
(ROOT/".local/aws-backend.hcl").write_text(f'bucket = "{bucket}"\nkey = "synthetic-pilot/terraform.tfstate"\nregion = "us-east-1"\nencrypt = true\nuse_lockfile = true\n')
(ROOT/".local/aws-backend.hcl").chmod(0o600)
print(json.dumps(result))
