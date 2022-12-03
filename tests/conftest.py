"""Common helper functions to test subarulink."""
import asyncio
import json
import time
from unittest.mock import patch

from asynctest import CoroutineMock
import pytest

import subarulink
import subarulink.const as sc

# https://solidabstractions.com/2018/testing-aiohttp-client
from tests.aiohttp import CaseControlledTestServer, http_redirect as redirect
from tests.api_responses import (
    CONDITION_EV,
    FETCH_SUBARU_CLIMATE_PRESETS,
    FETCH_USER_CLIMATE_PRESETS_EV,
    LOCATE_G2,
    LOGIN_MULTI_REGISTERED,
    LOGIN_SINGLE_REGISTERED,
    SELECT_VEHICLE_1,
    SELECT_VEHICLE_2,
    SELECT_VEHICLE_3,
    SELECT_VEHICLE_4,
    SELECT_VEHICLE_5,
    VALIDATE_SESSION_SUCCESS,
    VEHICLE_STATUS_EV,
)
from tests.certificate import ssl_certificate

TEST_COUNTRY = "USA"
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password"
TEST_DEVICE_ID = "9999999999"
TEST_PIN = "1234"
TEST_DEVICE_NAME = "subarulink test device"

TEST_VIN_1_G1 = "JF2ABCDE6L0000001"
TEST_VIN_2_EV = "JF2ABCDE6L0000002"
TEST_VIN_3_G2 = "JF2ABCDE6L0000003"
TEST_VIN_4_SAFETY_PLUS = "JF2ABCDE6L0000004"
TEST_VIN_5_G1_SECURITY = "JF2ABCDE6L0000005"


async def server_js_response(server, response, path=None, query=None, status=200):
    request = await server.receive_request()
    if path and sc.MOBILE_API_VERSION in request.path:
        if sc.FEATURE_G1_TELEMATICS in request.path:
            assert request.path == f"{sc.MOBILE_API_VERSION}{path}".replace("api_gen", sc.FEATURE_G1_TELEMATICS)
        else:
            assert request.path == f"{sc.MOBILE_API_VERSION}{path}".replace("api_gen", sc.FEATURE_G2_TELEMATICS)
    else:
        assert request.path == path
    if query:
        assert query.get("vin") == request.query.get("vin")
    js_resp = json.dumps(response)
    server.send_response(request, text=js_resp, content_type="application/json", status=status)


@pytest.fixture(name="http_redirect")
def http_redirect_fixture(redirect):
    return redirect


@pytest.fixture(name="test_server")
async def test_server_fixture(ssl_certificate):
    """Yield a local test server to use with server_js_response()."""
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            yield server


@pytest.fixture(name="controller")
async def controller_fixture(test_server, http_redirect):
    """Return a test controller that talks to a local test server."""
    http_redirect.add_server(sc.MOBILE_API_SERVER[sc.COUNTRY_USA], 443, test_server.port)
    controller = subarulink.Controller(
        http_redirect.session,
        TEST_USERNAME,
        TEST_PASSWORD,
        TEST_DEVICE_ID,
        TEST_PIN,
        TEST_DEVICE_NAME,
    )
    return controller


@pytest.fixture
async def multi_vehicle_controller(test_server, controller):
    """

    Return a multi-car authenticated session for testing.

    Use in a test case to obtain a controller object that is logged into a multi-vehicle account.

    """
    task = asyncio.create_task(controller.connect())
    await add_multi_vehicle_login_sequence(test_server)
    assert await task
    return controller


async def add_multi_vehicle_login_sequence(test_server):
    await server_js_response(test_server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)

    await server_js_response(
        test_server,
        SELECT_VEHICLE_1,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_1_G1, "_": str(int(time.time()))},
    )

    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )

    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )

    await server_js_response(
        test_server,
        SELECT_VEHICLE_4,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_4_SAFETY_PLUS, "_": str(int(time.time()))},
    )

    await server_js_response(
        test_server,
        SELECT_VEHICLE_5,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_5_G1_SECURITY, "_": str(int(time.time()))},
    )


@pytest.fixture
async def single_vehicle_controller(test_server, controller):
    """

    Return a single-car authenticated session for testing.

    Use in a test case to obtain a controller object that is logged into a single-vehicle account.

    """
    task = asyncio.create_task(controller.connect())

    await server_js_response(test_server, LOGIN_SINGLE_REGISTERED, path=sc.API_LOGIN)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_1,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_1_G1, "_": str(int(time.time()))},
    )
    assert await task
    return controller


def assert_vehicle_status(result, expected):
    assert result[sc.API_ODOMETER] == expected["data"][sc.API_ODOMETER]
    assert result[sc.API_LONGITUDE] == expected["data"][sc.API_LONGITUDE]
    assert result[sc.API_LATITUDE] == expected["data"][sc.API_LATITUDE]
    assert result[sc.API_AVG_FUEL_CONSUMPTION] == expected["data"][sc.API_AVG_FUEL_CONSUMPTION]
    assert result[sc.API_DIST_TO_EMPTY] == expected["data"][sc.API_DIST_TO_EMPTY]
    assert result[sc.API_VEHICLE_STATE] == expected["data"][sc.API_VEHICLE_STATE]
    assert result[sc.API_TIRE_PRESSURE_FL] == int(expected["data"][sc.API_TIRE_PRESSURE_FL])
    assert result[sc.API_TIRE_PRESSURE_FR] == int(expected["data"][sc.API_TIRE_PRESSURE_FR])
    assert result[sc.API_TIRE_PRESSURE_RL] == int(expected["data"][sc.API_TIRE_PRESSURE_RL])
    assert result[sc.API_TIRE_PRESSURE_RR] == int(expected["data"][sc.API_TIRE_PRESSURE_RR])


async def add_validate_session(test_server):
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)


async def add_select_vehicle_sequence(test_server, test_vehicle_id):
    test_vehicles = [
        {"vin": TEST_VIN_1_G1, "data": SELECT_VEHICLE_1},
        {"vin": TEST_VIN_2_EV, "data": SELECT_VEHICLE_2},
        {"vin": TEST_VIN_3_G2, "data": SELECT_VEHICLE_3},
        {"vin": TEST_VIN_4_SAFETY_PLUS, "data": SELECT_VEHICLE_4},
        {"vin": TEST_VIN_5_G1_SECURITY, "data": SELECT_VEHICLE_5},
    ]
    await server_js_response(
        test_server,
        test_vehicles[test_vehicle_id - 1]["data"],
        path=sc.API_SELECT_VEHICLE,
        query={"vin": test_vehicles[test_vehicle_id - 1]["vin"], "_": str(int(time.time()))},
    )


async def add_ev_vehicle_status(test_server):
    await server_js_response(test_server, VEHICLE_STATUS_EV, path=sc.API_VEHICLE_STATUS)


async def add_ev_vehicle_condition(test_server):
    await server_js_response(test_server, CONDITION_EV, path=sc.API_CONDITION)


async def add_g2_vehicle_locate(test_server):
    await server_js_response(test_server, LOCATE_G2, path=sc.API_LOCATE)


async def add_fetch_climate_presets(test_server):
    await server_js_response(test_server, FETCH_SUBARU_CLIMATE_PRESETS, path=sc.API_G2_FETCH_RES_SUBARU_PRESETS)
    await server_js_response(test_server, FETCH_USER_CLIMATE_PRESETS_EV, path=sc.API_G2_FETCH_RES_USER_PRESETS)
