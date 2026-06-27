"""Tests for subarulink vehicle status functions."""

import asyncio
from datetime import UTC, datetime

import pytest

from subarulink._subaru_api.const import (
    API_AVG_FUEL_CONSUMPTION,
    API_CONDITION,
    API_DIST_TO_EMPTY,
    API_G1_LOCATE_STATUS,
    API_G1_LOCATE_UPDATE,
    API_G2_LOCATE_STATUS,
    API_G2_LOCATE_UPDATE,
    API_LOCATE,
    API_VEHICLE_HEALTH,
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
    VEHICLE_CONDITION_EV_FUEL_ZERO,
    VEHICLE_CONDITION_EV_NULL_EV_DTE,
    VEHICLE_CONDITION_EV_OLD_TIMESTAMP,
    VEHICLE_STATUS_EV,
    VEHICLE_STATUS_EV_BAD_SENSORS,
    VEHICLE_STATUS_EV_MISSING_DATA,
    VEHICLE_STATUS_EV_NULL_ODOMETER,
    VEHICLE_STATUS_EV_NULL_ODOMETER,
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
    # Pass 1: populate the status cache with good values
    task = asyncio.create_task(multi_vehicle_controller.fetch(TEST_VIN_4_SAFETY_PLUS, force=True))
    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 4)
    await server_js_response(test_server, VEHICLE_STATUS_EV, path=API_VEHICLE_STATUS)
    await task

    # Pass 2: fetch with missing data; controller should keep the previous good values
    task = asyncio.create_task(multi_vehicle_controller.fetch(TEST_VIN_4_SAFETY_PLUS, force=True))
    await add_validate_session(test_server)
    # _current_vin is already TEST_VIN_4_SAFETY_PLUS after pass 1 — no select_vehicle needed
    await server_js_response(test_server, VEHICLE_STATUS_EV_MISSING_DATA, path=API_VEHICLE_STATUS)
    await task

    status = (await multi_vehicle_controller.get_data(TEST_VIN_4_SAFETY_PLUS))[sc.VEHICLE_STATUS]
    assert_vehicle_status(status, VEHICLE_STATUS_EV)


async def test_get_vehicle_status_null_odometer(test_server, multi_vehicle_controller):
    """When the API returns null for odometerValue, status must not raise and must report sc.BAD_ODOMETER."""
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_4_SAFETY_PLUS))

    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 4)

    await server_js_response(
        test_server,
        VEHICLE_STATUS_EV_NULL_ODOMETER,
        path=API_VEHICLE_STATUS,
    )
    status = (await task)[sc.VEHICLE_STATUS]
    assert status[sc.ODOMETER] == sc.BAD_ODOMETER


async def test_get_vehicle_status_bad_sensor_values(test_server, multi_vehicle_controller):
    """When AVG_FUEL_CONSUMPTION and DIST_TO_EMPTY equal the bad sentinel 16383, the previous value is kept."""
    # Pass 1: populate cache with good sensor values
    task = asyncio.create_task(multi_vehicle_controller.fetch(TEST_VIN_4_SAFETY_PLUS, force=True))
    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 4)
    await server_js_response(test_server, VEHICLE_STATUS_EV, path=API_VEHICLE_STATUS)
    await task

    expected_avg_fuel = VEHICLE_STATUS_EV["data"][API_AVG_FUEL_CONSUMPTION]
    expected_dte = VEHICLE_STATUS_EV["data"][API_DIST_TO_EMPTY]

    # Pass 2: fetch with bad sensor values; controller should keep old values
    task = asyncio.create_task(multi_vehicle_controller.fetch(TEST_VIN_4_SAFETY_PLUS, force=True))
    await add_validate_session(test_server)
    # _current_vin is already TEST_VIN_4_SAFETY_PLUS after pass 1 — no select_vehicle needed
    await server_js_response(test_server, VEHICLE_STATUS_EV_BAD_SENSORS, path=API_VEHICLE_STATUS)
    await task

    status = (await multi_vehicle_controller.get_data(TEST_VIN_4_SAFETY_PLUS))[sc.VEHICLE_STATUS]
    assert status[sc.AVG_FUEL_CONSUMPTION] == expected_avg_fuel
    assert status[sc.DIST_TO_EMPTY] == expected_dte


async def test_get_vehicle_condition_remaining_fuel_zero(test_server, multi_vehicle_controller):
    """remaining_fuel_percent=0 (empty tank) must be stored, not skipped as falsy."""
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_2_EV.lower()))
    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 2)
    await add_ev_vehicle_status(test_server)
    await add_validate_session(test_server)
    await server_js_response(test_server, VEHICLE_CONDITION_EV_FUEL_ZERO, path=API_CONDITION)
    await add_validate_session(test_server)
    await add_g2_vehicle_locate(test_server)
    await add_validate_session(test_server)
    await add_vehicle_health(test_server)
    await add_fetch_climate_presets(test_server)
    status = (await task)[sc.VEHICLE_STATUS]
    assert status[sc.REMAINING_FUEL_PERCENT] == 0


async def test_get_vehicle_condition_ev_dte_null_is_int_zero(test_server, multi_vehicle_controller):
    """When evDistanceToEmpty is null the stored value must be int 0, not None."""
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_2_EV.lower()))
    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 2)
    await add_ev_vehicle_status(test_server)
    await add_validate_session(test_server)
    await server_js_response(test_server, VEHICLE_CONDITION_EV_NULL_EV_DTE, path=API_CONDITION)
    await add_validate_session(test_server)
    await add_g2_vehicle_locate(test_server)
    await add_validate_session(test_server)
    await add_vehicle_health(test_server)
    await add_fetch_climate_presets(test_server)
    status = (await task)[sc.VEHICLE_STATUS]
    assert status[sc.EV_DISTANCE_TO_EMPTY] == 0
    assert isinstance(status[sc.EV_DISTANCE_TO_EMPTY], int)


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


async def test_last_fetch_and_update_times_are_timezone_aware(multi_vehicle_controller):
    """get_last_fetch_time and get_last_update_time must return timezone-aware datetimes
    even before any fetch or update has been performed (Bug #12)."""
    fetch_time = multi_vehicle_controller.get_last_fetch_time(TEST_VIN_2_EV)
    update_time = multi_vehicle_controller.get_last_update_time(TEST_VIN_2_EV)

    assert fetch_time.tzinfo is not None, "VEHICLE_LAST_FETCH sentinel must be timezone-aware"
    assert update_time.tzinfo is not None, "VEHICLE_LAST_UPDATE sentinel must be timezone-aware"

    # Comparing with an aware datetime must not raise TypeError
    now = datetime.now(UTC)
    assert now > fetch_time
    assert now > update_time


def test_get_api_gen_highest_generation_wins():
    """When a vehicle has feature flags for multiple API generations, the highest generation must
    take precedence (Bug #13 – sequential if vs elif caused the last truthy assignment to win,
    which also happened to be highest; elif with reversed order makes the intent explicit)."""
    import subarulink._subaru_api.const as _api
    from subarulink.controller import Controller

    # G4 beats G2
    assert (
        Controller._api_gen_from_features([_api.API_FEATURE_G2_TELEMATICS, _api.API_FEATURE_G4_TELEMATICS])
        == _api.API_FEATURE_G4_TELEMATICS
    )
    # G3 beats G2
    assert (
        Controller._api_gen_from_features([_api.API_FEATURE_G2_TELEMATICS, _api.API_FEATURE_G3_TELEMATICS])
        == _api.API_FEATURE_G3_TELEMATICS
    )
    # G4 beats G3
    assert (
        Controller._api_gen_from_features([_api.API_FEATURE_G3_TELEMATICS, _api.API_FEATURE_G4_TELEMATICS])
        == _api.API_FEATURE_G4_TELEMATICS
    )
    # Single G1
    assert Controller._api_gen_from_features([_api.API_FEATURE_G1_TELEMATICS]) == _api.API_FEATURE_G1_TELEMATICS


async def test_fetch_status_returns_false_on_http_500_condition(test_server, multi_vehicle_controller):
    """When the Subaru backend returns HTTP 500 on the condition query, fetch must
    return False rather than raise (intermittent Subaru backend timeout, Bug #15)."""
    task = asyncio.create_task(multi_vehicle_controller.fetch(TEST_VIN_2_EV, force=True))
    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 2)
    await add_ev_vehicle_status(test_server)
    await add_validate_session(test_server)
    await server_js_response(test_server, {}, path=API_CONDITION, status=500)
    assert not await task


async def test_fetch_status_returns_false_on_http_500_health(test_server, multi_vehicle_controller):
    """When the Subaru backend returns HTTP 500 on the health query (after condition
    and locate succeed), fetch must still return False rather than raise."""
    task = asyncio.create_task(multi_vehicle_controller.fetch(TEST_VIN_2_EV, force=True))
    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 2)
    await add_ev_vehicle_status(test_server)
    await add_validate_session(test_server)
    await add_ev_vehicle_condition(test_server)
    await add_validate_session(test_server)
    await add_g2_vehicle_locate(test_server)
    await add_validate_session(test_server)
    await server_js_response(test_server, {}, path=API_VEHICLE_HEALTH, status=500)
    assert not await task


async def test_get_vehicle_condition_stores_window_lock_sunroof(test_server, multi_vehicle_controller):
    """Window, sunroof, and lock fields must be stored when the vehicle declares the
    corresponding feature flags (WDWSTAT, MOONSTAT, DOOR_LU_STAT in selectVehicle_2.json)."""
    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_2_EV))
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

    # Windows (WDWSTAT feature flag)
    assert status[sc.WINDOW_FRONT_LEFT_STATUS] == "VENTED"
    assert status[sc.WINDOW_REAR_LEFT_STATUS] == "CLOSED"

    # Sunroof (MOONSTAT feature flag)
    assert status[sc.WINDOW_SUNROOF_STATUS] == "CLOSED"

    # Locks (DOOR_LU_STAT feature flag)
    assert status[sc.LOCK_FRONT_LEFT_STATUS] == "LOCKED"
    assert status[sc.LOCK_BOOT_STATUS] == "UNLOCKED"


async def test_get_vehicle_condition_old_timestamp_format(test_server, multi_vehicle_controller):
    """_parse_condition must fall back to API_TIMESTAMP_FMT_OLD when the timestamp
    has no millisecond component (e.g. '2022-09-27T11:22:15+0000')."""
    from datetime import timezone, timedelta

    task = asyncio.create_task(multi_vehicle_controller.get_data(TEST_VIN_2_EV))
    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 2)
    await add_ev_vehicle_status(test_server)
    await add_validate_session(test_server)
    await server_js_response(test_server, VEHICLE_CONDITION_EV_OLD_TIMESTAMP, path=API_CONDITION)
    await add_validate_session(test_server)
    await add_g2_vehicle_locate(test_server)
    await add_validate_session(test_server)
    await add_vehicle_health(test_server)
    await add_fetch_climate_presets(test_server)
    status = (await task)[sc.VEHICLE_STATUS]

    # The old-format timestamp "2022-09-27T11:22:15+0000" must parse without error
    expected = datetime(2022, 9, 27, 11, 22, 15, tzinfo=timezone(timedelta(0)))
    assert status[sc.TIMESTAMP] == expected


def test_check_power_windows_feature_flag_windows_list():
    """_check_power_windows returns True when features contain a WINDOWS_LIST flag."""
    from subarulink.controller import Controller
    import subarulink._subaru_api.const as _api

    assert Controller._check_power_windows([_api.API_FEATURE_WINDOWS_LIST[0]], {}) is True


def test_check_power_windows_feature_flag_moonroof_list():
    """_check_power_windows returns True when features contain a MOONROOF_LIST flag."""
    from subarulink.controller import Controller
    import subarulink._subaru_api.const as _api
    import subarulink.const as sc

    assert Controller._check_power_windows([_api.API_FEATURE_MOONROOF_LIST[0]], {}) is True


def test_check_power_windows_data_presence_fallback():
    """_check_power_windows returns True when rear-window values are non-UNKNOWN in data."""
    from subarulink.controller import Controller
    import subarulink._subaru_api.const as _api
    import subarulink.const as sc

    data = {
        _api.API_WINDOW_REAR_LEFT_STATUS: "CLOSED",
        _api.API_WINDOW_REAR_RIGHT_STATUS: "CLOSED",
    }
    assert Controller._check_power_windows([], data) is True


def test_check_power_windows_returns_false_when_both_rear_unknown():
    """_check_power_windows returns False when rear windows are UNKNOWN and no feature flag."""
    from subarulink.controller import Controller
    import subarulink._subaru_api.const as _api
    import subarulink.const as sc

    data = {
        _api.API_WINDOW_REAR_LEFT_STATUS: sc.WINDOW_UNKNOWN,
        _api.API_WINDOW_REAR_RIGHT_STATUS: sc.WINDOW_UNKNOWN,
    }
    assert Controller._check_power_windows([], data) is False


def test_check_lock_status_feature_flag():
    """_check_lock_status returns True when the DOOR_LU_STAT feature flag is present."""
    from subarulink.controller import Controller
    import subarulink._subaru_api.const as _api

    assert Controller._check_lock_status([_api.API_FEATURE_LOCK_STATUS], {}) is True


def test_check_lock_status_data_presence_fallback():
    """_check_lock_status returns True when front-left lock is LOCKED or UNLOCKED in data."""
    from subarulink.controller import Controller
    import subarulink._subaru_api.const as _api
    import subarulink.const as sc

    for state in [sc.LOCK_LOCKED, sc.LOCK_UNLOCKED]:
        assert Controller._check_lock_status([], {_api.API_LOCK_FRONT_LEFT_STATUS: state}) is True


def test_check_lock_status_returns_false_without_feature_or_data():
    """_check_lock_status returns False when no feature flag and no valid lock data."""
    from subarulink.controller import Controller
    import subarulink._subaru_api.const as _api

    assert Controller._check_lock_status([], {}) is False
    assert Controller._check_lock_status([], {_api.API_LOCK_FRONT_LEFT_STATUS: "UNKNOWN"}) is False


async def test_sanitize_seat_settings_no_heated_or_ventilated(multi_vehicle_controller):
    """Seat heat/cool values are rewritten to OFF when vehicle lacks RHSF/RVFS features."""
    preset = {
        "name": "Full Heat",
        sc.HEAT_SEAT_LEFT: "high_heat",
        sc.HEAT_SEAT_RIGHT: "high_heat",
    }
    result = multi_vehicle_controller._sanitize_seat_settings(TEST_VIN_2_EV, preset)
    assert result[sc.HEAT_SEAT_LEFT] == sc.HEAT_SEAT_OFF
    assert result[sc.HEAT_SEAT_RIGHT] == sc.HEAT_SEAT_OFF

    cool_preset = {
        "name": "Full Cool",
        sc.HEAT_SEAT_LEFT: "high_cool",
        sc.HEAT_SEAT_RIGHT: "high_cool",
    }
    result = multi_vehicle_controller._sanitize_seat_settings(TEST_VIN_2_EV, cool_preset)
    assert result[sc.HEAT_SEAT_LEFT] == sc.HEAT_SEAT_OFF
    assert result[sc.HEAT_SEAT_RIGHT] == sc.HEAT_SEAT_OFF


async def test_sanitize_seat_settings_with_heated_and_ventilated(multi_vehicle_controller):
    """Seat heat/cool values are preserved when vehicle has both RHSF and RVFS features."""
    import subarulink._subaru_api.const as _api

    # Temporarily add both seat feature flags to the vehicle
    features = multi_vehicle_controller._get_vehicle(TEST_VIN_2_EV)[sc.VEHICLE_FEATURES]
    features.append(_api.API_FEATURE_REMOTE_HEATED_SEAT_FRONT)
    features.append(_api.API_FEATURE_REMOTE_VENTILATED_SEAT_FRONT)

    try:
        heat_preset = {
            "name": "Full Heat",
            sc.HEAT_SEAT_LEFT: "high_heat",
            sc.HEAT_SEAT_RIGHT: "high_heat",
        }
        result = multi_vehicle_controller._sanitize_seat_settings(TEST_VIN_2_EV, heat_preset)
        assert result[sc.HEAT_SEAT_LEFT] == "high_heat"
        assert result[sc.HEAT_SEAT_RIGHT] == "high_heat"

        cool_preset = {
            "name": "Full Cool",
            sc.HEAT_SEAT_LEFT: "high_cool",
            sc.HEAT_SEAT_RIGHT: "high_cool",
        }
        result = multi_vehicle_controller._sanitize_seat_settings(TEST_VIN_2_EV, cool_preset)
        assert result[sc.HEAT_SEAT_LEFT] == "high_cool"
        assert result[sc.HEAT_SEAT_RIGHT] == "high_cool"
    finally:
        features.remove(_api.API_FEATURE_REMOTE_HEATED_SEAT_FRONT)
        features.remove(_api.API_FEATURE_REMOTE_VENTILATED_SEAT_FRONT)
