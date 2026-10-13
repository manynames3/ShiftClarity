import os
import re
from pathlib import Path
import boto3

class PrivateStorage:
    def __init__(self, settings):
        self.settings = settings
        self.s3 = boto3.client("s3",region_name=settings.region) if settings.cloud else None
        if not self.s3:
            Path(settings.storage_dir).mkdir(parents=True,exist_ok=True,mode=0o700)

    def _key(self,key):
        if not re.fullmatch(r"[a-z0-9_-]+/(quarantine|accepted)/[a-f0-9]{32}",key):
            raise ValueError("Invalid private object reference")
        return key

    def put(self,key,data):
        key=self._key(key)
        if self.s3:
            self.s3.put_object(Bucket=self.settings.bucket,Key=key,Body=data,ContentType="application/json",ServerSideEncryption="AES256")
        else:
            target=Path(self.settings.storage_dir)/key
            target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            try:
                with target.open("xb") as file:
                    os.chmod(target,0o600)
                    file.write(data)
            except FileExistsError:
                if target.read_bytes()!=data:
                    raise ValueError("Private object content conflict") from None

    def get(self,key):
        key=self._key(key)
        if self.s3:
            return self.s3.get_object(Bucket=self.settings.bucket,Key=key)["Body"].read(1024*1024+1)
        return (Path(self.settings.storage_dir)/key).read_bytes()

    def delete(self,key):
        key=self._key(key)
        if self.s3:
            self.s3.delete_object(Bucket=self.settings.bucket,Key=key)
        else:
            (Path(self.settings.storage_dir)/key).unlink(missing_ok=True)
