"""Tests for subarulink vehicle status functions."""
import asyncio
import time

import pytest

import subarulink.const as sc

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
    SELECT_VEHICLE_1,
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
from tests.conftest import (
    TEST_VIN_1_G1,
    TEST_VIN_2_EV,
    TEST_VIN_3_G2,
    TEST_VIN_4_SAFETY_PLUS,
    TEST_VIN_5_G1_SECURITY,
    add_ev_vehicle_condition,
    add_ev_vehicle_status,
    add_g2_vehicle_locate,
    add_select_vehicle_sequence,
    add_validate_session,
    assert_vehicle_status,
    server_js_response,
)


@pytest.mark.asyncio
async def test_vehicle_attributes(multi_vehicle_controller):
    assert multi_vehicle_controller.vin_to_name(TEST_VIN_1_G1) == FAKE_CAR_DATA_1["nickname"]
    assert multi_vehicle_controller.vin_to_name(TEST_VIN_2_EV) == FAKE_CAR_DATA_2["nickname"]
    assert multi_vehicle_controller.vin_to_name(TEST_VIN_3_G2) == FAKE_CAR_DATA_3["nickname"]
    assert multi_vehicle_controller.vin_to_name(TEST_VIN_4_SAFETY_PLUS) == FAKE_CAR_DATA_4["nickname"]
    assert multi_vehicle_controller.vin_to_name(TEST_VIN_5_G1_SECURITY) == FAKE_CAR_DATA_5["nickname"]

    assert multi_vehicle_controller.get_api_gen(TEST_VIN_1_G1) == sc.FEATURE_G1_TELEMATICS
    assert multi_vehicle_controller.get_api_gen(TEST_VIN_2_EV) == sc.FEATURE_G2_TELEMATICS
    assert multi_vehicle_controller.get_api_gen(TEST_VIN_3_G2) == sc.FEATURE_G2_TELEMATICS
    assert multi_vehicle_controller.get_api_gen(TEST_VIN_4_SAFETY_PLUS) == sc.FEATURE_G2_TELEMATICS
    assert multi_vehicle_controller.get_api_gen(TEST_VIN_5_G1_SECURITY) == sc.FEATURE_G1_TELEMATICS

    assert not multi_vehicle_controller.get_safety_status(TEST_VIN_1_G1)
    assert multi_vehicle_controller.get_safety_status(TEST_VIN_2_EV)
    assert multi_vehicle_controller.get_safety_status(TEST_VIN_3_G2)
    assert multi_vehicle_controller.get_safety_status(TEST_VIN_4_SAFETY_PLUS)
    assert multi_vehicle_controller.get_safety_status(TEST_VIN_5_G1_SECURITY)

    assert not multi_vehicle_controller.get_ev_status(TEST_VIN_1_G1)
    assert multi_vehicle_controller.get_ev_status(TEST_VIN_2_EV)
    assert not multi_vehicle_controller.get_ev_status(TEST_VIN_3_G2)
    assert not multi_vehicle_controller.get_ev_status(TEST_VIN_4_SAFETY_PLUS)
    assert not multi_vehicle_controller.get_ev_status(TEST_VIN_5_G1_SECURITY)

    assert not multi_vehicle_controller.get_remote_status(TEST_VIN_1_G1)
    assert multi_vehicle_controller.get_remote_status(TEST_VIN_2_EV)
    assert multi_vehicle_controller.get_remote_status(TEST_VIN_3_G2)
    assert not multi_vehicle_controller.get_remote_status(TEST_VIN_4_SAFETY_PLUS)
    assert multi_vehicle_controller.get_remote_status(TEST_VIN_5_G1_SECURITY)

    assert not multi_vehicle_controller.get_res_status(TEST_VIN_1_G1)
    assert not multi_vehicle_controller.get_res_status(TEST_VIN_2_EV)
    assert multi_vehicle_controller.get_res_status(TEST_VIN_3_G2)
    assert not multi_vehicle_controller.get_res_status(TEST_VIN_4_SAFETY_PLUS)
    assert not multi_vehicle_controller.get_res_status(TEST_VIN_5_G1_SECURITY)


@pytest.mark.asyncio
async def test_get_vehicle_status_ev_security_plus(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_2_EV.lower()))
    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 2)
    await add_ev_vehicle_status(test_server)
    await add_validate_session(test_server)
    await add_ev_vehicle_condition(test_server)
    await add_validate_session(test_server)
    await add_g2_vehicle_locate(test_server)
    status = (await task)["status"]
    assert status[sc.LOCATION_VALID]
    assert_vehicle_status(status, VEHICLE_STATUS_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_ev_bad_location(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_2_EV.lower()))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_2,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_2_EV, "_": str(int(time.time()))},
    )
    await server_js_response(test_server, VEHICLE_STATUS_EV, path=sc.API_VEHICLE_STATUS)
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(test_server, CONDITION_EV, path=sc.API_CONDITION)
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(test_server, LOCATE_G2, path=sc.API_LOCATE)
    status = (await task)["status"]
    assert status[sc.LOCATION_VALID]
    assert_vehicle_status(status, VEHICLE_STATUS_G2)

    # Emulates a fetch after a Crosstrek PHEV is turned off, it will return bad coordinates
    task = asyncio.create_task(multi_vehicle_controller.fetch(TEST_VIN_2_EV.lower(), force=True))
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(test_server, VEHICLE_STATUS_EV, path=sc.API_VEHICLE_STATUS)
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(test_server, CONDITION_EV, path=sc.API_CONDITION)
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(test_server, LOCATE_G2_BAD_LOCATION, path=sc.API_LOCATE)
    await task
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_2_EV.lower()))
    status = (await task)["status"]

    # We should be informed that the current location is invalid/old
    assert not status[sc.LOCATION_VALID]

    # But still preserve the previous valid location
    assert_vehicle_status(status, VEHICLE_STATUS_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_g2_security_plus(test_server, multi_vehicle_controller):
    VALID_EXTERNAL_TEMP = "22.0"
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_3_G2))
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_3,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_3_G2, "_": str(int(time.time()))},
    )
    await server_js_response(test_server, VEHICLE_STATUS_G2, path=sc.API_VEHICLE_STATUS)
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)

    # Manually set EXTERNAL_TEMP to good value
    multi_vehicle_controller._vehicles[TEST_VIN_3_G2]["status"][sc.EXTERNAL_TEMP] = VALID_EXTERNAL_TEMP

    # This condition below includes a known erroneous EXTERNAL_TEMP, which should be discarded
    await server_js_response(test_server, CONDITION_G2, path=sc.API_CONDITION)
    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(test_server, LOCATE_G2, path=sc.API_LOCATE)
    status = (await task)["status"]
    assert status[sc.LOCATION_VALID]

    # Verify erroneous EXTERNAL TEMP was discarded
    assert status[sc.EXTERNAL_TEMP] == VALID_EXTERNAL_TEMP
    assert_vehicle_status(status, VEHICLE_STATUS_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_safety_plus(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_4_SAFETY_PLUS))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_4,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_4_SAFETY_PLUS, "_": str(int(time.time()))},
    )
    await server_js_response(test_server, VEHICLE_STATUS_G2, path=sc.API_VEHICLE_STATUS)

    status = (await task)["status"]
    assert_vehicle_status(status, VEHICLE_STATUS_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_no_tire_pressure(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_4_SAFETY_PLUS))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_4,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_4_SAFETY_PLUS, "_": str(int(time.time()))},
    )
    # Manually set Tire Pressures to good value
    good_data = VEHICLE_STATUS_G2["data"]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS]["status"][sc.TIRE_PRESSURE_FL] = good_data[
        sc.VS_TIRE_PRESSURE_FL
    ]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS]["status"][sc.TIRE_PRESSURE_FR] = good_data[
        sc.VS_TIRE_PRESSURE_FR
    ]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS]["status"][sc.TIRE_PRESSURE_RL] = good_data[
        sc.VS_TIRE_PRESSURE_RL
    ]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS]["status"][sc.TIRE_PRESSURE_RR] = good_data[
        sc.VS_TIRE_PRESSURE_RR
    ]

    # Provide no tire pressures, controller should ignore and keep previous
    await server_js_response(
        test_server,
        VEHICLE_STATUS_G2_NO_TIRE_PRESSURE,
        path=sc.API_VEHICLE_STATUS,
    )
    status = (await task)["status"]
    assert_vehicle_status(status, VEHICLE_STATUS_G2)


@pytest.mark.asyncio
async def test_get_vehicle_status_no_subscription(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_1_G1))

    await server_js_response(test_server, VALIDATE_SESSION_SUCCESS, path=sc.API_VALIDATE_SESSION)
    await server_js_response(
        test_server,
        SELECT_VEHICLE_1,
        path=sc.API_SELECT_VEHICLE,
        query={"vin": TEST_VIN_1_G1, "_": str(int(time.time()))},
    )
    await server_js_response(
        test_server,
        VEHICLE_STATUS_G2_NO_TIRE_PRESSURE,
        path=sc.API_VEHICLE_STATUS,
    )

    await task


@pytest.mark.asyncio
async def test_update_g2(test_server, multi_vehicle_controller):
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
        VEHICLE_STATUS_EXECUTE,
        path=sc.API_G2_LOCATE_UPDATE,
    )
    await server_js_response(test_server, VEHICLE_STATUS_STARTED, path=sc.API_G2_LOCATE_STATUS)
    await server_js_response(
        test_server,
        VEHICLE_STATUS_FINISHED_SUCCESS,
        path=sc.API_G2_LOCATE_STATUS,
    )

    assert await task


@pytest.mark.asyncio
async def test_update_g1(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.update(TEST_VIN_5_G1_SECURITY))

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
        path=sc.API_G1_LOCATE_UPDATE,
    )
    await server_js_response(test_server, LOCATE_G1_STARTED, path=sc.API_G1_LOCATE_STATUS)
    await server_js_response(
        test_server,
        LOCATE_G1_FINISHED,
        path=sc.API_G1_LOCATE_STATUS,
    )

    assert await task
