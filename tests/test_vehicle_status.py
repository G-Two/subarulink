"""Tests for subarulink vehicle status functions."""
import asyncio

import pytest

from subarulink._subaru_api.const import (
    API_AVG_FUEL_CONSUMPTION,
    API_DIST_TO_EMPTY,
    API_G1_LOCATE_STATUS,
    API_G1_LOCATE_UPDATE,
    API_G2_LOCATE_STATUS,
    API_G2_LOCATE_UPDATE,
    API_LATITUDE,
    API_LOCATE,
    API_LONGITUDE,
    API_TIRE_PRESSURE_FL,
    API_TIRE_PRESSURE_FR,
    API_TIRE_PRESSURE_RL,
    API_TIRE_PRESSURE_RR,
    API_VEHICLE_STATE,
    API_VEHICLE_STATUS,
)
import subarulink.const as sc

from tests.api_responses import (
    LOCATE_G1_EXECUTE,
    LOCATE_G1_FINISHED,
    LOCATE_G1_STARTED,
    LOCATE_G2_BAD_LOCATION,
    SELECT_VEHICLE_1,
    SELECT_VEHICLE_2,
    SELECT_VEHICLE_3,
    SELECT_VEHICLE_4,
    SELECT_VEHICLE_5,
    VEHICLE_CONDITION_EV,
    VEHICLE_STATUS_EV,
    VEHICLE_STATUS_EV_MISSING_DATA,
    VEHICLE_STATUS_EXECUTE,
    VEHICLE_STATUS_FINISHED_SUCCESS,
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
    add_fetch_climate_presets,
    add_g2_vehicle_locate,
    add_select_vehicle_sequence,
    add_validate_session,
    add_vehicle_health,
    assert_vehicle_condition,
    assert_vehicle_status,
    server_js_response,
)


async def test_vehicle_attributes(multi_vehicle_controller):
    assert multi_vehicle_controller.vin_to_name(TEST_VIN_1_G1) == SELECT_VEHICLE_1["data"]["nickname"]
    assert multi_vehicle_controller.vin_to_name(TEST_VIN_2_EV) == SELECT_VEHICLE_2["data"]["nickname"]
    assert multi_vehicle_controller.vin_to_name(TEST_VIN_3_G2) == SELECT_VEHICLE_3["data"]["nickname"]
    assert multi_vehicle_controller.vin_to_name(TEST_VIN_4_SAFETY_PLUS) == SELECT_VEHICLE_4["data"]["nickname"]
    assert multi_vehicle_controller.vin_to_name(TEST_VIN_5_G1_SECURITY) == SELECT_VEHICLE_5["data"]["nickname"]

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


async def test_get_vehicle_status_ev_security_plus(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_2_EV.lower()))
    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 2)
    await add_ev_vehicle_status(test_server)
    await add_validate_session(test_server)
    await add_ev_vehicle_condition(test_server)
    await add_validate_session(test_server)
    await add_g2_vehicle_locate(test_server)
    await add_validate_session(test_server)
    await add_vehicle_health(test_server)
    await add_fetch_climate_presets(test_server)
    status = (await task)[sc.VEHICLE_STATUS]
    assert status[sc.LOCATION_VALID]
    assert_vehicle_status(status, VEHICLE_STATUS_EV)
    assert_vehicle_condition(status, VEHICLE_CONDITION_EV)


async def test_get_vehicle_status_ev_bad_location(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_2_EV.lower()))
    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 2)
    await add_ev_vehicle_status(test_server)
    await add_validate_session(test_server)
    await add_ev_vehicle_condition(test_server)
    await add_validate_session(test_server)
    await add_g2_vehicle_locate(test_server)
    await add_validate_session(test_server)
    await add_vehicle_health(test_server)
    await add_fetch_climate_presets(test_server)
    status = (await task)[sc.VEHICLE_STATUS]
    assert status[sc.LOCATION_VALID]
    assert_vehicle_status(status, VEHICLE_STATUS_EV)

    # Emulates a fetch after a Crosstrek PHEV is turned off, it will return bad coordinates
    task = asyncio.create_task(multi_vehicle_controller.fetch(TEST_VIN_2_EV.lower(), force=True))
    await add_validate_session(test_server)
    await add_ev_vehicle_status(test_server)
    await add_validate_session(test_server)
    await add_ev_vehicle_condition(test_server)
    await add_validate_session(test_server)
    await server_js_response(test_server, LOCATE_G2_BAD_LOCATION, path=API_LOCATE)
    await add_validate_session(test_server)
    await add_vehicle_health(test_server)
    await add_fetch_climate_presets(test_server)
    await task
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_2_EV.lower()))
    status = (await task)[sc.VEHICLE_STATUS]

    # We should be informed that the current location is invalid/old
    assert not status[sc.LOCATION_VALID]

    # But still preserve the previous valid location
    assert_vehicle_status(status, VEHICLE_STATUS_EV)


async def test_get_vehicle_status_missing_data(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_4_SAFETY_PLUS))

    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 4)

    # Manually set unreliable fields to good value
    good_data = VEHICLE_STATUS_EV["data"]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS][sc.VEHICLE_STATUS][sc.TIRE_PRESSURE_FL] = good_data[
        API_TIRE_PRESSURE_FL
    ]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS][sc.VEHICLE_STATUS][sc.TIRE_PRESSURE_FR] = good_data[
        API_TIRE_PRESSURE_FR
    ]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS][sc.VEHICLE_STATUS][sc.TIRE_PRESSURE_RL] = good_data[
        API_TIRE_PRESSURE_RL
    ]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS][sc.VEHICLE_STATUS][sc.TIRE_PRESSURE_RR] = good_data[
        API_TIRE_PRESSURE_RR
    ]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS][sc.VEHICLE_STATUS][sc.AVG_FUEL_CONSUMPTION] = good_data[
        API_AVG_FUEL_CONSUMPTION
    ]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS][sc.VEHICLE_STATUS][sc.DIST_TO_EMPTY] = good_data[
        API_DIST_TO_EMPTY
    ]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS][sc.VEHICLE_STATUS][sc.LONGITUDE] = good_data[
        API_LONGITUDE
    ]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS][sc.VEHICLE_STATUS][sc.LATITUDE] = good_data[API_LATITUDE]
    multi_vehicle_controller._vehicles[TEST_VIN_4_SAFETY_PLUS][sc.VEHICLE_STATUS][sc.VEHICLE_STATE] = good_data[
        API_VEHICLE_STATE
    ]

    # When VehicleStatus is missing data, controller should ignore and keep previous value
    await server_js_response(
        test_server,
        VEHICLE_STATUS_EV_MISSING_DATA,
        path=API_VEHICLE_STATUS,
    )
    status = (await task)[sc.VEHICLE_STATUS]
    assert_vehicle_status(status, VEHICLE_STATUS_EV)


async def test_update_g2(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.update(TEST_VIN_2_EV))

    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 2)

    await server_js_response(
        test_server,
        VEHICLE_STATUS_EXECUTE,
        path=API_G2_LOCATE_UPDATE,
    )
    await server_js_response(test_server, VEHICLE_STATUS_STARTED, path=API_G2_LOCATE_STATUS)
    await server_js_response(
        test_server,
        VEHICLE_STATUS_FINISHED_SUCCESS,
        path=API_G2_LOCATE_STATUS,
    )

    assert await task


async def test_update_g1(test_server, multi_vehicle_controller):
    task = asyncio.create_task(multi_vehicle_controller.update(TEST_VIN_5_G1_SECURITY))

    await add_validate_session(test_server)
    await server_js_response(
        test_server,
        LOCATE_G1_EXECUTE,
        path=API_G1_LOCATE_UPDATE,
    )
    await server_js_response(test_server, LOCATE_G1_STARTED, path=API_G1_LOCATE_STATUS)
    await server_js_response(
        test_server,
        LOCATE_G1_FINISHED,
        path=API_G1_LOCATE_STATUS,
    )

    assert await task
