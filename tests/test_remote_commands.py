"""Tests for subarulink remote commands."""
import asyncio
import time

import pytest

import subarulink.const as sc
from subarulink.exceptions import (
    InvalidPIN,
    PINLockoutProtect,
    RemoteServiceFailure,
    SubaruException,
    VehicleNotSupported,
)

from tests.api_responses import (
    GET_CLIMATE_SETTINGS_G2,
    LOCATE_G1_EXECUTE,
    LOCATE_G1_STARTED,
    LOGIN_MULTI_REGISTERED,
    REMOTE_CMD_INVALID_PIN,
    REMOTE_SERVICE_EXECUTE,
    REMOTE_SERVICE_STATUS_FINISHED_FAIL,
    REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
    REMOTE_SERVICE_STATUS_STARTED,
    SAVE_CLIMATE_SETTINGS,
    SELECT_VEHICLE_2,
    SELECT_VEHICLE_3,
    SELECT_VEHICLE_5,
    VALIDATE_SESSION_FAIL,
    VALIDATE_SESSION_SUCCESS,
)
from tests.conftest import (
    TEST_VIN_2_EV,
    TEST_VIN_3_G2,
    TEST_VIN_4_SAFETY_PLUS,
    TEST_VIN_5_G1_SECURITY,
    server_js_response,
)


@pytest.mark.asyncio
async def test_remote_cmds_g2_ev(test_server, multi_vehicle_controller):
    cmd_list = [
        {
            "command": multi_vehicle_controller.horn(TEST_VIN_2_EV),
            "path": sc.API_HORN_LIGHTS,
        },
        {
            "command": multi_vehicle_controller.horn_stop(TEST_VIN_2_EV),
            "path": sc.API_HORN_LIGHTS_STOP,
        },
        {
            "command": multi_vehicle_controller.lights(TEST_VIN_2_EV),
            "path": sc.API_LIGHTS,
        },
        {
            "command": multi_vehicle_controller.lights_stop(TEST_VIN_2_EV),
            "path": sc.API_LIGHTS_STOP,
        },
        {
            "command": multi_vehicle_controller.lock(TEST_VIN_2_EV),
            "path": sc.API_LOCK,
        },
        {
            "command": multi_vehicle_controller.unlock(TEST_VIN_2_EV),
            "path": sc.API_UNLOCK,
        },
        {
            "command": multi_vehicle_controller.charge_start(TEST_VIN_2_EV),
            "path": sc.API_EV_CHARGE_NOW,
        },
        {
            "command": multi_vehicle_controller.remote_stop(TEST_VIN_2_EV),
            "path": sc.API_G2_REMOTE_ENGINE_STOP,
        },
    ]

    for cmd in cmd_list:
        task = asyncio.create_task(cmd["command"])
        await server_js_response(test_server, VALIDATE_SESSION_FAIL, path=sc.API_VALIDATE_SESSION)
        await server_js_response(test_server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)
        await server_js_response(
            test_server,
            SELECT_VEHICLE_2,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
        )
        await server_js_response(
            test_server,
            REMOTE_SERVICE_EXECUTE,
            path=cmd["path"],
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


@pytest.mark.asyncio
async def test_remote_cmds_g1(test_server, multi_vehicle_controller):
    cmd_list = [
        {
            "command": multi_vehicle_controller.horn(TEST_VIN_5_G1_SECURITY),
            "path": sc.API_HORN_LIGHTS,
            "status_url": sc.API_G1_HORN_LIGHTS_STATUS,
        },
        {
            "command": multi_vehicle_controller.horn_stop(TEST_VIN_5_G1_SECURITY),
            "path": sc.API_HORN_LIGHTS_STOP,
            "status_url": sc.API_G1_HORN_LIGHTS_STATUS,
        },
        {
            "command": multi_vehicle_controller.lights(TEST_VIN_5_G1_SECURITY),
            "path": sc.API_LIGHTS,
            "status_url": sc.API_G1_HORN_LIGHTS_STATUS,
        },
        {
            "command": multi_vehicle_controller.lights_stop(TEST_VIN_5_G1_SECURITY),
            "path": sc.API_LIGHTS_STOP,
            "status_url": sc.API_G1_HORN_LIGHTS_STATUS,
        },
        {
            "command": multi_vehicle_controller.lock(TEST_VIN_5_G1_SECURITY),
            "path": sc.API_LOCK,
            "status_url": sc.API_REMOTE_SVC_STATUS,
        },
        {
            "command": multi_vehicle_controller.unlock(TEST_VIN_5_G1_SECURITY),
            "path": sc.API_UNLOCK,
            "status_url": sc.API_REMOTE_SVC_STATUS,
        },
    ]

    for cmd in cmd_list:
        task = asyncio.create_task(cmd["command"])
        await server_js_response(test_server, VALIDATE_SESSION_FAIL, path=sc.API_VALIDATE_SESSION)
        await server_js_response(test_server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)
        await server_js_response(
            test_server,
            SELECT_VEHICLE_5,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_5_G1_SECURITY, "_": str(int(time.time()))},
        )
        await server_js_response(
            test_server,
            REMOTE_SERVICE_EXECUTE,
            path=cmd["path"],
        )
        await server_js_response(test_server, REMOTE_SERVICE_STATUS_STARTED, path=cmd["status_url"])
        await server_js_response(
            test_server,
            REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
            path=cmd["status_url"],
        )
        assert await task


@pytest.mark.asyncio
async def test_remote_cmds_unsupported(multi_vehicle_controller):
    cmd_list = [
        multi_vehicle_controller.horn(TEST_VIN_4_SAFETY_PLUS),
        multi_vehicle_controller.horn_stop(TEST_VIN_4_SAFETY_PLUS),
        multi_vehicle_controller.lights(TEST_VIN_4_SAFETY_PLUS),
        multi_vehicle_controller.lights_stop(TEST_VIN_4_SAFETY_PLUS),
        multi_vehicle_controller.lock(TEST_VIN_4_SAFETY_PLUS),
        multi_vehicle_controller.unlock(TEST_VIN_4_SAFETY_PLUS),
        multi_vehicle_controller.charge_start(TEST_VIN_4_SAFETY_PLUS),
        multi_vehicle_controller.remote_stop(TEST_VIN_4_SAFETY_PLUS),
        multi_vehicle_controller.get_climate_settings(TEST_VIN_4_SAFETY_PLUS),
        multi_vehicle_controller.save_climate_settings(TEST_VIN_4_SAFETY_PLUS, None),
        multi_vehicle_controller.remote_start(TEST_VIN_4_SAFETY_PLUS),
        multi_vehicle_controller.update(TEST_VIN_4_SAFETY_PLUS),
    ]

    for cmd in cmd_list:
        task = asyncio.create_task(cmd)
        with pytest.raises(VehicleNotSupported):
            assert not await task


@pytest.mark.asyncio
async def test_vehicle_remote_cmd_invalid_pin(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_3_G2))

    assert not multi_vehicle_controller.invalid_pin_entered()
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(test_server, REMOTE_CMD_INVALID_PIN, path=sc.API_LIGHTS)
    with pytest.raises(InvalidPIN):
        assert not await task
        assert multi_vehicle_controller.invalid_pin_entered()


@pytest.mark.asyncio
async def test_vehicle_remote_cmd_invalid_pin_twice(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_3_G2))

    assert not multi_vehicle_controller.invalid_pin_entered()
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        REMOTE_CMD_INVALID_PIN,
        path=sc.API_LIGHTS,
    )
    with pytest.raises(InvalidPIN):
        assert not await task
        assert multi_vehicle_controller.invalid_pin_entered()

    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_3_G2))
    with pytest.raises(PINLockoutProtect):
        await task


@pytest.mark.asyncio
async def test_remote_cmd_failure(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_3_G2))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=sc.API_LIGHTS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_STARTED,
        path=sc.API_REMOTE_SVC_STATUS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_FINISHED_FAIL,
        path=sc.API_REMOTE_SVC_STATUS,
    )
    with pytest.raises(RemoteServiceFailure):
        assert not await task


@pytest.mark.asyncio
async def test_remote_cmd_timeout_g2(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_3_G2))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=sc.API_LIGHTS,
    )
    for _ in range(0, 20):
        await server_js_response(
            test_server,
            REMOTE_SERVICE_STATUS_STARTED,
            path=sc.API_REMOTE_SVC_STATUS,
        )

    with pytest.raises(RemoteServiceFailure):
        assert not await task


@pytest.mark.asyncio
async def test_remote_cmd_timeout_g1(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_5_G1_SECURITY))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_5,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_5_G1_SECURITY, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        LOCATE_G1_EXECUTE,
        path=sc.API_LIGHTS,
    )
    for _ in range(0, 20):
        await server_js_response(test_server, LOCATE_G1_STARTED, path=sc.API_G1_HORN_LIGHTS_STATUS)

    with pytest.raises(RemoteServiceFailure):
        assert not await task


@pytest.mark.asyncio
async def test_get_climate_settings(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.get_climate_settings(TEST_VIN_3_G2))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        GET_CLIMATE_SETTINGS_G2,
        path=sc.API_G2_FETCH_CLIMATE_SETTINGS,
    )
    assert await task


@pytest.mark.asyncio
async def test_validate_climate_settings(multi_vehicle_controller):
    form_data = {
        sc.REAR_AC: None,
        sc.MODE: None,
        sc.FAN_SPEED: None,
        sc.TEMP_F: "100",
        sc.REAR_DEFROST: None,
        sc.HEAT_SEAT_LEFT: None,
        sc.HEAT_SEAT_RIGHT: None,
        sc.RECIRCULATE: None,
        sc.RUNTIME: None,
        sc.START_CONFIG: None,
    }
    task = asyncio.create_task(multi_vehicle_controller.save_climate_settings(TEST_VIN_3_G2, form_data))

    with pytest.raises(SubaruException):
        assert not await task


@pytest.mark.asyncio
async def test_save_climate_settings(test_server, multi_vehicle_controller):
    form_data = {
        sc.REAR_AC: "false",
        sc.MODE: "AUTO",
        sc.FAN_SPEED: "AUTO",
        sc.TEMP_F: "71",
        sc.REAR_DEFROST: sc.REAR_DEFROST_OFF,
        sc.HEAT_SEAT_LEFT: "OFF",
        sc.HEAT_SEAT_RIGHT: "OFF",
        sc.RECIRCULATE: "outsideAir",
        sc.RUNTIME: "10",
        sc.START_CONFIG: "start_Climate_Control_only_allow_key_in_ignition",
    }
    task = asyncio.create_task(multi_vehicle_controller.save_climate_settings(TEST_VIN_2_EV, form_data))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        SAVE_CLIMATE_SETTINGS,
        path=sc.API_G2_SAVE_CLIMATE_SETTINGS,
    )

    assert await task


@pytest.mark.asyncio
async def test_remote_start_no_args(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.remote_start(TEST_VIN_3_G2))
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        GET_CLIMATE_SETTINGS_G2,
        path=sc.API_G2_FETCH_CLIMATE_SETTINGS,
    )
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=sc.API_G2_REMOTE_ENGINE_START,
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


@pytest.mark.asyncio
async def test_remote_start_bad_args(multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.remote_start(TEST_VIN_3_G2, {"Bad": "Params"}))

    with pytest.raises(SubaruException):
        await task


@pytest.mark.asyncio
async def test_remote_start_good_args(test_server, multi_vehicle_controller):
    form_data = {
        sc.REAR_AC: "false",
        sc.MODE: "AUTO",
        sc.FAN_SPEED: "AUTO",
        sc.TEMP_F: "71",
        sc.REAR_DEFROST: sc.REAR_DEFROST_OFF,
        sc.HEAT_SEAT_LEFT: "OFF",
        sc.HEAT_SEAT_RIGHT: "OFF",
        sc.RECIRCULATE: "outsideAir",
    }
    task = asyncio.create_task(multi_vehicle_controller.remote_start(TEST_VIN_3_G2, form_data))
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=sc.API_G2_REMOTE_ENGINE_START,
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
