"""Common helper functions to test subarulink."""
import asyncio
import json
import time

import subarulink
import subarulink.const as sc

# https://solidabstractions.com/2018/testing-aiohttp-client
from tests.aiohttp import CaseControlledTestServer, http_redirect
from tests.api_responses import (
    LOGIN_MULTI_REGISTERED,
    LOGIN_SINGLE_REGISTERED,
    REFRESH_VEHICLES_MULTI_1,
    REFRESH_VEHICLES_MULTI_2,
    REFRESH_VEHICLES_MULTI_3,
    REFRESH_VEHICLES_MULTI_4,
    REFRESH_VEHICLES_MULTI_5,
    REFRESH_VEHICLES_SINGLE,
    SELECT_VEHICLE_1,
    SELECT_VEHICLE_2,
    SELECT_VEHICLE_3,
    SELECT_VEHICLE_4,
    SELECT_VEHICLE_5,
)
from tests.certificate import ssl_certificate

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


async def setup_multi_session(server, http_redirect):
    """

    Set up a multi-car account authenticated session for testing.

    Use in a test case to obtain a controller object that is logged into a multi-vehicle account.

    """
    http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
    controller = subarulink.Controller(
        http_redirect.session, TEST_USERNAME, TEST_PASSWORD, TEST_DEVICE_ID, TEST_PIN, TEST_DEVICE_NAME,
    )
    task = asyncio.create_task(controller.connect())

    await server_js_response(server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)

    await server_js_response(
        server, SELECT_VEHICLE_1, path=sc.API_SELECT_VEHICLE, query={"vin": TEST_VIN_1_G1, "_": str(int(time.time()))},
    )
    await server_js_response(
        server, REFRESH_VEHICLES_MULTI_1, path=sc.API_REFRESH_VEHICLES, query={"_": str(int(time.time()))},
    )

    await server_js_response(
        server, SELECT_VEHICLE_2, path=sc.API_SELECT_VEHICLE, query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(
        server, REFRESH_VEHICLES_MULTI_2, path=sc.API_REFRESH_VEHICLES, query={"_": str(int(time.time()))},
    )

    await server_js_response(
        server, SELECT_VEHICLE_3, path=sc.API_SELECT_VEHICLE, query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        server, REFRESH_VEHICLES_MULTI_3, path=sc.API_REFRESH_VEHICLES, query={"_": str(int(time.time()))},
    )

    await server_js_response(
        server,
        SELECT_VEHICLE_4,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_4_SAFETY_PLUS, "_": str(int(time.time()))},
    )
    await server_js_response(
        server, REFRESH_VEHICLES_MULTI_4, path=sc.API_REFRESH_VEHICLES, query={"_": str(int(time.time()))},
    )

    await server_js_response(
        server,
        SELECT_VEHICLE_5,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_5_G1_SECURITY, "_": str(int(time.time()))},
    )
    await server_js_response(
        server, REFRESH_VEHICLES_MULTI_5, path=sc.API_REFRESH_VEHICLES, query={"_": str(int(time.time()))},
    )

    assert await task
    return controller


async def setup_single_session(server, http_redirect):
    """

    Set up a single-car account authenticated session for testing.

    Use in a test case to obtain a controller object that is logged into a single-vehicle account.

    """
    http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
    controller = subarulink.Controller(
        http_redirect.session, TEST_USERNAME, TEST_PASSWORD, TEST_DEVICE_ID, TEST_PIN, TEST_DEVICE_NAME,
    )
    task = asyncio.create_task(controller.connect())

    await server_js_response(server, LOGIN_SINGLE_REGISTERED, path=sc.API_LOGIN)
    await server_js_response(
        server, SELECT_VEHICLE_1, path=sc.API_SELECT_VEHICLE, query={"vin": TEST_VIN_1_G1, "_": str(int(time.time()))},
    )
    await server_js_response(
        server, REFRESH_VEHICLES_SINGLE, path=sc.API_REFRESH_VEHICLES, query={"_": str(int(time.time()))},
    )
    assert await task
    return controller


def assert_vehicle_status(result, expected):
    assert result[sc.ODOMETER] == expected["data"][sc.VS_ODOMETER]
    assert result[sc.TIMESTAMP] == expected["data"][sc.VS_TIMESTAMP] / 1000
    assert result[sc.LONGITUDE] == expected["data"][sc.VS_LONGITUDE]
    assert result[sc.LATITUDE] == expected["data"][sc.VS_LATITUDE]
    assert result[sc.AVG_FUEL_CONSUMPTION] == expected["data"][sc.VS_AVG_FUEL_CONSUMPTION]
    assert result[sc.DIST_TO_EMPTY] == expected["data"][sc.VS_DIST_TO_EMPTY]
    assert result[sc.VEHICLE_STATE] == expected["data"][sc.VS_VEHICLE_STATE]
    assert result[sc.TIRE_PRESSURE_FL] == int(expected["data"][sc.VS_TIRE_PRESSURE_FL])
    assert result[sc.TIRE_PRESSURE_FR] == int(expected["data"][sc.VS_TIRE_PRESSURE_FR])
    assert result[sc.TIRE_PRESSURE_RL] == int(expected["data"][sc.VS_TIRE_PRESSURE_RL])
    assert result[sc.TIRE_PRESSURE_RR] == int(expected["data"][sc.VS_TIRE_PRESSURE_RR])
