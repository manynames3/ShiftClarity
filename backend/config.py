import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent

@dataclass(frozen=True)
class Settings:
    database_url: str=field(repr=False)
    issuer: str
    client_id: str
    client_secret: str=field(repr=False)
    origin: str
    org_id: str
    storage_dir: str
    cloud: bool = False
    bucket: str = ""
    region: str = "us-east-1"
    cognito_pool: str = ""
    worker_enabled: bool = True
    job_queue_url: str = ""
    job_queue_arn: str = ""
    gateway_host: str = ""
    edge_proxy_secret: str = field(default="", repr=False)

    def validate(self):
        if bool(self.gateway_host) != bool(self.edge_proxy_secret):
            raise ValueError("Gateway host and edge credential must be configured together")
        if self.gateway_host and (not re.fullmatch(r"[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com",self.gateway_host) or len(self.edge_proxy_secret)<43):
            raise ValueError("Invalid edge gateway configuration")
        for value in (self.issuer, self.origin):
            parsed = urlparse(value)
            if parsed.scheme != "https" and (self.cloud or parsed.hostname not in ("127.0.0.1", "localhost")):
                raise ValueError("HTTPS required outside local development")
        if self.cloud and (not self.bucket or not self.cognito_pool or "sslmode=verify-full" not in self.database_url):
            raise ValueError("Cloud requires private S3, Cognito and verified database TLS")
        if self.cloud and self.issuer!="https://cognito-idp."+self.region+".amazonaws.com/"+self.cognito_pool:
            raise ValueError("Cognito issuer must match the configured pool")
        return self

def load_settings():
    path = os.environ.get("SHIFTCLARITY_CONFIG", str(ROOT / ".local/config.json"))
    if os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_SECRET_ARN"):
        import boto3
        database_url=os.environ.get("DATABASE_URL")
        if not database_url:
            database_url=boto3.client("secretsmanager",region_name=os.environ.get("AWS_REGION","us-east-1")).get_secret_value(
                SecretId=os.environ["DATABASE_SECRET_ARN"])["SecretString"]
        client_secret=os.environ.get("OIDC_CLIENT_SECRET")
        if not client_secret:
            provider=boto3.client("cognito-idp",region_name=os.environ.get("AWS_REGION","us-east-1"))
            client_secret=provider.describe_user_pool_client(UserPoolId=os.environ["COGNITO_POOL_ID"],ClientId=os.environ["OIDC_CLIENT_ID"])["UserPoolClient"]["ClientSecret"]
        return Settings(
            database_url=database_url, issuer=os.environ["OIDC_ISSUER"],
            client_id=os.environ["OIDC_CLIENT_ID"], client_secret=client_secret,
            origin=os.environ["APP_ORIGIN"], org_id=os.environ["ORG_ID"], storage_dir="/tmp/unused",
            cloud=True, bucket=os.environ["PRIVATE_BUCKET"], region=os.environ.get("AWS_REGION","us-east-1"),
            cognito_pool=os.environ["COGNITO_POOL_ID"],worker_enabled=not bool(os.environ.get("JOB_QUEUE_URL")),
            job_queue_url=os.environ.get("JOB_QUEUE_URL",""),job_queue_arn=os.environ.get("JOB_QUEUE_ARN",""),
            gateway_host=os.environ.get("GATEWAY_HOST",""),edge_proxy_secret=os.environ.get("EDGE_PROXY_SECRET","")
        ).validate()
    return Settings(**json.loads(Path(path).read_text())).validate()
