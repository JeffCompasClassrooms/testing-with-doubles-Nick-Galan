import io
import json
import pytest
from squirrel_server import SquirrelServerHandler
from squirrel_db import SquirrelDB

todo = pytest.mark.skip(reason='TODO: pending spec')

class FakeRequest():
    def __init__(self, mock_wfile, method, path, body=None):
        self._mock_wfile = mock_wfile
        self._method = method
        self._path = path
        self._body = body

    def sendall(self, x):
        return

    def makefile(self, *args, **kwargs):
        if args[0] == 'rb':
            if self._body:
                headers = 'Content-Length: {}\r\n'.format(len(self._body))
                body = self._body
            else:
                headers = ''
                body = ''
            request = bytes('{} {} HTTP/1.0\r\n{}\r\n{}'.format(self._method, self._path, headers, body), 'utf-8')
            return io.BytesIO(request)
        elif args[0] == 'wb':
            return self._mock_wfile

@pytest.fixture
def dummy_client():
    return ('127.0.0.1', 80)

@pytest.fixture
def dummy_server():
    return None

@pytest.fixture
def mock_db_init(mocker):
    return mocker.patch.object(SquirrelDB, '__init__', return_value=None)

@pytest.fixture
def mock_db_get_squirrels(mocker, mock_db_init):
    return mocker.patch.object(SquirrelDB, 'getSquirrels', return_value=['squirrel'])

@pytest.fixture
def mock_db_get_squirrel(mocker, mock_db_init):
    return mocker.patch.object(SquirrelDB, 'getSquirrel', return_value={'id': 1, 'name': 'Sandy'})

@pytest.fixture
def mock_db_update_squirrel(mocker, mock_db_init):
    return mocker.patch.object(SquirrelDB, 'updateSquirrel')

@pytest.fixture
def mock_db_delete_squirrel(mocker, mock_db_init):
    return mocker.patch.object(SquirrelDB, 'deleteSquirrel')

@pytest.fixture(autouse=True)
def patch_wbufsize(mocker):
    mocker.patch.object(SquirrelServerHandler, 'wbufsize', 1)

@pytest.fixture
def fake_get_squirrels_request(mocker):
    return FakeRequest(mocker.Mock(), 'GET', '/squirrels')

@pytest.fixture
def fake_create_squirrel_request(mocker):
    return FakeRequest(mocker.Mock(), 'POST', '/squirrels', body='name=Chippy&size=small')

@pytest.fixture
def fake_get_squirrel_by_id_request(mocker):
    return FakeRequest(mocker.Mock(), 'GET', '/squirrels/1')

@pytest.fixture
def fake_get_nonexistent_squirrel_request(mocker):
    return FakeRequest(mocker.Mock(), 'GET', '/squirrels/999')

@pytest.fixture
def fake_update_squirrel_request(mocker):
    return FakeRequest(mocker.Mock(), 'PUT', '/squirrels/1', body='name=Updated&size=medium')

@pytest.fixture
def fake_delete_squirrel_request(mocker):
    return FakeRequest(mocker.Mock(), 'DELETE', '/squirrels/1')

@pytest.fixture
def mock_response_methods(mocker):
    mock_send_response = mocker.patch.object(SquirrelServerHandler, 'send_response')
    mock_send_header = mocker.patch.object(SquirrelServerHandler, 'send_header')
    mock_end_headers = mocker.patch.object(SquirrelServerHandler, 'end_headers')
    return mock_send_response, mock_send_header, mock_end_headers

def describe_SquirrelServerHandler():

    def describe_GET_requests():
        def describe_all_squirrels():
            def it_queries_db_for_squirrels(dummy_client, dummy_server, fake_get_squirrels_request, mock_db_get_squirrels):
                SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)
                mock_db_get_squirrels.assert_called_once()

            def it_returns_200_status_code(fake_get_squirrels_request, dummy_client, dummy_server, mock_response_methods):
                mock_send_response, mock_send_header, mock_end_headers = mock_response_methods
                SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)
                mock_send_response.assert_called_once_with(200)

            def it_sends_json_content_type_header(fake_get_squirrels_request, dummy_client, dummy_server, mock_db_get_squirrels, mock_response_methods):
                mock_send_response, mock_send_header, mock_end_headers = mock_response_methods
                SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)
                mock_send_header.assert_called_once_with("Content-Type", "application/json")

            def it_calls_end_headers(fake_get_squirrels_request, dummy_client, dummy_server, mock_db_get_squirrels, mock_response_methods):
                mock_send_response, mock_send_header, mock_end_headers = mock_response_methods
                SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)
                mock_end_headers.assert_called_once()
                
            def it_returns_response_body_with_squirrels_json_data(fake_get_squirrels_request, dummy_client, dummy_server, mock_db_get_squirrels):
                response = SquirrelServerHandler(fake_get_squirrels_request, dummy_client, dummy_server)
                response.wfile.write.assert_any_call(bytes(json.dumps(['squirrel']), "utf-8"))
        
        def describe_single_squirrel():
            def it_queries_db_for_one_squirrel(fake_get_squirrel_by_id_request, dummy_client, dummy_server, mock_db_get_squirrel):
                SquirrelServerHandler(fake_get_squirrel_by_id_request, dummy_client, dummy_server)
                mock_db_get_squirrel.assert_called_once_with('1')

            def it_returns_200_if_squirrel_found(fake_get_squirrel_by_id_request, dummy_client, dummy_server, mock_db_get_squirrel, mock_response_methods):
                mock_send_response, _, _ = mock_response_methods
                SquirrelServerHandler(fake_get_squirrel_by_id_request, dummy_client, dummy_server)
                mock_send_response.assert_called_once_with(200)
            
            def it_returns_404_if_squirrel_not_found(mocker, fake_get_nonexistent_squirrel_request, dummy_client, dummy_server, mock_response_methods):
                mocker.patch.object(SquirrelDB, 'getSquirrel', return_value=None)
                mock_send_response, _, _ = mock_response_methods
                SquirrelServerHandler(fake_get_nonexistent_squirrel_request, dummy_client, dummy_server)
                mock_send_response.assert_called_once_with(404)

    def describe_POST_requests():
        def it_queries_db_to_create_squirrel_with_given_data(mocker, fake_create_squirrel_request, dummy_client, dummy_server):
            mock_db_create_squirrel = mocker.patch.object(SquirrelDB,'createSquirrel',return_value=None)
            SquirrelServerHandler(fake_create_squirrel_request,dummy_client,dummy_server)
            mock_db_create_squirrel.assert_called_once_with('Chippy','small')

        def it_returns_201_on_creation(mocker, fake_create_squirrel_request, dummy_client, dummy_server, mock_response_methods):
            mocker.patch.object(SquirrelDB,'createSquirrel',return_value=None)
            mock_send_response, _, _ = mock_response_methods
            SquirrelServerHandler(fake_create_squirrel_request,dummy_client,dummy_server)
            mock_send_response.assert_called_once_with(201)

    def describe_PUT_requests():
        def it_updates_a_squirrel_if_it_exists(fake_update_squirrel_request, dummy_client, dummy_server, mock_db_get_squirrel, mock_db_update_squirrel):
            SquirrelServerHandler(fake_update_squirrel_request, dummy_client, dummy_server)
            mock_db_get_squirrel.assert_called_once_with('1')
            mock_db_update_squirrel.assert_called_once_with('1', 'Updated', 'medium')

        def it_returns_204_on_successful_update(fake_update_squirrel_request, dummy_client, dummy_server, mock_db_get_squirrel, mock_db_update_squirrel, mock_response_methods):
            mock_send_response, _, _ = mock_response_methods
            SquirrelServerHandler(fake_update_squirrel_request, dummy_client, dummy_server)
            mock_send_response.assert_called_once_with(204)
        
        def it_returns_404_if_squirrel_to_update_is_not_found(mocker, fake_update_squirrel_request, dummy_client, dummy_server, mock_response_methods, mock_db_update_squirrel):
            mocker.patch.object(SquirrelDB, 'getSquirrel', return_value=None)
            mock_send_response, _, _ = mock_response_methods
            SquirrelServerHandler(fake_update_squirrel_request, dummy_client, dummy_server)
            mock_send_response.assert_called_once_with(404)
            mock_db_update_squirrel.assert_not_called()

    def describe_DELETE_requests():
        def it_deletes_a_squirrel_if_it_exists(fake_delete_squirrel_request, dummy_client, dummy_server, mock_db_get_squirrel, mock_db_delete_squirrel):
            SquirrelServerHandler(fake_delete_squirrel_request, dummy_client, dummy_server)
            mock_db_get_squirrel.assert_called_once_with('1')
            mock_db_delete_squirrel.assert_called_once_with('1')

        def it_returns_204_on_successful_delete(fake_delete_squirrel_request, dummy_client, dummy_server, mock_db_get_squirrel, mock_db_delete_squirrel, mock_response_methods):
            mock_send_response, _, _ = mock_response_methods
            SquirrelServerHandler(fake_delete_squirrel_request, dummy_client, dummy_server)
            mock_send_response.assert_called_once_with(204)
        
        def it_returns_404_if_squirrel_to_delete_is_not_found(mocker, fake_delete_squirrel_request, dummy_client, dummy_server, mock_response_methods, mock_db_delete_squirrel):
            mocker.patch.object(SquirrelDB, 'getSquirrel', return_value=None)
            mock_send_response, _, _ = mock_response_methods
            SquirrelServerHandler(fake_delete_squirrel_request, dummy_client, dummy_server)
            mock_send_response.assert_called_once_with(404)
            mock_db_delete_squirrel.assert_not_called()

    def describe_bad_paths():
        def it_returns_404_for_post_to_an_id(mocker, dummy_client, dummy_server, mock_response_methods):
            bad_request = FakeRequest(mocker.Mock(), 'POST', '/squirrels/1')
            mock_send_response, _, _ = mock_response_methods
            SquirrelServerHandler(bad_request, dummy_client, dummy_server)
            mock_send_response.assert_called_once_with(404)

        def it_returns_404_for_put_without_an_id(mocker, dummy_client, dummy_server, mock_response_methods):
            bad_request = FakeRequest(mocker.Mock(), 'PUT', '/squirrels')
            mock_send_response, _, _ = mock_response_methods
            SquirrelServerHandler(bad_request, dummy_client, dummy_server)
            mock_send_response.assert_called_once_with(404)