"""Tests for subarulink connection functions."""
import asyncio
import time

import pytest

import subarulink
import subarulink.const as sc
from subarulink.exceptions import SubaruException

from tests.api_responses import (
    CONDITION_EV,
    ERROR_403,
    ERROR_VEHICLE_SETUP,
    ERROR_VIN_NOT_FOUND,
    FETCH_SUBARU_CLIMATE_PRESETS,
    FETCH_USER_CLIMATE_PRESETS_EV,
    LOCATE_G2,
    LOGIN_ERRORS,
    LOGIN_INVALID_PASSWORD,
    LOGIN_MULTI_REGISTERED,
    LOGIN_SINGLE_NOT_REGISTERED,
    LOGIN_SINGLE_REGISTERED,
    REMOTE_CMD_INVALID_PIN,
    REMOTE_SERVICE_EXECUTE,
    REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
    REMOTE_SERVICE_STATUS_STARTED,
    SELECT_VEHICLE_1,
    SELECT_VEHICLE_2,
    SELECT_VEHICLE_3,
    VALIDATE_SESSION_FAIL,
    VALIDATE_SESSION_SUCCESS,
    VEHICLE_STATUS_EV,
    VEHICLE_STATUS_EXECUTE,
    VEHICLE_STATUS_FINISHED_SUCCESS,
    VEHICLE_STATUS_STARTED,
)
from tests.conftest import (
    TEST_DEVICE_ID,
    TEST_DEVICE_NAME,
    TEST_PASSWORD,
    TEST_PIN,
    TEST_USERNAME,
    TEST_VIN_1_G1,
    TEST_VIN_2_EV,
    TEST_VIN_3_G2,
    TEST_VIN_4_SAFETY_PLUS,
    TEST_VIN_5_G1_SECURITY,
    server_js_response,
)


async def test_connect_incomplete_credentials():
    controller = subarulink.Controller(
        None,
        TEST_USERNAME,
        None,
        TEST_DEVICE_ID,
        TEST_PIN,
        TEST_DEVICE_NAME,
    )
    task = asyncio.create_task(controller.connect())

    with pytest.raises(subarulink.SubaruException):
        await task


async def test_no_dns(http_redirect):
    controller = subarulink.Controller(
        http_redirect.session,
        TEST_USERNAME,
        TEST_PASSWORD,
        TEST_DEVICE_ID,
        TEST_PIN,
        TEST_DEVICE_NAME,
    )
    task = asyncio.create_task(controller.connect())

    with pytest.raises(subarulink.SubaruException):
        await task


async def test_connect_fail_authenticate(test_server, controller):
    task = asyncio.create_task(controller.connect())

    await server_js_response(test_server, LOGIN_INVALID_PASSWORD, path=sc.API_LOGIN)
    with pytest.raises(subarulink.SubaruException):
        await task


async def test_handle_404(test_server, controller):
    task = asyncio.create_task(controller.connect())

    await server_js_response(test_server, LOGIN_INVALID_PASSWORD, path=sc.API_LOGIN, status=404)
    with pytest.raises(subarulink.SubaruException):
        await task


async def test_connect_device_registration_success(test_server, controller):
    task = asyncio.create_task(controller.connect())

    await server_js_response(test_server, LOGIN_SINGLE_NOT_REGISTERED, path=sc.API_LOGIN)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_1,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_1_G1, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server, {"success": True, "data": {"userName": "test@test.com"}}, path=sc.API_2FA_CONTACT
    )
    assert await task

    task = asyncio.create_task(controller.request_auth_code("userName"))
    await server_js_response(test_server, {"success": True}, path=sc.API_2FA_SEND_VERIFICATION)
    assert await task

    task = asyncio.create_task(controller.submit_auth_code("123456"))
    await server_js_response(test_server, {"success": True}, path=sc.API_2FA_AUTH_VERIFY)
    await server_js_response(test_server, LOGIN_SINGLE_NOT_REGISTERED, path=sc.API_LOGIN)
    await server_js_response(test_server, LOGIN_SINGLE_NOT_REGISTERED, path=sc.API_LOGIN)
    await server_js_response(test_server, LOGIN_SINGLE_REGISTERED, path=sc.API_LOGIN)
    assert await task


async def test_connect_device_registration_bad_input(test_server, controller):
    task = asyncio.create_task(controller.connect())

    await server_js_response(test_server, LOGIN_SINGLE_NOT_REGISTERED, path=sc.API_LOGIN)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_1,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_1_G1, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server, {"success": True, "data": {"userName": "test@test.com"}}, path=sc.API_2FA_CONTACT
    )
    assert await task

    task = asyncio.create_task(controller.request_auth_code("invalid_auth_type"))
    assert not await task

    task = asyncio.create_task(controller.submit_auth_code("invalid_code_format"))
    assert not await task


async def test_connect_single_car(single_vehicle_controller):
    assert single_vehicle_controller.get_vehicles() == [TEST_VIN_1_G1]
    assert single_vehicle_controller.get_ev_status(TEST_VIN_1_G1) is False


async def test_connect_multi_car(multi_vehicle_controller):
    vehicles = multi_vehicle_controller.get_vehicles()
    assert TEST_VIN_1_G1 in vehicles
    assert TEST_VIN_2_EV in vehicles
    assert TEST_VIN_3_G2 in vehicles
    assert TEST_VIN_4_SAFETY_PLUS in vehicles
    assert TEST_VIN_5_G1_SECURITY in vehicles
    assert not multi_vehicle_controller.get_ev_status(TEST_VIN_1_G1)
    assert multi_vehicle_controller.get_ev_status(TEST_VIN_2_EV)
    assert not multi_vehicle_controller.get_remote_status(TEST_VIN_1_G1)
    assert multi_vehicle_controller.get_remote_status(TEST_VIN_3_G2)
    assert not multi_vehicle_controller.get_res_status(TEST_VIN_1_G1)
    assert multi_vehicle_controller.get_remote_status(TEST_VIN_3_G2)
    assert not multi_vehicle_controller.get_safety_status(TEST_VIN_1_G1)
    assert multi_vehicle_controller.get_safety_status(TEST_VIN_4_SAFETY_PLUS)


async def test_login_fail(test_server, controller):
    for fail_msg in LOGIN_ERRORS:
        task = asyncio.create_task(controller.connect())
        await server_js_response(test_server, fail_msg, path=sc.API_LOGIN)
        with pytest.raises(subarulink.SubaruException):
            await task


async def test_test_pin_success(test_server, multi_vehicle_controller):
    assert multi_vehicle_controller.is_pin_required()
    task = asyncio.create_task(multi_vehicle_controller.test_pin())
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(test_server, VEHICLE_STATUS_EV, path=sc.API_G2_LOCATE_UPDATE)
    assert await task


async def test_test_pin_fail(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.test_pin())
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(test_server, REMOTE_CMD_INVALID_PIN, path=sc.API_G2_LOCATE_UPDATE)
    with pytest.raises(subarulink.InvalidPIN):
        await task

    assert not multi_vehicle_controller.update_saved_pin(TEST_PIN)
    assert multi_vehicle_controller.update_saved_pin("0000")


async def test_test_pin_not_needed(single_vehicle_controller):
    assert not single_vehicle_controller.is_pin_required()
    task = asyncio.create_task(single_vehicle_controller.test_pin())
    assert not await task


async def test_switch_vehicle_success(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_2_EV))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(test_server, REMOTE_SERVICE_EXECUTE, path=sc.API_LIGHTS)
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_STARTED,
        path=sc.API_REMOTE_SVC_STATUS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
        path=sc.API_REMOTE_SVC_STATUS,
    )

    assert await task


async def test_switch_vehicle_fail(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_2_EV))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        ERROR_VIN_NOT_FOUND,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    with pytest.raises(SubaruException):
        await task


async def test_switch_vehicle_setup_fail(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.horn(TEST_VIN_2_EV))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        ERROR_VEHICLE_SETUP,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(test_server, LOGIN_SINGLE_REGISTERED, path=sc.API_LOGIN)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=sc.API_HORN_LIGHTS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_STARTED,
        path=sc.API_REMOTE_SVC_STATUS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
        path=sc.API_REMOTE_SVC_STATUS,
    )
    assert await task


async def test_expired_session(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.horn(TEST_VIN_3_G2))

    await server_js_response(test_server, VALIDATE_SESSION_FAIL, path=sc.API_VALIDATE_SESSION)
    await server_js_response(test_server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=sc.API_HORN_LIGHTS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_STARTED,
        path=sc.API_REMOTE_SVC_STATUS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
        path=sc.API_REMOTE_SVC_STATUS,
    )

    assert await task


async def test_403_during_remote_query(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_2_EV))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(test_server, VEHICLE_STATUS_EV, path=sc.API_VEHICLE_STATUS)
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(test_server, ERROR_403, path=sc.API_CONDITION)
    await server_js_response(test_server, VALIDATE_SESSION_FAIL, path=sc.API_VALIDATE_SESSION)

    await server_js_response(test_server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(test_server, CONDITION_EV, path=sc.API_CONDITION)
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(test_server, LOCATE_G2, path=sc.API_LOCATE)
    await server_js_response(test_server, FETCH_SUBARU_CLIMATE_PRESETS, path=sc.API_G2_FETCH_RES_SUBARU_PRESETS)
    await server_js_response(test_server, FETCH_USER_CLIMATE_PRESETS_EV, path=sc.API_G2_FETCH_RES_USER_PRESETS)

    result = await task
    # assert result[sc.VEHICLE_STATUS][sc.BATTERY_VOLTAGE]


async def test_403_during_remote_command(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.update(TEST_VIN_2_EV))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        ERROR_403,
        path=sc.API_G2_LOCATE_UPDATE,
    )

    # 403 Handling and reattempt
    await server_js_response(test_server, VALIDATE_SESSION_FAIL, path=sc.API_VALIDATE_SESSION)
    await server_js_response(test_server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        VEHICLE_STATUS_EXECUTE,
        path=sc.API_G2_LOCATE_UPDATE,
    )

    # Back to normal
    await server_js_response(test_server, VEHICLE_STATUS_STARTED, path=sc.API_G2_LOCATE_STATUS)
    await server_js_response(
        test_server,
        VEHICLE_STATUS_FINISHED_SUCCESS,
        path=sc.API_G2_LOCATE_STATUS,
    )

    assert await task


async def test_interval_functions(multi_vehicle_controller):
    INVALID_NEW_INTERVAL = 25
    VALID_NEW_INTERVAL = 500

    assert multi_vehicle_controller.get_update_interval() == sc.DEFAULT_UPDATE_INTERVAL
    multi_vehicle_controller.set_update_interval(INVALID_NEW_INTERVAL)
    assert multi_vehicle_controller.get_update_interval() == sc.DEFAULT_UPDATE_INTERVAL
    multi_vehicle_controller.set_update_interval(VALID_NEW_INTERVAL)
    assert multi_vehicle_controller.get_update_interval() == VALID_NEW_INTERVAL
    assert multi_vehicle_controller.get_fetch_interval() == sc.DEFAULT_FETCH_INTERVAL
    multi_vehicle_controller.set_fetch_interval(INVALID_NEW_INTERVAL)
    assert multi_vehicle_controller.get_fetch_interval() == sc.DEFAULT_FETCH_INTERVAL
    multi_vehicle_controller.set_fetch_interval(VALID_NEW_INTERVAL)
    assert multi_vehicle_controller.get_fetch_interval() == VALID_NEW_INTERVAL
