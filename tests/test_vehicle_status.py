"""Tests for subarulink."""
import asyncio
import time
from unittest.mock import patch

from asynctest import CoroutineMock
import pytest

import subarulink.const as sc

from tests.aiohttp import CaseControlledTestServer, http_redirect
from tests.api_responses import (
    CONDITION_EV,
    CONDITION_G2,
    FAKE_CAR_DATA_1,
    FAKE_CAR_DATA_2,
    FAKE_CAR_DATA_3,
    FAKE_CAR_DATA_4,
    FAKE_CAR_DATA_5,
    LOCATE_G1_EXECUTE,
    LOCATE_G1_FINISHED,
    LOCATE_G1_STARTED,
    LOCATE_G2,
    LOCATE_G2_BAD_LOCATION,
    SELECT_VEHICLE_2,
    SELECT_VEHICLE_3,
    SELECT_VEHICLE_4,
    SELECT_VEHICLE_5,
    VALIDATE_SESSION_SUCCESS,
    VEHICLE_STATUS_EV,
    VEHICLE_STATUS_EXECUTE,
    VEHICLE_STATUS_FINISHED_SUCCESS,
    VEHICLE_STATUS_G2,
    VEHICLE_STATUS_G2_NO_TIRE_PRESSURE,
    VEHICLE_STATUS_STARTED,
)
from tests.certificate import ssl_certificate
from tests.common import (
    TEST_VIN_1_G1,
    TEST_VIN_2_EV,
    TEST_VIN_3_G2,
    TEST_VIN_4_SAFETY_PLUS,
    TEST_VIN_5_G1_SECURITY,
    assert_vehicle_status,
    server_js_response,
    setup_multi_session,
)


@pytest.mark.asyncio
async def test_vehicle_attributes(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            assert controller.vin_to_name(TEST_VIN_1_G1) == FAKE_CAR_DATA_1["nickname"]
            assert controller.vin_to_name(TEST_VIN_2_EV) == FAKE_CAR_DATA_2["nickname"]
            assert controller.vin_to_name(TEST_VIN_3_G2) == FAKE_CAR_DATA_3["nickname"]
            assert controller.vin_to_name(TEST_VIN_4_SAFETY_PLUS) == FAKE_CAR_DATA_4["nickname"]
            assert controller.vin_to_name(TEST_VIN_5_G1_SECURITY) == FAKE_CAR_DATA_5["nickname"]

            assert controller.get_api_gen(TEST_VIN_1_G1) == sc.FEATURE_G1_TELEMATICS
            assert controller.get_api_gen(TEST_VIN_2_EV) == sc.FEATURE_G2_TELEMATICS
            assert controller.get_api_gen(TEST_VIN_3_G2) == sc.FEATURE_G2_TELEMATICS
            assert controller.get_api_gen(TEST_VIN_4_SAFETY_PLUS) == sc.FEATURE_G2_TELEMATICS
            assert controller.get_api_gen(TEST_VIN_5_G1_SECURITY) == sc.FEATURE_G1_TELEMATICS

            assert not controller.get_safety_status(TEST_VIN_1_G1)
            assert controller.get_safety_status(TEST_VIN_2_EV)
            assert controller.get_safety_status(TEST_VIN_3_G2)
            assert controller.get_safety_status(TEST_VIN_4_SAFETY_PLUS)
            assert controller.get_safety_status(TEST_VIN_5_G1_SECURITY)

            assert not controller.get_ev_status(TEST_VIN_1_G1)
            assert controller.get_ev_status(TEST_VIN_2_EV)
            assert not controller.get_ev_status(TEST_VIN_3_G2)
            assert not controller.get_ev_status(TEST_VIN_4_SAFETY_PLUS)
            assert not controller.get_ev_status(TEST_VIN_5_G1_SECURITY)

            assert not controller.get_remote_status(TEST_VIN_1_G1)
            assert controller.get_remote_status(TEST_VIN_2_EV)
            assert controller.get_remote_status(TEST_VIN_3_G2)
            assert not controller.get_remote_status(TEST_VIN_4_SAFETY_PLUS)
            assert controller.get_remote_status(TEST_VIN_5_G1_SECURITY)

            assert not controller.get_res_status(TEST_VIN_1_G1)
            assert not controller.get_res_status(TEST_VIN_2_EV)
            assert controller.get_res_status(TEST_VIN_3_G2)
            assert not controller.get_res_status(TEST_VIN_4_SAFETY_PLUS)
            assert not controller.get_res_status(TEST_VIN_5_G1_SECURITY)


@pytest.mark.asyncio
async def test_get_vehicle_status_ev_security_plus(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_data(TEST_VIN_2_EV.lower()))
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(
            server,
            SELECT_VEHICLE_2,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
        )
        await server_js_response(server, VEHICLE_STATUS_EV, path=sc.API_VEHICLE_STATUS)
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, CONDITION_EV, path=sc.API_CONDITION)
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, LOCATE_G2, path=sc.API_LOCATE)
        status = (await task)["status"]
        assert status[sc.LOCATION_VALID]
        assert_vehicle_status(status, VEHICLE_STATUS_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_ev_bad_location(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_data(TEST_VIN_2_EV.lower()))
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(
            server,
            SELECT_VEHICLE_2,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
        )
        await server_js_response(server, VEHICLE_STATUS_EV, path=sc.API_VEHICLE_STATUS)
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, CONDITION_EV, path=sc.API_CONDITION)
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, LOCATE_G2, path=sc.API_LOCATE)
        status = (await task)["status"]
        assert status[sc.LOCATION_VALID]
        assert_vehicle_status(status, VEHICLE_STATUS_G2)

        # Emulates a fetch after a Crosstrek PHEV is turned off, it will return bad coordinates
        task = asyncio.create_task(controller.fetch(TEST_VIN_2_EV.lower(), force=True))
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, VEHICLE_STATUS_EV, path=sc.API_VEHICLE_STATUS)
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, CONDITION_EV, path=sc.API_CONDITION)
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, LOCATE_G2_BAD_LOCATION, path=sc.API_LOCATE)
        await task
        task = asyncio.create_task(controller.get_data(TEST_VIN_2_EV.lower()))
        status = (await task)["status"]
        # We should be informed that the current location is invalid/old
        assert not status[sc.LOCATION_VALID]
        # But still preserve the previous valid location
        assert_vehicle_status(status, VEHICLE_STATUS_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_g2_security_plus(http_redirect, ssl_certificate):
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
        await server_js_response(server, CONDITION_G2, path=sc.API_CONDITION)
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(server, LOCATE_G2, path=sc.API_LOCATE)
        status = (await task)["status"]
        assert status[sc.LOCATION_VALID]
        assert_vehicle_status(status, VEHICLE_STATUS_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_safety_plus(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_data(TEST_VIN_4_SAFETY_PLUS))
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(
            server,
            SELECT_VEHICLE_4,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_4_SAFETY_PLUS, "_": str(int(time.time()))},
        )
        await server_js_response(server, VEHICLE_STATUS_G2, path=sc.API_VEHICLE_STATUS)
        status = (await task)["status"]
        assert_vehicle_status(status, VEHICLE_STATUS_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_no_tire_pressure(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_data(TEST_VIN_4_SAFETY_PLUS))
        await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
        await server_js_response(
            server,
            SELECT_VEHICLE_4,
            path=sc.API_SELECT_VEHICLE,
            query={"vin": TEST_VIN_4_SAFETY_PLUS, "_": str(int(time.time()))},
        )
        await server_js_response(server, VEHICLE_STATUS_G2_NO_TIRE_PRESSURE, path=sc.API_VEHICLE_STATUS)
        status = (await task)["status"]
        with pytest.raises(AssertionError):
            assert_vehicle_status(status, VEHICLE_STATUS_G2)
        assert not status[sc.TIRE_PRESSURE_FL]
        assert not status[sc.TIRE_PRESSURE_FR]
        assert not status[sc.TIRE_PRESSURE_RL]
        assert not status[sc.TIRE_PRESSURE_RR]


@pytest.mark.asyncio
async def test_get_vehicle_status_no_subscription(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)

        task = asyncio.create_task(controller.get_data(TEST_VIN_1_G1))
        assert await task


@pytest.mark.asyncio
async def test_update_g2(http_redirect, ssl_certificate):
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
                server, VEHICLE_STATUS_EXECUTE, path=sc.API_G2_LOCATE_UPDATE,
            )
            await server_js_response(server, VEHICLE_STATUS_STARTED, path=sc.API_G2_LOCATE_STATUS)
            await server_js_response(
                server, VEHICLE_STATUS_FINISHED_SUCCESS, path=sc.API_G2_LOCATE_STATUS,
            )

            assert await task


@pytest.mark.asyncio
async def test_update_g1(http_redirect, ssl_certificate):
    with patch("asyncio.sleep", new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.update(TEST_VIN_5_G1_SECURITY))
            await server_js_response(server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
            await server_js_response(
                server, LOCATE_G1_EXECUTE, path=sc.API_G1_LOCATE_UPDATE,
            )
            await server_js_response(server, LOCATE_G1_STARTED, path=sc.API_G1_LOCATE_STATUS)
            await server_js_response(
                server, LOCATE_G1_FINISHED, path=sc.API_G1_LOCATE_STATUS,
            )

            assert await task
