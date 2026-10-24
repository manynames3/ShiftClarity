"""Upload only an image whose ID matches the recorded Lambda container verification."""
import base64
import json
import subprocess
from pathlib import Path
import boto3
ROOT=Path(__file__).resolve().parent.parent
session=boto3.Session(region_name="us-east-1")
identity=session.client("sts").get_caller_identity()
assert identity["Account"]=="636305658578" and ":assumed-role/shiftclarity-deployer/" in identity["Arn"]
evidence=json.loads((ROOT/"artifacts/lambda-container-verification.json").read_text())
image=json.loads(subprocess.check_output(["docker","image","inspect","shiftclarity:lambda-verified"],text=True))[0]
assert evidence["image_id"]==image["Id"] and evidence["aws_lambda_runtime_emulator"] and image["Architecture"]=="amd64"
repository=json.loads((ROOT/".local/aws-bootstrap.json").read_text())["repository_uri"]
tag="synthetic-"+image["Id"].split(":")[1][:16]
target=repository+":"+tag
ecr=session.client("ecr")
authorization=ecr.get_authorization_token()["authorizationData"][0]
username,password=base64.b64decode(authorization["authorizationToken"]).decode().split(":",1)
subprocess.run(["docker","login","--username",username,"--password-stdin",authorization["proxyEndpoint"]],input=password,text=True,check=True,capture_output=True)
subprocess.run(["docker","tag","shiftclarity:lambda-verified",target],check=True)
subprocess.run(["docker","push",target],check=True,capture_output=True)
digest=ecr.describe_images(repositoryName="shiftclarity-synthetic",imageIds=[{"imageTag":tag}])["imageDetails"][0]["imageDigest"]
registry_image=ecr.batch_get_image(repositoryName="shiftclarity-synthetic",imageIds=[{"imageDigest":digest}])["images"][0]
manifest=json.loads(registry_image["imageManifest"])
assert manifest.get("mediaType") in ("application/vnd.docker.distribution.manifest.v2+json","application/vnd.oci.image.manifest.v1+json") and manifest.get("layers") and not manifest.get("manifests"),"Lambda requires one image manifest; rebuild with --provenance=false --sbom=false before verifying and pushing."
database=json.loads((ROOT/".local/neon-cloud-metadata.json").read_text())
path=ROOT/".local/aws.tfvars.json"
variables=json.loads(path.read_text()) if path.exists() else {}
variables.update(image_identifier=repository+"@"+digest,database_secret_arn=database["database_secret_arn"])
path.write_text(json.dumps(variables,indent=2))
path.chmod(0o600)
(ROOT/"artifacts/aws-image.json").write_text(json.dumps({"image_uri":variables["image_identifier"],"verified_image_id":image["Id"],"architecture":"amd64","manifest_media_type":manifest["mediaType"]},indent=2))
print(json.dumps({"image_uri":variables["image_identifier"],"verified_image_id":image["Id"]}))
