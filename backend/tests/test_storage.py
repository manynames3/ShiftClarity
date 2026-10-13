import io
import os
from dataclasses import replace
from unittest.mock import patch
import boto3
import pytest
from botocore.stub import Stubber
from botocore.response import StreamingBody
from backend.storage import PrivateStorage

def test_local_opaque_objects_private_permissions_and_traversal(environment):
    storage=PrivateStorage(environment)
    key=environment.org_id+"/accepted/"+"a"*32
    storage.put(key,b'{"synthetic":true}')
    assert storage.get(key)==b'{"synthetic":true}'
    assert os.stat(environment.storage_dir+"/"+key).st_mode&0o777==0o600
    for malicious in ["../../secret","other/file.txt",environment.org_id+"/accepted/../secret"]:
        with pytest.raises(ValueError):storage.get(malicious)
    storage.delete(key)
    with pytest.raises(FileNotFoundError):storage.get(key)

def test_s3_adapter_encrypts_opaque_data_without_public_access(settings):
    client=boto3.client("s3",region_name="us-east-1",aws_access_key_id="synthetic-test",aws_secret_access_key="synthetic-test")
    cloud=replace(settings,cloud=True,bucket="private-synthetic-test")
    key=cloud.org_id+"/quarantine/"+"b"*32
    with patch("backend.storage.boto3.client",return_value=client),Stubber(client) as stub:
        stub.add_response("put_object",{},{"Bucket":cloud.bucket,"Key":key,"Body":b"{}","ContentType":"application/json","ServerSideEncryption":"AES256"})
        stub.add_response("get_object",{"Body":StreamingBody(io.BytesIO(b"{}"),2)},{"Bucket":cloud.bucket,"Key":key})
        stub.add_response("delete_object",{},{"Bucket":cloud.bucket,"Key":key})
        storage=PrivateStorage(cloud)
        storage.put(key,b"{}")
        assert storage.get(key)==b"{}"
        storage.delete(key)
        stub.assert_no_pending_responses()
