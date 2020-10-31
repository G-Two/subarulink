""" Tests for subarulink. """
import asyncio
import json
import time
from unittest.mock import patch

from asynctest import CoroutineMock
import pytest

import subarulink
import subarulink.const as sc

# https://solidabstractions.com/2018/testing-aiohttp-client
# pylint: disable=unused-import
from tests.aiohttp import CaseControlledTestServer, http_redirect
from tests.certificate import TemporaryCertificate, ssl_certificate
from tests.responses import *

TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password"
TEST_DEVICE_ID = "9999999999"
TEST_PIN = "1234"
TEST_DEVICE_NAME = "subarulink test device"

TEST_VIN_1_G1 = "JF2ABCDE6L0000001"
TEST_VIN_2_EV = "JF2ABCDE6L0000002"
TEST_VIN_3_G2 = "JF2ABCDE6L0000003"
TEST_VIN_4_SAFETY_PLUS = "JF2ABCDE6L0000004"


async def server_js_response(server, response, path=None, query=None, status=200):
    request = await server.receive_request()
    if path and sc.MOBILE_API_VERSION in request.path:
        assert request.path == f"{sc.MOBILE_API_VERSION}{path}".replace("api_gen", "g2")
    else:
        assert request.path == path
    if query:
        assert query.get("vin") == request.query.get("vin")
    js_resp = json.dumps(response)
    server.send_response(request, text=js_resp, content_type="application/json", status=status)


# pylint: disable=redefined-outer-name
async def setup_multi_session(server, http_redirect):
    """

    Helper function to setup an authenticated session. Use in a test case to obtain
    a controller object that is logged into a multi-vehicle account.  The vehicle
    context is vehicle #4.

    """
    http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
    controller = subarulink.Controller(
        http_redirect.session,
        TEST_USERNAME,
        TEST_PASSWORD,
        TEST_DEVICE_ID,
        TEST_PIN,
        TEST_DEVICE_NAME,
    )
    task = asyncio.create_task(controller.connect())

    await server_js_response(server, login_multi_registered, path=sc.API_LOGIN)
    await server_js_response(
        server,
        refreshVehicles_multi,
        path=sc.API_REFRESH_VEHICLES,
        query={"_": str(int(time.time()))},
    )
    await server_js_response(
        server,
        selectVehicle_1,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_1_G1, "_": str(int(time.time()))},
    )
    await server_js_response(
        server,
        selectVehicle_2,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(
        server,
        selectVehicle_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(
        server,
        selectVehicle_4,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_4_SAFETY_PLUS, "_": str(int(time.time()))},
    )
    assert await task
    return controller


async def setup_single_session(server, http_redirect):
    """

    Helper function to setup an authenticated session. Use in a test case to obtain
    a controller object that is logged into a single-vehicle account.

    """
    http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
    controller = subarulink.Controller(
        http_redirect.session,
        TEST_USERNAME,
        TEST_PASSWORD,
        TEST_DEVICE_ID,
        TEST_PIN,
        TEST_DEVICE_NAME,
    )
    task = asyncio.create_task(controller.connect())

    await server_js_response(server, login_single_registered, path=sc.API_LOGIN)
    await server_js_response(
        server,
        refreshVehicles_single,
        path=sc.API_REFRESH_VEHICLES,
        query={"_": str(int(time.time()))},
    )
    assert await task
    return controller


@pytest.mark.asyncio
async def test_connect_incomplete_credentials(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session,
            TEST_USERNAME,
            None,
            TEST_DEVICE_ID,
            TEST_PIN,
            TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        with pytest.raises(subarulink.SubaruException):
            await task


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_connect_fail_authenticate(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session,
            TEST_USERNAME,
            TEST_PASSWORD,
            TEST_DEVICE_ID,
            TEST_PIN,
            TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        await server_js_response(server, login_invalid_password, path=sc.API_LOGIN)
        with pytest.raises(subarulink.SubaruException):
            await task


@pytest.mark.asyncio
async def test_handle_404(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session,
            TEST_USERNAME,
            TEST_PASSWORD,
            TEST_DEVICE_ID,
            TEST_PIN,
            TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        await server_js_response(server, login_invalid_password, path=sc.API_LOGIN, status=404)
        with pytest.raises(subarulink.SubaruException):
            await task


@pytest.mark.asyncio
async def test_connect_device_registration(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
            http_redirect.add_server(sc.WEB_API_SERVER, 443, server.port)
            controller = subarulink.Controller(
                http_redirect.session,
                TEST_USERNAME,
                TEST_PASSWORD,
                TEST_DEVICE_ID,
                TEST_PIN,
                TEST_DEVICE_NAME,
            )
            task = asyncio.create_task(controller.connect())

            await server_js_response(server, login_single_not_registered, path=sc.API_LOGIN)
            await server_js_response(
                server,
                refreshVehicles_single,
                path=sc.API_REFRESH_VEHICLES,
                query={"_": str(int(time.time()))},
            )
            await server_js_response(server, True, path=sc.WEB_API_LOGIN)
            await server_js_response(server, True, path=sc.WEB_API_AUTHORIZE_DEVICE)
            await server_js_response(server, True, path=sc.WEB_API_NAME_DEVICE)
            await server_js_response(server, login_single_not_registered, path=sc.API_LOGIN)
            await server_js_response(server, login_single_not_registered, path=sc.API_LOGIN)
            await server_js_response(server, login_single_registered, path=sc.API_LOGIN)

            response = await task
            assert response


@pytest.mark.asyncio
async def test_connect_single_car(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session,
            TEST_USERNAME,
            TEST_PASSWORD,
            TEST_DEVICE_ID,
            TEST_PIN,
            TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        await server_js_response(server, login_single_registered, path=sc.API_LOGIN)
        await server_js_response(
            server,
            refreshVehicles_single,
            path=sc.API_REFRESH_VEHICLES,
            query={"_": str(int(time.time()))},
        )

        response = await task
        assert response == True
        assert controller.get_vehicles() == [TEST_VIN_1_G1]
        assert controller.get_ev_status(TEST_VIN_1_G1) == False


@pytest.mark.asyncio
async def test_connect_multi_car(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session,
            TEST_USERNAME,
            TEST_PASSWORD,
            TEST_DEVICE_ID,
            TEST_PIN,
            TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        await server_js_response(server, login_multi_registered, path=sc.API_LOGIN)
        await server_js_response(
            server,
            refreshVehicles_multi,
            path=sc.API_REFRESH_VEHICLES,
            query={"_": str(int(time.time()))},
        )
        await server_js_response(
            server,
            selectVehicle_1,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_1_G1, "_": str(int(time.time()))},
        )
        await server_js_response(
            server,
            selectVehicle_2,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
        )
        await server_js_response(
            server,
            selectVehicle_3,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
        )
        await server_js_response(
            server,
            selectVehicle_4,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_4_SAFETY_PLUS, "_": str(int(time.time()))},
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
async def test_test_login(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server(sc.MOBILE_API_SERVER, 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session,
            TEST_USERNAME,
            TEST_PASSWORD,
            TEST_DEVICE_ID,
            TEST_PIN,
            TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect(test_login=True))

        await server_js_response(server, login_single_registered, path=sc.API_LOGIN)
        await server_js_response(
            server,
            refreshVehicles_single,
            path=sc.API_REFRESH_VEHICLES,
            query={"_": str(int(time.time()))},
        )

        response = await task
        assert response == True


@pytest.mark.asyncio
async def test_test_pin_success(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.test_pin())
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                selectVehicle_2,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            await server_js_response(server, vehicleStatus_EV, path=sc.API_VEHICLE_STATUS)
            assert await task


@pytest.mark.asyncio
async def test_test_pin_fail(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.test_pin())
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                selectVehicle_2,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            await server_js_response(server, remote_cmd_invalid_pin, path=sc.API_VEHICLE_STATUS)
            with pytest.raises(subarulink.InvalidPIN):
                await task

            assert not controller.update_saved_pin(TEST_PIN)
            assert controller.update_saved_pin("0000")


@pytest.mark.asyncio
async def test_get_vehicle_status_ev_security_plus(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_data(TEST_VIN_2_EV.lower()))
        await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
        await server_js_response(
            server,
            selectVehicle_2,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
        )
        await server_js_response(server, vehicleStatus_EV, path=sc.API_VEHICLE_STATUS)
        await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, condition_EV, path=sc.API_CONDITION)
        await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, locate_G2, path=sc.API_LOCATE)
        status = (await task)["status"]
        assert_vehicle_status(status, vehicleStatus_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_g2_security_plus(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_data(TEST_VIN_3_G2))
        await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
        await server_js_response(
            server,
            selectVehicle_3,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
        )
        await server_js_response(server, vehicleStatus_G2, path=sc.API_VEHICLE_STATUS)
        await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, condition_G2, path=sc.API_CONDITION)
        await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, locate_G2, path=sc.API_LOCATE)
        status = (await task)["status"]
        assert_vehicle_status(status, vehicleStatus_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_safety_plus(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_data(TEST_VIN_4_SAFETY_PLUS))
        await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, vehicleStatus_G2, path=sc.API_VEHICLE_STATUS)
        status = (await task)["status"]
        assert_vehicle_status(status, vehicleStatus_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_no_tire_pressure(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_data(TEST_VIN_4_SAFETY_PLUS))
        await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, vehicleStatus_G2_no_tire_pressure, path=sc.API_VEHICLE_STATUS)
        status = (await task)["status"]
        with pytest.raises(AssertionError):
            assert_vehicle_status(status, vehicleStatus_G2)
        assert not status[sc.TIRE_PRESSURE_FL]
        assert not status[sc.TIRE_PRESSURE_FR]
        assert not status[sc.TIRE_PRESSURE_RL]
        assert not status[sc.TIRE_PRESSURE_RR]


@pytest.mark.asyncio
async def test_get_vehicle_status_unsupported(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_data(TEST_VIN_1_G1))
        with pytest.raises(subarulink.SubaruException):
            await task


@pytest.mark.asyncio
async def test_vehicle_attributes(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            assert controller.vin_to_name(TEST_VIN_1_G1) == fake_car_data_1["nickname"]
            assert controller.vin_to_name(TEST_VIN_2_EV) == fake_car_data_2["nickname"]
            assert controller.vin_to_name(TEST_VIN_3_G2) == fake_car_data_3["nickname"]
            assert controller.vin_to_name(TEST_VIN_4_SAFETY_PLUS) == fake_car_data_4["nickname"]

            assert controller.get_api_gen(TEST_VIN_1_G1) == sc.FEATURE_G1_TELEMATICS
            assert controller.get_api_gen(TEST_VIN_2_EV) == sc.FEATURE_G2_TELEMATICS
            assert controller.get_api_gen(TEST_VIN_3_G2) == sc.FEATURE_G2_TELEMATICS
            assert controller.get_api_gen(TEST_VIN_4_SAFETY_PLUS) == sc.FEATURE_G2_TELEMATICS

            assert not controller.get_safety_status(TEST_VIN_1_G1)
            assert controller.get_safety_status(TEST_VIN_2_EV)
            assert controller.get_safety_status(TEST_VIN_3_G2)
            assert controller.get_safety_status(TEST_VIN_4_SAFETY_PLUS)

            assert not controller.get_ev_status(TEST_VIN_1_G1)
            assert controller.get_ev_status(TEST_VIN_2_EV)
            assert not controller.get_ev_status(TEST_VIN_3_G2)
            assert not controller.get_ev_status(TEST_VIN_4_SAFETY_PLUS)

            assert not controller.get_remote_status(TEST_VIN_1_G1)
            assert controller.get_remote_status(TEST_VIN_2_EV)
            assert controller.get_remote_status(TEST_VIN_3_G2)
            assert not controller.get_remote_status(TEST_VIN_4_SAFETY_PLUS)

            assert not controller.get_res_status(TEST_VIN_1_G1)
            assert not controller.get_res_status(TEST_VIN_2_EV)
            assert controller.get_res_status(TEST_VIN_3_G2)
            assert not controller.get_res_status(TEST_VIN_4_SAFETY_PLUS)


@pytest.mark.asyncio
async def test_update(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.update(TEST_VIN_2_EV))
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                selectVehicle_2,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            await server_js_response(
                server,
                vehicleStatus_execute,
                path=sc.API_G2_LOCATE_UPDATE,
            )
            await server_js_response(server, vehicleStatus_status_started, path=sc.API_G2_LOCATE_STATUS)
            await server_js_response(
                server,
                vehicleStatus_finished_success,
                path=sc.API_G2_LOCATE_STATUS,
            )
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, vehicleStatus_EV, path=sc.API_VEHICLE_STATUS)
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, condition_EV, path=sc.API_CONDITION)
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, locate_G2, path=sc.API_LOCATE)
            assert await task


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
                {
                    "command": controller.charge_start(TEST_VIN_2_EV),
                    "path": sc.API_EV_CHARGE_NOW,
                },
                {
                    "command": controller.remote_stop(TEST_VIN_2_EV),
                    "path": sc.API_G2_REMOTE_ENGINE_STOP,
                },
            ]

            for cmd in cmd_list:
                task = asyncio.create_task(cmd["command"])
                await server_js_response(server, validateSession_false, path=sc.API_VALIDATE_SESSION)
                await server_js_response(server, login_multi_registered, path=sc.API_LOGIN)
                await server_js_response(
                    server,
                    selectVehicle_3,
                    path=sc.API_SELECT_VEHICLE,
                    query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
                )
                await server_js_response(
                    server,
                    remoteService_execute,
                    path=cmd["path"],
                )
                await server_js_response(server, remoteService_status_started, path=sc.API_REMOTE_SVC_STATUS)
                await server_js_response(
                    server,
                    remoteService_status_finished_success,
                    path=sc.API_REMOTE_SVC_STATUS,
                )
                assert await task


@pytest.mark.asyncio
async def test_vehicle_remote_cmd_invalid_pin(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))

            assert not controller.invalid_pin_entered()
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                selectVehicle_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(server, remote_cmd_invalid_pin, path=sc.API_LIGHTS)
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
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                selectVehicle_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(
                server,
                remote_cmd_invalid_pin,
                path=sc.API_LIGHTS,
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

            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                selectVehicle_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(
                server,
                remoteService_execute,
                path=sc.API_LIGHTS,
            )
            await server_js_response(server, remoteService_status_started, path=sc.API_REMOTE_SVC_STATUS)
            await server_js_response(
                server,
                remoteService_status_finished_failed,
                path=sc.API_REMOTE_SVC_STATUS,
            )
            assert not await task


@pytest.mark.asyncio
async def test_remote_cmd_timeout(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))

            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                selectVehicle_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(
                server,
                remoteService_execute,
                path=sc.API_LIGHTS,
            )
            for _ in range(0, 20):
                await server_js_response(server, remoteService_status_started, path=sc.API_REMOTE_SVC_STATUS)

            assert not await task


@pytest.mark.asyncio
async def test_get_climate_settings(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_climate_settings(TEST_VIN_3_G2))
        await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
        await server_js_response(
            server,
            selectVehicle_3,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
        )
        await server_js_response(
            server,
            get_climate_settings_G2,
            path=sc.API_G2_FETCH_CLIMATE_SETTINGS,
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
        await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
        await server_js_response(
            server,
            selectVehicle_2,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
        )
        await server_js_response(
            server,
            save_climate_settings,
            path=sc.API_G2_SAVE_CLIMATE_SETTINGS,
        )
        assert await task


@pytest.mark.asyncio
async def test_remote_start_no_args(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.remote_start(TEST_VIN_3_G2))
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                selectVehicle_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(
                server,
                get_climate_settings_G2,
                path=sc.API_G2_FETCH_CLIMATE_SETTINGS,
            )
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                remoteService_execute,
                path=sc.API_G2_REMOTE_ENGINE_START,
            )
            await server_js_response(server, remoteService_status_started, path=sc.API_REMOTE_SVC_STATUS)
            await server_js_response(
                server,
                remoteService_status_finished_success,
                path=sc.API_REMOTE_SVC_STATUS,
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


@pytest.mark.asyncio
async def test_switch_vehicle(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_2_EV))

            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                selectVehicle_2,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            await server_js_response(server, remoteService_execute, path=sc.API_LIGHTS)
            await server_js_response(server, remoteService_status_started, path=sc.API_REMOTE_SVC_STATUS)
            await server_js_response(
                server,
                remoteService_status_finished_success,
                path=sc.API_REMOTE_SVC_STATUS,
            )

            assert await task


@pytest.mark.asyncio
async def test_expired_session(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.horn(TEST_VIN_3_G2))

            await server_js_response(server, validateSession_false, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, login_multi_registered, path=sc.API_LOGIN)
            await server_js_response(
                server,
                selectVehicle_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(
                server,
                remoteService_execute,
                path=sc.API_HORN_LIGHTS,
            )
            await server_js_response(
                server,
                remoteService_status_started,
                path=sc.API_REMOTE_SVC_STATUS,
            )
            await server_js_response(
                server,
                remoteService_status_finished_success,
                path=sc.API_REMOTE_SVC_STATUS,
            )

            assert await task


@pytest.mark.asyncio
async def test_403_during_remote_query(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.get_data(TEST_VIN_3_G2))

            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                selectVehicle_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(server, vehicleStatus_G2, path=sc.API_VEHICLE_STATUS)
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, error_403, path=sc.API_CONDITION)

            await server_js_response(server, validateSession_false, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, login_multi_registered, path=sc.API_LOGIN)
            await server_js_response(
                server,
                selectVehicle_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
            )
            await server_js_response(server, condition_G2, path=sc.API_CONDITION)
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, locate_G2, path=sc.API_LOCATE)
            result = await task
            assert result[sc.VEHICLE_STATUS][sc.BATTERY_VOLTAGE]


@pytest.mark.asyncio
async def test_403_during_remote_command(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.update(TEST_VIN_2_EV))
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server,
                selectVehicle_2,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            await server_js_response(
                server,
                error_403,
                path=sc.API_G2_LOCATE_UPDATE,
            )

            ## 403 Handling and reattempt
            await server_js_response(server, validateSession_false, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, login_multi_registered, path=sc.API_LOGIN)
            await server_js_response(
                server,
                selectVehicle_3,
                path=sc.API_SELECT_VEHICLE,
                query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
            )
            await server_js_response(
                server,
                vehicleStatus_execute,
                path=sc.API_G2_LOCATE_UPDATE,
            )
            ## Back to normal

            await server_js_response(server, vehicleStatus_status_started, path=sc.API_G2_LOCATE_STATUS)
            await server_js_response(
                server,
                vehicleStatus_finished_success,
                path=sc.API_G2_LOCATE_STATUS,
            )
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, vehicleStatus_EV, path=sc.API_VEHICLE_STATUS)
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, condition_EV, path=sc.API_CONDITION)
            await server_js_response(server, validateSession_true, path=sc.API_VALIDATE_SESSION)
            await server_js_response(server, locate_G2, path=sc.API_LOCATE)
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


def assert_vehicle_status(result, expected):
    assert result[sc.ODOMETER] == expected["data"][sc.VS_ODOMETER]
    assert result[sc.TIMESTAMP] == expected["data"][sc.VS_TIMESTAMP] / 1000
    assert result[sc.LONGITUDE] == expected["data"][sc.VS_LONGITUDE]
    assert result[sc.LATITUDE] == expected["data"][sc.VS_LATITUDE]
    assert result[sc.HEADING] == expected["data"][sc.VS_HEADING]
    assert result[sc.AVG_FUEL_CONSUMPTION] == expected["data"][sc.VS_AVG_FUEL_CONSUMPTION]
    assert result[sc.DIST_TO_EMPTY] == expected["data"][sc.VS_DIST_TO_EMPTY]
    assert result[sc.VEHICLE_STATE] == expected["data"][sc.VS_VEHICLE_STATE]
    assert result[sc.TIRE_PRESSURE_FL] == int(expected["data"][sc.VS_TIRE_PRESSURE_FL])
    assert result[sc.TIRE_PRESSURE_FR] == int(expected["data"][sc.VS_TIRE_PRESSURE_FR])
    assert result[sc.TIRE_PRESSURE_RL] == int(expected["data"][sc.VS_TIRE_PRESSURE_RL])
    assert result[sc.TIRE_PRESSURE_RR] == int(expected["data"][sc.VS_TIRE_PRESSURE_RR])
