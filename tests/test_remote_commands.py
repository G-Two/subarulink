"""Tests for subarulink remote commands."""
import asyncio
import time
from unittest.mock import patch

from asynctest import CoroutineMock
import pytest

import subarulink
import subarulink.const as sc

from tests.aiohttp import CaseControlledTestServer, http_redirect
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
    VALIDATE_SESSION_FAIL,
    VALIDATE_SESSION_SUCCESS,
)
from tests.certificate import ssl_certificate
from tests.common import (
    TEST_VIN_2_EV,
    TEST_VIN_3_G2,
    TEST_VIN_4_SAFETY_PLUS,
    TEST_VIN_5_G1_SECURITY,
    server_js_response,
    setup_multi_session,
)


@pytest.mark.asyncio
async def test_remote_cmds(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            cmd_list = [
                {"command": controller.horn(TEST_VIN_2_EV), "path": sc.API_HORN_LIGHTS},
                {"command": controller.lights(TEST_VIN_2_EV), "path": sc.API_LIGHTS},
                {"command": controller.lock(TEST_VIN_2_EV), "path": sc.API_LOCK},
                {"command": controller.unlock(TEST_VIN_2_EV), "path": sc.API_UNLOCK},
                {"command": controller.charge_start(TEST_VIN_2_EV), "path": sc.API_EV_CHARGE_NOW},
                {"command": controller.remote_stop(TEST_VIN_2_EV), "path": sc.API_G2_REMOTE_ENGINE_STOP},
            ]

            for cmd in cmd_list:
                task = asyncio.create_task(cmd["command"])
                await server_js_response(server, VALIDATE_SESSION_FAIL, path=sc.API_VALIDATE_SESSION)
                await server_js_response(server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)
                await server_js_response(
                    server,
                    SELECT_VEHICLE_3,
                    path=sc.API_SELECT_VEHICLE,
                    query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
                )
                await server_js_response(
                    server, REMOTE_SERVICE_EXECUTE, path=cmd["path"],
                )
                await server_js_response(server, REMOTE_SERVICE_STATUS_STARTED, path=sc.API_REMOTE_SVC_STATUS)
                await server_js_response(
                    server, REMOTE_SERVICE_STATUS_FINISHED_SUCCESS, path=sc.API_REMOTE_SVC_STATUS,
                )
                assert await task


@pytest.mark.asyncio
async def test_vehicle_remote_cmd_invalid_pin(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))

            assert not controller.invalid_pin_entered()
            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                SELECT_VEHICLE_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(server, REMOTE_CMD_INVALID_PIN, path=sc.API_LIGHTS)
            with pytest.raises(subarulink.InvalidPIN):
                assert not await task
                assert controller.invalid_pin_entered()


@pytest.mark.asyncio
async def test_vehicle_remote_cmd_invalid_pin_twice(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))

            assert not controller.invalid_pin_entered()
            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                SELECT_VEHICLE_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(
                server, REMOTE_CMD_INVALID_PIN, path=sc.API_LIGHTS,
            )
            with pytest.raises(subarulink.InvalidPIN):
                assert not await task
                assert controller.invalid_pin_entered()

            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))
            with pytest.raises(subarulink.PINLockoutProtect):
                await task


@pytest.mark.asyncio
async def test_remote_cmd_failure(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))

            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                SELECT_VEHICLE_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(
                server, REMOTE_SERVICE_EXECUTE, path=sc.API_LIGHTS,
            )
            await server_js_response(server, REMOTE_SERVICE_STATUS_STARTED, path=sc.API_REMOTE_SVC_STATUS)
            await server_js_response(
                server, REMOTE_SERVICE_STATUS_FINISHED_FAIL, path=sc.API_REMOTE_SVC_STATUS,
            )
            assert not await task


@pytest.mark.asyncio
async def test_remote_cmd_timeout_g2(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))

            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                SELECT_VEHICLE_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(
                server, REMOTE_SERVICE_EXECUTE, path=sc.API_LIGHTS,
            )
            for _ in range(0, 20):
                await server_js_response(server, REMOTE_SERVICE_STATUS_STARTED, path=sc.API_REMOTE_SVC_STATUS)

            assert not await task


@pytest.mark.asyncio
async def test_remote_cmd_timeout_g1(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_5_G1_SECURITY))

            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server, LOCATE_G1_EXECUTE, path=sc.API_LIGHTS,
            )
            for _ in range(0, 20):
                await server_js_response(server, LOCATE_G1_STARTED, path=sc.API_REMOTE_SVC_STATUS)

            assert not await task


@pytest.mark.asyncio
async def test_get_climate_settings(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_climate_settings(TEST_VIN_3_G2))
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(
            server,
            SELECT_VEHICLE_3,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
        )
        await server_js_response(
            server, GET_CLIMATE_SETTINGS_G2, path=sc.API_G2_FETCH_CLIMATE_SETTINGS,
        )
        assert await task


@pytest.mark.asyncio
async def test_validate_climate_settings(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        form_data = {
            sc.REAR_AC: None,
            sc.MODE: None,
            sc.FAN_SPEED: None,
            sc.TEMP: "100",
            sc.REAR_DEFROST: None,
            sc.HEAT_SEAT_LEFT: None,
            sc.HEAT_SEAT_RIGHT: None,
            sc.RECIRCULATE: None,
            sc.RUNTIME: None,
            sc.START_CONFIG: None,
        }
        task = asyncio.create_task(controller.save_climate_settings(TEST_VIN_3_G2, form_data))

        assert not await task


@pytest.mark.asyncio
async def test_save_climate_settings(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        form_data = {
            sc.REAR_AC: "false",
            sc.MODE: "AUTO",
            sc.FAN_SPEED: "AUTO",
            sc.TEMP: "71",
            sc.REAR_DEFROST: sc.REAR_DEFROST_OFF,
            sc.HEAT_SEAT_LEFT: "OFF",
            sc.HEAT_SEAT_RIGHT: "OFF",
            sc.RECIRCULATE: "outsideAir",
            sc.RUNTIME: "10",
            sc.START_CONFIG: "start_Climate_Control_only_allow_key_in_ignition",
        }
        task = asyncio.create_task(controller.save_climate_settings(TEST_VIN_2_EV, form_data))
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(
            server,
            SELECT_VEHICLE_2,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
        )
        await server_js_response(
            server, SAVE_CLIMATE_SETTINGS, path=sc.API_G2_SAVE_CLIMATE_SETTINGS,
        )
        assert await task


@pytest.mark.asyncio
async def test_remote_start_no_args(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.remote_start(TEST_VIN_3_G2))
            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                SELECT_VEHICLE_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(
                server, GET_CLIMATE_SETTINGS_G2, path=sc.API_G2_FETCH_CLIMATE_SETTINGS,
            )
            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server, REMOTE_SERVICE_EXECUTE, path=sc.API_G2_REMOTE_ENGINE_START,
            )
            await server_js_response(server, REMOTE_SERVICE_STATUS_STARTED, path=sc.API_REMOTE_SVC_STATUS)
            await server_js_response(
                server, REMOTE_SERVICE_STATUS_FINISHED_SUCCESS, path=sc.API_REMOTE_SVC_STATUS,
            )

            assert await task


@pytest.mark.asyncio
async def test_remote_start_bad_args(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)
            task = asyncio.create_task(controller.remote_start(TEST_VIN_3_G2, {"Bad": "Params"}))
            with pytest.raises(subarulink.SubaruException):
                await task


@pytest.mark.asyncio
async def test_remote_cmd_unsupported(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)
            task = asyncio.create_task(controller.lights(TEST_VIN_4_SAFETY_PLUS))
            with pytest.raises(subarulink.SubaruException):
                await task
