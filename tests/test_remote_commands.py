"""Tests for subarulink remote commands."""
import asyncio
import time

import pytest

from subarulink._subaru_api.const import (
    API_EV_CHARGE_NOW,
    API_G1_HORN_LIGHTS_STATUS,
    API_G2_FETCH_RES_SUBARU_PRESETS,
    API_G2_FETCH_RES_USER_PRESETS,
    API_G2_REMOTE_ENGINE_START,
    API_G2_REMOTE_ENGINE_STOP,
    API_G2_SAVE_RES_QUICK_START_SETTINGS,
    API_G2_SAVE_RES_SETTINGS,
    API_HORN_LIGHTS,
    API_HORN_LIGHTS_STOP,
    API_LIGHTS,
    API_LIGHTS_STOP,
    API_LOCK,
    API_LOGIN,
    API_REMOTE_SVC_STATUS,
    API_SELECT_VEHICLE,
    API_UNLOCK,
    API_VALIDATE_SESSION,
)
import subarulink.const as sc
from subarulink.exceptions import (
    InvalidPIN,
    PINLockoutProtect,
    RemoteServiceFailure,
    VehicleNotSupported,
)

from tests.api_responses import (
    FETCH_SUBARU_CLIMATE_PRESETS,
    FETCH_USER_CLIMATE_PRESETS_EV,
    LOCATE_G1_EXECUTE,
    LOCATE_G1_STARTED,
    LOGIN_MULTI_REGISTERED,
    REMOTE_CMD_INVALID_PIN,
    REMOTE_SERVICE_EXECUTE,
    REMOTE_SERVICE_STATUS_FINISHED_FAIL,
    REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
    REMOTE_SERVICE_STATUS_INVALID_TOKEN,
    REMOTE_SERVICE_STATUS_STARTED,
    SELECT_VEHICLE_2,
    SELECT_VEHICLE_3,
    SELECT_VEHICLE_5,
    SUBARU_PRESET_1,
    TEST_USER_PRESET_1,
    UPDATE_USER_CLIMATE_PRESETS,
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


async def test_remote_cmds_g2_ev(test_server, multi_vehicle_controller):
    cmd_list = [
        {
            "command": multi_vehicle_controller.horn(TEST_VIN_2_EV),
            "path": API_HORN_LIGHTS,
        },
        {
            "command": multi_vehicle_controller.horn_stop(TEST_VIN_2_EV),
            "path": API_HORN_LIGHTS_STOP,
        },
        {
            "command": multi_vehicle_controller.lights(TEST_VIN_2_EV),
            "path": API_LIGHTS,
        },
        {
            "command": multi_vehicle_controller.lights_stop(TEST_VIN_2_EV),
            "path": API_LIGHTS_STOP,
        },
        {
            "command": multi_vehicle_controller.lock(TEST_VIN_2_EV),
            "path": API_LOCK,
        },
        {
            "command": multi_vehicle_controller.unlock(TEST_VIN_2_EV),
            "path": API_UNLOCK,
        },
        {
            "command": multi_vehicle_controller.charge_start(TEST_VIN_2_EV),
            "path": API_EV_CHARGE_NOW,
        },
        {
            "command": multi_vehicle_controller.remote_stop(TEST_VIN_2_EV),
            "path": API_G2_REMOTE_ENGINE_STOP,
        },
    ]

    for cmd in cmd_list:
        task = asyncio.create_task(cmd["command"])
        await server_js_response(test_server, VALIDATE_SESSION_FAIL, path=API_VALIDATE_SESSION)
        await server_js_response(test_server, LOGIN_MULTI_REGISTERED, path=API_LOGIN)
        await server_js_response(
            test_server,
            SELECT_VEHICLE_2,
            path=API_SELECT_VEHICLE,
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
            path=API_REMOTE_SVC_STATUS,
        )
        await server_js_response(
            test_server,
            REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
            path=API_REMOTE_SVC_STATUS,
        )
        assert await task


async def test_remote_cmds_g1(test_server, multi_vehicle_controller):
    cmd_list = [
        {
            "command": multi_vehicle_controller.horn(TEST_VIN_5_G1_SECURITY),
            "path": API_HORN_LIGHTS,
            "status_url": API_G1_HORN_LIGHTS_STATUS,
        },
        {
            "command": multi_vehicle_controller.horn_stop(TEST_VIN_5_G1_SECURITY),
            "path": API_HORN_LIGHTS_STOP,
            "status_url": API_G1_HORN_LIGHTS_STATUS,
        },
        {
            "command": multi_vehicle_controller.lights(TEST_VIN_5_G1_SECURITY),
            "path": API_LIGHTS,
            "status_url": API_G1_HORN_LIGHTS_STATUS,
        },
        {
            "command": multi_vehicle_controller.lights_stop(TEST_VIN_5_G1_SECURITY),
            "path": API_LIGHTS_STOP,
            "status_url": API_G1_HORN_LIGHTS_STATUS,
        },
        {
            "command": multi_vehicle_controller.lock(TEST_VIN_5_G1_SECURITY),
            "path": API_LOCK,
            "status_url": API_REMOTE_SVC_STATUS,
        },
        {
            "command": multi_vehicle_controller.unlock(TEST_VIN_5_G1_SECURITY),
            "path": API_UNLOCK,
            "status_url": API_REMOTE_SVC_STATUS,
        },
    ]

    for cmd in cmd_list:
        task = asyncio.create_task(cmd["command"])
        await server_js_response(test_server, VALIDATE_SESSION_FAIL, path=API_VALIDATE_SESSION)
        await server_js_response(test_server, LOGIN_MULTI_REGISTERED, path=API_LOGIN)
        await server_js_response(
            test_server,
            SELECT_VEHICLE_5,
            path=API_SELECT_VEHICLE,
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
        multi_vehicle_controller.remote_start(TEST_VIN_4_SAFETY_PLUS, "Test"),
        multi_vehicle_controller.update(TEST_VIN_4_SAFETY_PLUS),
    ]

    for cmd in cmd_list:
        task = asyncio.create_task(cmd)
        with pytest.raises(VehicleNotSupported):
            assert not await task


async def test_vehicle_remote_cmd_invalid_pin(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_3_G2))

    assert not multi_vehicle_controller.invalid_pin_entered()
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(test_server, REMOTE_CMD_INVALID_PIN, path=API_LIGHTS)
    with pytest.raises(InvalidPIN):
        assert not await task
        assert multi_vehicle_controller.invalid_pin_entered()


async def test_vehicle_remote_cmd_invalid_pin_twice(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_3_G2))

    assert not multi_vehicle_controller.invalid_pin_entered()
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        REMOTE_CMD_INVALID_PIN,
        path=API_LIGHTS,
    )
    with pytest.raises(InvalidPIN):
        assert not await task
        assert multi_vehicle_controller.invalid_pin_entered()

    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_3_G2))
    with pytest.raises(PINLockoutProtect):
        await task


async def test_remote_cmd_failure(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_3_G2))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=API_LIGHTS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_STARTED,
        path=API_REMOTE_SVC_STATUS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_FINISHED_FAIL,
        path=API_REMOTE_SVC_STATUS,
    )
    with pytest.raises(RemoteServiceFailure):
        assert not await task


async def test_remote_cmd_timeout_g2(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_3_G2))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=API_LIGHTS,
    )
    for _ in range(0, 20):
        await server_js_response(
            test_server,
            REMOTE_SERVICE_STATUS_STARTED,
            path=API_REMOTE_SVC_STATUS,
        )

    with pytest.raises(RemoteServiceFailure):
        assert not await task


async def test_remote_cmd_invalid_token(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_3_G2))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=API_LIGHTS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_STARTED,
        path=API_REMOTE_SVC_STATUS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_INVALID_TOKEN,
        path=API_REMOTE_SVC_STATUS,
    )
    ## Session cookies cleared due to InvalidToken
    await server_js_response(test_server, VALIDATE_SESSION_FAIL, path=API_VALIDATE_SESSION)
    await server_js_response(test_server, LOGIN_MULTI_REGISTERED, path=API_LOGIN)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )

    ## Continue with checking for remote service status
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_STARTED,
        path=API_REMOTE_SVC_STATUS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
        path=API_REMOTE_SVC_STATUS,
    )

    assert await task


async def test_remote_cmd_timeout_g1(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.lights(TEST_VIN_5_G1_SECURITY))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        LOCATE_G1_EXECUTE,
        path=API_LIGHTS,
    )
    for _ in range(0, 20):
        await server_js_response(test_server, LOCATE_G1_STARTED, path=API_G1_HORN_LIGHTS_STATUS)

    with pytest.raises(RemoteServiceFailure):
        assert not await task


async def test_delete_climate_preset_by_name(test_server, multi_vehicle_controller):
    task = asyncio.create_task(
        multi_vehicle_controller.delete_climate_preset_by_name(TEST_VIN_2_EV, TEST_USER_PRESET_1)
    )
    await server_js_response(test_server, FETCH_SUBARU_CLIMATE_PRESETS, path=API_G2_FETCH_RES_SUBARU_PRESETS)
    await server_js_response(test_server, FETCH_USER_CLIMATE_PRESETS_EV, path=API_G2_FETCH_RES_USER_PRESETS)
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        UPDATE_USER_CLIMATE_PRESETS,
        path=API_G2_SAVE_RES_SETTINGS,
    )
    await server_js_response(test_server, FETCH_SUBARU_CLIMATE_PRESETS, path=API_G2_FETCH_RES_SUBARU_PRESETS)
    await server_js_response(test_server, FETCH_USER_CLIMATE_PRESETS_EV, path=API_G2_FETCH_RES_USER_PRESETS)
    assert await task


async def test_update_user_climate_presets(test_server, multi_vehicle_controller):
    new_preset_data = [
        {
            sc.REAR_AC: "false",
            sc.MODE: "AUTO",
            sc.FAN_SPEED: "AUTO",
            sc.TEMP_F: "71",
            sc.REAR_DEFROST: sc.REAR_DEFROST_OFF,
            sc.HEAT_SEAT_LEFT: "OFF",
            sc.HEAT_SEAT_RIGHT: "OFF",
            sc.RECIRCULATE: "outsideAir",
            sc.RUNTIME: "10",
            sc.PRESET_NAME: "Test",
        }
    ]

    task = asyncio.create_task(multi_vehicle_controller.update_user_climate_presets(TEST_VIN_2_EV, new_preset_data))
    await server_js_response(test_server, FETCH_SUBARU_CLIMATE_PRESETS, path=API_G2_FETCH_RES_SUBARU_PRESETS)
    await server_js_response(test_server, FETCH_USER_CLIMATE_PRESETS_EV, path=API_G2_FETCH_RES_USER_PRESETS)
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        UPDATE_USER_CLIMATE_PRESETS,
        path=API_G2_SAVE_RES_SETTINGS,
    )
    await server_js_response(test_server, FETCH_SUBARU_CLIMATE_PRESETS, path=API_G2_FETCH_RES_SUBARU_PRESETS)
    await server_js_response(test_server, FETCH_USER_CLIMATE_PRESETS_EV, path=API_G2_FETCH_RES_USER_PRESETS)
    assert await task


async def test_remote_start(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.remote_start(TEST_VIN_2_EV, SUBARU_PRESET_1))
    await server_js_response(test_server, FETCH_SUBARU_CLIMATE_PRESETS, path=API_G2_FETCH_RES_SUBARU_PRESETS)
    await server_js_response(test_server, FETCH_USER_CLIMATE_PRESETS_EV, path=API_G2_FETCH_RES_USER_PRESETS)
    await server_js_response(
        test_server,
        UPDATE_USER_CLIMATE_PRESETS,
        path=API_G2_SAVE_RES_QUICK_START_SETTINGS,
    )
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )

    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=API_G2_REMOTE_ENGINE_START,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_STARTED,
        path=API_REMOTE_SVC_STATUS,
    )
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
        path=API_REMOTE_SVC_STATUS,
    )

    assert await task
