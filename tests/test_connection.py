"""Tests for subarulink."""
import asyncio
import time
from unittest.mock import patch

from asynctest import CoroutineMock
import pytest

import subarulink
import subarulink.const as sc
from subarulink.exceptions import SubaruException

from tests.aiohttp import CaseControlledTestServer, http_redirect
from tests.api_responses import (
    CONDITION_G2,
    ERROR_403,
    ERROR_VIN_NOT_FOUND,
    LOCATE_G2,
    LOGIN_ERRORS,
    LOGIN_INVALID_PASSWORD,
    LOGIN_MULTI_REGISTERED,
    LOGIN_SINGLE_NOT_REGISTERED,
    LOGIN_SINGLE_REGISTERED,
    REFRESH_VEHICLES_MULTI,
    REFRESH_VEHICLES_SINGLE,
    REMOTE_CMD_INVALID_PIN,
    REMOTE_SERVICE_EXECUTE,
    REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
    REMOTE_SERVICE_STATUS_STARTED,
    SELECT_VEHICLE_1,
    SELECT_VEHICLE_2,
    SELECT_VEHICLE_3,
    SELECT_VEHICLE_4,
    SELECT_VEHICLE_5,
    VALIDATE_SESSION_FAIL,
    VALIDATE_SESSION_SUCCESS,
    VEHICLE_STATUS_EV,
    VEHICLE_STATUS_EXECUTE,
    VEHICLE_STATUS_FINISHED_SUCCESS,
    VEHICLE_STATUS_G2,
    VEHICLE_STATUS_STARTED,
)
from tests.certificate import ssl_certificate
from tests.common import (
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
    setup_multi_session,
    setup_single_session,
)


@pytest.mark.asyncio
async def test_connect_incomplete_credentials(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session, TEST_USERNAME, None, TEST_DEVICE_ID, TEST_PIN, TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        with pytest.raises(subarulink.SubaruException):
            await task


@pytest.mark.asyncio
async def test_no_dns(http_redirect):
    controller = subarulink.Controller(
        http_redirect.session, TEST_USERNAME, TEST_PASSWORD, TEST_DEVICE_ID, TEST_PIN, TEST_DEVICE_NAME,
    )
    task = asyncio.create_task(controller.connect())

    with pytest.raises(subarulink.SubaruException):
        await task


@pytest.mark.asyncio
async def test_connect_fail_authenticate(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session, TEST_USERNAME, TEST_PASSWORD, TEST_DEVICE_ID, TEST_PIN, TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        await server_js_response(server, LOGIN_INVALID_PASSWORD, path=sc.API_LOGIN)
        with pytest.raises(subarulink.SubaruException):
            await task


@pytest.mark.asyncio
async def test_handle_404(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session, TEST_USERNAME, TEST_PASSWORD, TEST_DEVICE_ID, TEST_PIN, TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        await server_js_response(server, LOGIN_INVALID_PASSWORD, path=sc.API_LOGIN, status=404)
        with pytest.raises(subarulink.SubaruException):
            await task


@pytest.mark.asyncio
async def test_connect_device_registration(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
            http_redirect.add_server(sc.WEB_API_SERVER, 443, server.port)
            controller = subarulink.Controller(
                http_redirect.session, TEST_USERNAME, TEST_PASSWORD, TEST_DEVICE_ID, TEST_PIN, TEST_DEVICE_NAME,
            )
            task = asyncio.create_task(controller.connect())

            await server_js_response(server, LOGIN_SINGLE_NOT_REGISTERED, path=sc.API_LOGIN)
            await server_js_response(
                server, REFRESH_VEHICLES_SINGLE, path=sc.API_REFRESH_VEHICLES, query={"_": str(int(time.time()))},
            )
            await server_js_response(server, True, path=sc.WEB_API_LOGIN)
            await server_js_response(server, True, path=sc.WEB_API_AUTHORIZE_DEVICE)
            await server_js_response(server, True, path=sc.WEB_API_NAME_DEVICE)
            await server_js_response(server, LOGIN_SINGLE_NOT_REGISTERED, path=sc.API_LOGIN)
            await server_js_response(server, LOGIN_SINGLE_NOT_REGISTERED, path=sc.API_LOGIN)
            await server_js_response(server, LOGIN_SINGLE_REGISTERED, path=sc.API_LOGIN)

            response = await task
            assert response


@pytest.mark.asyncio
async def test_connect_single_car(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session, TEST_USERNAME, TEST_PASSWORD, TEST_DEVICE_ID, TEST_PIN, TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        await server_js_response(server, LOGIN_SINGLE_REGISTERED, path=sc.API_LOGIN)
        await server_js_response(
            server, REFRESH_VEHICLES_SINGLE, path=sc.API_REFRESH_VEHICLES, query={"_": str(int(time.time()))},
        )

        response = await task
        assert response is True
        assert controller.get_vehicles() == [TEST_VIN_1_G1]
        assert controller.get_ev_status(TEST_VIN_1_G1) is False


@pytest.mark.asyncio
async def test_connect_multi_car(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session, TEST_USERNAME, TEST_PASSWORD, TEST_DEVICE_ID, TEST_PIN, TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        await server_js_response(server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)
        await server_js_response(
            server, REFRESH_VEHICLES_MULTI, path=sc.API_REFRESH_VEHICLES, query={"_": str(int(time.time()))},
        )
        await server_js_response(
            server,
            SELECT_VEHICLE_1,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_1_G1, "_": str(int(time.time()))},
        )
        await server_js_response(
            server,
            SELECT_VEHICLE_2,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
        )
        await server_js_response(
            server,
            SELECT_VEHICLE_3,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
        )
        await server_js_response(
            server,
            SELECT_VEHICLE_4,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_4_SAFETY_PLUS, "_": str(int(time.time()))},
        )
        await server_js_response(
            server,
            SELECT_VEHICLE_5,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_5_G1_SECURITY, "_": str(int(time.time()))},
        )

        response = await task
        assert response
        vehicles = controller.get_vehicles()
        assert TEST_VIN_1_G1 in vehicles
        assert TEST_VIN_2_EV in vehicles
        assert TEST_VIN_3_G2 in vehicles
        assert TEST_VIN_4_SAFETY_PLUS in vehicles
        assert not controller.get_ev_status(TEST_VIN_1_G1)
        assert controller.get_ev_status(TEST_VIN_2_EV)
        assert not controller.get_remote_status(TEST_VIN_1_G1)
        assert controller.get_remote_status(TEST_VIN_3_G2)
        assert not controller.get_res_status(TEST_VIN_1_G1)
        assert controller.get_remote_status(TEST_VIN_3_G2)
        assert not controller.get_safety_status(TEST_VIN_1_G1)
        assert controller.get_safety_status(TEST_VIN_4_SAFETY_PLUS)


@pytest.mark.asyncio
async def test_test_login_success(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session, TEST_USERNAME, TEST_PASSWORD, TEST_DEVICE_ID, TEST_PIN, TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect(test_login=True))

        await server_js_response(server, LOGIN_SINGLE_REGISTERED, path=sc.API_LOGIN)
        await server_js_response(
            server, REFRESH_VEHICLES_SINGLE, path=sc.API_REFRESH_VEHICLES, query={"_": str(int(time.time()))},
        )

        assert await task is True


@pytest.mark.asyncio
async def test_test_login_fail(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session, TEST_USERNAME, TEST_PASSWORD, TEST_DEVICE_ID, TEST_PIN, TEST_DEVICE_NAME,
        )

        for fail_msg in LOGIN_ERRORS:
            task = asyncio.create_task(controller.connect(test_login=True))
            await server_js_response(server, fail_msg, path=sc.API_LOGIN)
            with pytest.raises(subarulink.SubaruException):
                await task


@pytest.mark.asyncio
async def test_test_pin_success(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.test_pin())
            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                SELECT_VEHICLE_2,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            await server_js_response(server, VEHICLE_STATUS_EV, path=sc.API_G2_LOCATE_UPDATE)
            assert await task


@pytest.mark.asyncio
async def test_test_pin_fail(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.test_pin())
            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                SELECT_VEHICLE_2,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            await server_js_response(server, REMOTE_CMD_INVALID_PIN, path=sc.API_G2_LOCATE_UPDATE)
            with pytest.raises(subarulink.InvalidPIN):
                await task

            assert not controller.update_saved_pin(TEST_PIN)
            assert controller.update_saved_pin("0000")


@pytest.mark.asyncio
async def test_test_pin_not_needed(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_single_session(server, http_redirect)

            task = asyncio.create_task(controller.test_pin())
            assert not await task


@pytest.mark.asyncio
async def test_switch_vehicle_success(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_2_EV))

            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                SELECT_VEHICLE_2,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            await server_js_response(server, REMOTE_SERVICE_EXECUTE, path=sc.API_LIGHTS)
            await server_js_response(server, REMOTE_SERVICE_STATUS_STARTED, path=sc.API_REMOTE_SVC_STATUS)
            await server_js_response(
                server, REMOTE_SERVICE_STATUS_FINISHED_SUCCESS, path=sc.API_REMOTE_SVC_STATUS,
            )

            assert await task


@pytest.mark.asyncio
async def test_switch_vehicle_fail(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_2_EV))

            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                ERROR_VIN_NOT_FOUND,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            with pytest.raises(SubaruException):
                await task


@pytest.mark.asyncio
async def test_expired_session(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.horn(TEST_VIN_3_G2))

            await server_js_response(server, VALIDATE_SESSION_FAIL, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)
            await server_js_response(
                server,
                SELECT_VEHICLE_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(
                server, REMOTE_SERVICE_EXECUTE, path=sc.API_HORN_LIGHTS,
            )
            await server_js_response(
                server, REMOTE_SERVICE_STATUS_STARTED, path=sc.API_REMOTE_SVC_STATUS,
            )
            await server_js_response(
                server, REMOTE_SERVICE_STATUS_FINISHED_SUCCESS, path=sc.API_REMOTE_SVC_STATUS,
            )

            assert await task


@pytest.mark.asyncio
async def test_403_during_remote_query(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.get_data(TEST_VIN_3_G2))

            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                SELECT_VEHICLE_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(server, VEHICLE_STATUS_G2, path=sc.API_VEHICLE_STATUS)
            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, ERROR_403, path=sc.API_CONDITION)

            await server_js_response(server, VALIDATE_SESSION_FAIL, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)
            await server_js_response(
                server,
                SELECT_VEHICLE_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(server, CONDITION_G2, path=sc.API_CONDITION)
            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, LOCATE_G2, path=sc.API_LOCATE)
            result = await task
            assert result[sc.VEHICLE_STATUS][sc.BATTERY_VOLTAGE]


@pytest.mark.asyncio
async def test_403_during_remote_command(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.update(TEST_VIN_2_EV))
            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                SELECT_VEHICLE_2,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            await server_js_response(
                server, ERROR_403, path=sc.API_G2_LOCATE_UPDATE,
            )

            # 403 Handling and reattempt
            await server_js_response(server, VALIDATE_SESSION_FAIL, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, LOGIN_MULTI_REGISTERED, path=sc.API_LOGIN)
            await server_js_response(
                server,
                SELECT_VEHICLE_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            await server_js_response(
                server, VEHICLE_STATUS_EXECUTE, path=sc.API_G2_LOCATE_UPDATE,
            )
            # Back to normal

            await server_js_response(server, VEHICLE_STATUS_STARTED, path=sc.API_G2_LOCATE_STATUS)
            await server_js_response(
                server, VEHICLE_STATUS_FINISHED_SUCCESS, path=sc.API_G2_LOCATE_STATUS,
            )

            assert await task


@pytest.mark.asyncio
async def test_interval_functions(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

        INVALID_NEW_INTERVAL = 25
        VALID_NEW_INTERVAL = 500

        assert controller.get_update_interval() == sc.DEFAULT_UPDATE_INTERVAL
        controller.set_update_interval(INVALID_NEW_INTERVAL)
        assert controller.get_update_interval() == sc.DEFAULT_UPDATE_INTERVAL
        controller.set_update_interval(VALID_NEW_INTERVAL)
        assert controller.get_update_interval() == VALID_NEW_INTERVAL

        assert controller.get_fetch_interval() == sc.DEFAULT_FETCH_INTERVAL
        controller.set_fetch_interval(INVALID_NEW_INTERVAL)
        assert controller.get_fetch_interval() == sc.DEFAULT_FETCH_INTERVAL
        controller.set_fetch_interval(VALID_NEW_INTERVAL)
        assert controller.get_fetch_interval() == VALID_NEW_INTERVAL
