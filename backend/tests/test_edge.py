from dataclasses import replace
from fastapi.testclient import TestClient
import pytest
from backend.app import create_app
from backend.config import Settings

@pytest.fixture
def edge_settings(tmp_path):
    return Settings(database_url='postgresql://unused',issuer='https://identity.example.invalid',client_id='test',client_secret='test',origin='https://shiftclarity.pages.dev',org_id='synthetic-pilot',storage_dir=str(tmp_path),worker_enabled=False,gateway_host='4p30g92j37.execute-api.us-east-1.amazonaws.com',edge_proxy_secret='a'*64)

def test_edge_host_and_credential_do_not_replace_session_authorization(edge_settings):
    settings=edge_settings
    # These rejected/anonymous requests need no database or application startup.
    client=TestClient(create_app(settings))
    assert client.get('/api/v1/session').status_code==400
    headers={'host':settings.gateway_host}
    assert client.get('/api/v1/session',headers=headers).status_code==403
    assert client.get('/api/v1/session',headers={**headers,'x-shiftclarity-edge':'wrong'}).status_code==403
    assert client.get('/api/v1/session',headers=[(b'host',settings.gateway_host.encode()),(b'x-shiftclarity-edge',b'\xff')]).status_code==403
    response=client.get('/api/v1/session',headers={**headers,'x-shiftclarity-edge':settings.edge_proxy_secret})
    assert response.status_code==401
    assert response.headers['Cache-Control']=='no-store'
    assert client.get('/health').json()=={'status':'running','data_mode':'synthetic'}

def test_edge_configuration_fails_closed(edge_settings):
    for values in [{'gateway_host':'attacker.invalid','edge_proxy_secret':'a'*64},{'gateway_host':'4p30g92j37.execute-api.us-east-1.amazonaws.com'},{'edge_proxy_secret':'a'*64}]:
        with pytest.raises(ValueError):replace(edge_settings,**{'gateway_host':'','edge_proxy_secret':'',**values}).validate()
    assert 'a'*64 not in repr(edge_settings)
