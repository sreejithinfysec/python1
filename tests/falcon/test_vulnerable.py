import mock
import pytest
import falcon
from six.moves.urllib_parse import quote

from falcon import testing

import vulnpy
import vulnpy.falcon

from vulnpy.trigger import DATA
from tests import parametrize_root, parametrize_triggers


@pytest.fixture(scope="module")
def client():
    app = falcon.API()
    vulnpy.falcon.add_vulnerable_routes(app)
    return testing.TestClient(app)


@parametrize_root
def test_root_views(client, view_name):
    if view_name == "home":
        response = client.simulate_get("/vulnpy")
    else:
        response = client.simulate_get("/vulnpy/{}".format(view_name))
    assert response.status_code == 200


@parametrize_triggers
@pytest.mark.parametrize("request_method", ["simulate_get"])
def test_trigger(client, request_method, view_name, trigger_name):
    get_or_post = getattr(client, request_method)

    data = DATA.get(view_name)

    if view_name == "unsafe_code_exec":
        data = quote(data)

    response = get_or_post(
        "/vulnpy/{}/{}".format(view_name, trigger_name),
        params={"user_input": data},
    )
    assert response.status_code == 200


@mock.patch(
    "vulnpy.trigger.cmdi.do_os_system", side_effect=Exception("something bad happened")
)
def test_handle_exception(mocked_trigger, client):
    response = client.simulate_get(
        "/vulnpy/cmdi/os-system",
        params={"user_input": "something", "catch_exception": True},
    )
    assert mocked_trigger.called
    assert response.status_code == 200
