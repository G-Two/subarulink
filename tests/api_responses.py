"""Subaru API responses used for tests."""
from copy import deepcopy
import json

import subarulink._subaru_api.const as api
import subarulink.const as sc


def read_json(filename, encoding=None, errors=None):
    """Read a JSON file and return a python object."""
    with open(f"tests/fixtures/{filename}", encoding=encoding, errors=errors) as f:
        return json.loads(f.read())


### Responses to login.json

LOGIN_INVALID_PASSWORD = {
    "errorCode": api.API_ERROR_INVALID_CREDENTIALS,
    "dataName": None,
    "data": None,
    "success": False,
}

LOGIN_PASSWORD_WARNING = {
    "data": None,
    "dataName": None,
    "errorCode": api.API_ERROR_PASSWORD_WARNING,
    "success": False,
}

LOGIN_ACCOUNT_LOCKED = {
    "data": None,
    "dataName": None,
    "errorCode": api.API_ERROR_ACCOUNT_LOCKED,
    "success": False,
}

LOGIN_NO_VEHICLES = {
    "data": None,
    "dataName": None,
    "errorCode": api.API_ERROR_NO_VEHICLES,
    "success": False,
}

LOGIN_NO_ACCOUNT = {
    "data": None,
    "dataName": None,
    "errorCode": api.API_ERROR_NO_ACCOUNT,
    "success": False,
}

LOGIN_INVALID_ACCOUNT = {
    "data": None,
    "dataName": None,
    "errorCode": api.API_ERROR_INVALID_ACCOUNT,
    "success": False,
}

LOGIN_TOO_MANY_ATTEMPTS = {
    "data": None,
    "dataName": None,
    "errorCode": api.API_ERROR_TOO_MANY_ATTEMPTS,
    "success": False,
}

LOGIN_NO_SUCCESS_KEY = {"data": None}

LOGIN_ERRORS = [
    LOGIN_TOO_MANY_ATTEMPTS,
    LOGIN_INVALID_ACCOUNT,
    LOGIN_INVALID_PASSWORD,
    LOGIN_PASSWORD_WARNING,
    LOGIN_TOO_MANY_ATTEMPTS,
    LOGIN_ACCOUNT_LOCKED,
    LOGIN_NO_ACCOUNT,
    LOGIN_NO_SUCCESS_KEY,
]

LOGIN_SINGLE_REGISTERED = read_json("login_single_car.json")
LOGIN_MULTI_REGISTERED = read_json("login_multi_car.json")

LOGIN_SINGLE_NOT_REGISTERED = deepcopy(LOGIN_SINGLE_REGISTERED)
LOGIN_SINGLE_NOT_REGISTERED["data"]["deviceRegistered"] = False

LOGIN_MULTI_NOT_REGISTERED = deepcopy(LOGIN_MULTI_REGISTERED)
LOGIN_MULTI_NOT_REGISTERED["data"]["deviceRegistered"] = False


### Responses for selectVehicle.json

# This is a Generation 1 with no active subscription
SELECT_VEHICLE_1 = read_json("selectVehicle_1.json")

# This is a PHEV with Safety/Security Plus
SELECT_VEHICLE_2 = read_json("selectVehicle_2.json")

# This is a Generation 2 with Safety/Security Plus
SELECT_VEHICLE_3 = read_json("selectVehicle_3.json")

# This is a Generation 2 with Safety Plus
SELECT_VEHICLE_4 = read_json("selectVehicle_4.json")

# This is a Generation 1 with a safety/security active subscription
SELECT_VEHICLE_5 = read_json("selectVehicle_5.json")


VALIDATE_SESSION_SUCCESS = {
    "data": None,
    "dataName": None,
    "errorCode": None,
    "success": True,
}

VALIDATE_SESSION_FAIL = {
    "data": None,
    "dataName": None,
    "errorCode": None,
    "success": False,
}

VEHICLE_CONDITION_EV = read_json("condition.json")
VEHICLE_STATUS_EV = read_json("vehicleStatus.json")
VEHICLE_STATUS_EV_MISSING_DATA = read_json("vehicleStatus_missing.json")
VEHICLE_HEALTH_EV = read_json("vehicleHealth.json")

REMOTE_CMD_INVALID_PIN = {
    "data": {
        "errorDescription": "The credentials supplied are invalid, tries left 1",
        "errorLabel": "InvalidCredentials",
    },
    "dataName": "errorResponse",
    "errorCode": "InvalidCredentials",
    "success": False,
}


# /service/g2/locate/execute.json
LOCATE_G2 = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "finished",
        "remoteServiceType": "locate",
        "result": {
            "heading": 170,
            "latitude": 39.83,
            "longitude": -98.585,
            "speed": 0,
            "timestamp": 1640459786000,
        },
        "serviceRequestId": None,
        "subState": None,
        "success": True,
        "updateTime": None,
        "vin": "JF2ABCDE6L0000002",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}

# /service/g2/locate/execute.json
LOCATE_G2_BAD_LOCATION = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "finished",
        "remoteServiceType": "locate",
        "result": {
            "heading": 170,
            "latitude": sc.BAD_LATITUDE,
            "longitude": sc.BAD_LONGITUDE,
            "speed": 0,
            "timestamp": 1640459786000,
        },
        "serviceRequestId": None,
        "subState": None,
        "success": True,
        "updateTime": None,
        "vin": "JF2ABCDE6L0000002",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}

# /service/g2/lightsOnly/execute.json
REMOTE_SERVICE_EXECUTE = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "started",
        "remoteServiceType": "lightsOnly",
        "result": None,
        "serviceRequestId": "JF2ABCDE6L0000002_1595799253112_21_@NGTP",
        "subState": None,
        "success": False,
        "updateTime": None,
        "vin": "JF2ABCDE6L0000002",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}

# /service/g2/remoteService/status.json
REMOTE_SERVICE_STATUS_STARTED = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "started",
        "remoteServiceType": "lightsOnly",
        "result": None,
        "serviceRequestId": "JF2ABCDE6L0000002_1595799253112_21_@NGTP",
        "subState": None,
        "success": False,
        "updateTime": 1595799253000,
        "vin": "JF2ABCDE6L0000002",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}

REMOTE_SERVICE_STATUS_FINISHED_SUCCESS = {
    "data": {
        "cancelled": False,
        "errorCode": "null:null",
        "remoteServiceState": "finished",
        "remoteServiceType": "lightsOnly",
        "result": None,
        "serviceRequestId": "JF2ABCDE6L0000002_1595799253112_21_@NGTP",
        "subState": None,
        "success": True,
        "updateTime": 1595799258000,
        "vin": "JF2ABCDE6L0000002",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}

REMOTE_SERVICE_STATUS_FINISHED_FAIL = {
    "data": {
        "cancelled": False,
        "errorCode": "null:null",
        "remoteServiceState": "finished",
        "remoteServiceType": "lightsOnly",
        "result": None,
        "serviceRequestId": "JF2ABCDE6L0000002_1595799253112_21_@NGTP",
        "subState": None,
        "success": False,
        "updateTime": 1595799258000,
        "vin": "JF2ABCDE6L0000002",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}

REMOTE_SERVICE_STATUS_INVALID_TOKEN = {
    "success": False,
    "errorCode": "InvalidToken",
    "dataName": "errorResponse",
    "data": {"errorLabel": "InvalidToken", "errorDescription": "E003"},
}

VEHICLE_STATUS_EXECUTE = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "started",
        "remoteServiceType": "vehicleStatus",
        "result": None,
        "serviceRequestId": "JF2ABCDE6L0000002_1596597153693_11_@NGTP",
        "subState": None,
        "success": False,
        "updateTime": None,
        "vin": "JF2ABCDE6L0000002",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}

VEHICLE_STATUS_STARTED = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "started",
        "remoteServiceType": "vehicleStatus",
        "result": None,
        "serviceRequestId": "JF2ABCDE6L0000002_1596597153693_11_@NGTP",
        "subState": None,
        "success": False,
        "updateTime": 1596597153000,
        "vin": "JF2ABCDE6L0000002",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}

VEHICLE_STATUS_FINISHED_SUCCESS = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "finished",
        "remoteServiceType": "locate",
        "result": {
            "heading": 170,
            "latitude": 39.83,
            "longitude": -98.585,
            "speed": 0,
            "timestamp": 1596597163000,
        },
        "serviceRequestId": None,
        "subState": None,
        "success": True,
        "updateTime": None,
        "vin": "JF2ABCDE6L0000002",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}

LOCATE_G1_EXECUTE = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": None,
        "remoteServiceType": "locate",
        "result": None,
        "serviceRequestId": "01234457-89ab-cdef-0123-456789abcdef",
        "subState": None,
        "success": False,
        "updateTime": None,
        "vin": "JF2ABCDE6L0000005",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}

LOCATE_G1_STARTED = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "started",
        "remoteServiceType": "locate",
        "result": None,
        "serviceRequestId": "01234457-89ab-cdef-0123-456789abcdef",
        "subState": None,
        "success": False,
        "updateTime": 1607210415000,
        "vin": "JF2ABCDE6L0000005",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}

LOCATE_G1_FINISHED = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "finished",
        "remoteServiceType": "locate",
        "result": {
            "heading": None,
            "latitude": 39.83,
            "longitude": -98.585,
            "locationTimestamp": 1607210423000,
            "speed": None,
        },
        "serviceRequestId": "01234457-89ab-cdef-0123-456789abcdef",
        "subState": None,
        "success": True,
        "updateTime": 1607210425000,
        "vin": "JF2ABCDE6L0000005",
    },
    "dataName": "remoteServiceStatus",
    "errorCode": None,
    "success": True,
}


FETCH_SUBARU_CLIMATE_PRESETS = read_json("climatePresetsSubaru.json")
SUBARU_PRESET_1 = "Full Cool"

FETCH_USER_CLIMATE_PRESETS_EV = read_json("climatePresetsUser.json")
TEST_USER_PRESET_1 = "Test User Preset 1"


UPDATE_USER_CLIMATE_PRESETS = {
    "success": True,
    "errorCode": None,
    "dataName": None,
    "data": None,
}

ERROR_403 = {
    "success": False,
    "errorCode": api.API_ERROR_SOA_403,
    "dataName": "errorResponse",
    "data": {"errorLabel": api.API_ERROR_SOA_403, "errorDescription": None},
}

ERROR_VIN_NOT_FOUND = {
    "data": None,
    "dataName": None,
    "errorCode": api.API_ERROR_VEHICLE_NOT_IN_ACCOUNT,
    "success": False,
}

ERROR_VEHICLE_SETUP = {
    "data": None,
    "dataName": None,
    "errorCode": api.API_ERROR_VEHICLE_SETUP,
    "success": False,
}
