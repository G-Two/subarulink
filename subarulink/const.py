#  SPDX-License-Identifier: Apache-2.0
"""
Constants used with this package.

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""

COUNTRY_USA = "USA"
COUNTRY_CAN = "CAN"

MOBILE_API_SERVER = {
    COUNTRY_USA: "mobileapi.prod.subarucs.com",
    COUNTRY_CAN: "mobileapi.ca.prod.subarucs.com",
}
MOBILE_API_VERSION = "/g2v21"
MOBILE_APP = {
    COUNTRY_USA: "com.subaru.telematics.app.remote",
    COUNTRY_CAN: "ca.subaru.telematics.remote",
}

# Same API for g1 and g2
API_LOGIN = "/login.json"
API_2FA_CONTACT = "/twoStepAuthContacts.json"
API_2FA_SEND_VERIFICATION = "/twoStepAuthSendVerification.json"
API_2FA_AUTH_VERIFY = "/twoStepAuthVerify.json"
API_REFRESH_VEHICLES = "/refreshVehicles.json"
API_SELECT_VEHICLE = "/selectVehicle.json"
API_VALIDATE_SESSION = "/validateSession.json"
API_VEHICLE_STATUS = "/vehicleStatus.json"
API_AUTHORIZE_DEVICE = "/authenticateDevice.json"
API_NAME_DEVICE = "/nameThisDevice.json"

# Similar API for g1 and g2 -- controller should replace 'api_gen' with either 'g1' or 'g2'
API_LOCK = "/service/api_gen/lock/execute.json"
API_LOCK_CANCEL = "/service/api_gen/lock/cancel.json"

API_UNLOCK = "/service/api_gen/unlock/execute.json"
API_UNLOCK_CANCEL = "/service/api_gen/unlock/cancel.json"

API_HORN_LIGHTS = "/service/api_gen/hornLights/execute.json"
API_HORN_LIGHTS_CANCEL = "/service/api_gen/hornLights/cancel.json"
API_HORN_LIGHTS_STOP = "/service/api_gen/hornLights/stop.json"

API_LIGHTS = "/service/api_gen/lightsOnly/execute.json"
API_LIGHTS_CANCEL = "/service/api_gen/lightsOnly/cancel.json"
API_LIGHTS_STOP = "/service/api_gen/lightsOnly/stop.json"

API_CONDITION = "/service/api_gen/condition/execute.json"
API_LOCATE = "/service/api_gen/locate/execute.json"
API_REMOTE_SVC_STATUS = "/service/api_gen/remoteService/status.json"

# Different API for g1 and g2
API_G1_LOCATE_UPDATE = "/service/g1/vehicleLocate/execute.json"
API_G1_LOCATE_STATUS = "/service/g1/vehicleLocate/status.json"
API_G2_LOCATE_UPDATE = "/service/g2/vehicleStatus/execute.json"
API_G2_LOCATE_STATUS = "/service/g2/vehicleStatus/locationStatus.json"

# g1-Only API
API_G1_HORN_LIGHTS_STATUS = "/service/g1/hornLights/status.json"

# g2-Only API
API_G2_SEND_POI = "/service/g2/sendPoi/execute.json"
API_G2_SPEEDFENCE = "/service/g2/speedFence/execute.json"
API_G2_GEOFENCE = "/service/g2/geoFence/execute.json"
API_G2_CURFEW = "/service/g2/curfew/execute.json"

API_G2_REMOTE_ENGINE_START = "/service/g2/engineStart/execute.json"
API_G2_REMOTE_ENGINE_START_CANCEL = "/service/g2/engineStart/cancel.json"
API_G2_REMOTE_ENGINE_STOP = "/service/g2/engineStop/execute.json"

API_G2_FETCH_RES_QUICK_START_SETTINGS = "/service/g2/remoteEngineQuickStartSettings/fetch.json"
API_G2_FETCH_RES_USER_PRESETS = "/service/g2/remoteEngineStartSettings/fetch.json"
API_G2_FETCH_RES_SUBARU_PRESETS = "/service/g2/climatePresetSettings/fetch.json"
API_G2_SAVE_RES_SETTINGS = "/service/g2/remoteEngineStartSettings/save.json"
API_G2_SAVE_RES_QUICK_START_SETTINGS = "/service/g2/remoteEngineQuickStartSettings/save.json"

# EV-Only API
API_EV_CHARGE_NOW = "/service/g2/phevChargeNow/execute.json"
API_EV_FETCH_CHARGE_SETTINGS = "/service/g2/phevGetTimerSettings/execute.json"
API_EV_SAVE_CHARGE_SETTINGS = "/service/g2/phevSendTimerSetting/execute.json"
API_EV_DELETE_CHARGE_SCHEDULE = "/service/g2/phevDeleteTimerSetting/execute.json"

MAX_SESSION_AGE_MINS = 240
SERVICE_REQ_ID = "serviceRequestId"

# Remote start constants
TEMP_F = "climateZoneFrontTemp"
TEMP_F_MAX = 85
TEMP_F_MIN = 60

TEMP_C = "climateZoneFrontTempCelsius"
TEMP_C_MAX = 30
TEMP_C_MIN = 15

RUNTIME = "runTimeMinutes"
RUNTIME_10_MIN = "10"
RUNTIME_5_MIN = "5"

MODE = "climateZoneFrontAirMode"
MODE_DEFROST = "WINDOW"
MODE_FEET_DEFROST = "FEET_WINDOW"
MODE_FACE = "FACE"
MODE_FEET = "FEET"
MODE_SPLIT = "FEET_FACE_BALANCED"
MODE_AUTO = "AUTO"

HEAT_SEAT_LEFT = "heatedSeatFrontLeft"
HEAT_SEAT_RIGHT = "heatedSeatFrontRight"
HEAT_SEAT_HI = "HIGH_HEAT"
HEAT_SEAT_MED = "MEDIUM_HEAT"
HEAT_SEAT_LOW = "LOW_HEAT"
HEAT_SEAT_OFF = "OFF"

REAR_DEFROST = "heatedRearWindowActive"
REAR_DEFROST_ON = "true"
REAR_DEFROST_OFF = "false"

FAN_SPEED = "climateZoneFrontAirVolume"
FAN_SPEED_LOW = "2"
FAN_SPEED_MED = "4"
FAN_SPEED_HI = "7"
FAN_SPEED_AUTO = "AUTO"

RECIRCULATE = "outerAirCirculation"
RECIRCULATE_OFF = "outsideAir"
RECIRCULATE_ON = "recirculation"

REAR_AC = "airConditionOn"
REAR_AC_ON = "true"
REAR_AC_OFF = "false"

PRESET_NAME = "name"
PRESET_INDEX = "index"

CAN_EDIT = "canEdit"
CAN_EDIT_VALUE = "true"
DISABLED = "disabled"
DISABLED_VALUE = "false"
PRESET_TYPE = "presetType"
PRESET_TYPE_USER = "userPreset"
START_CONFIGURATION = "startConfiguration"
START_CONFIGURATION_EV = "START_CLIMATE_CONTROL_ONLY_ALLOW_KEY_IN_IGNITION"
START_CONFIGURATION_RES = "START_ENGINE_ALLOW_KEY_IN_IGNITION"

START_CONFIG_CONSTS_EV = {
    CAN_EDIT: CAN_EDIT_VALUE,
    DISABLED: DISABLED_VALUE,
    PRESET_TYPE: PRESET_TYPE_USER,
    START_CONFIGURATION: START_CONFIGURATION_EV,
}
START_CONFIG_CONSTS_RES = {
    CAN_EDIT: CAN_EDIT_VALUE,
    DISABLED: DISABLED_VALUE,
    PRESET_TYPE: PRESET_TYPE_USER,
    START_CONFIGURATION: START_CONFIGURATION_RES,
}

VALID_CLIMATE_OPTIONS = {
    TEMP_C: [str(_) for _ in range(TEMP_C_MIN, TEMP_C_MAX + 1)],
    TEMP_F: [str(_) for _ in range(TEMP_F_MIN, TEMP_F_MAX + 1)],
    FAN_SPEED: [FAN_SPEED_AUTO, FAN_SPEED_LOW, FAN_SPEED_MED, FAN_SPEED_HI],
    HEAT_SEAT_LEFT: [HEAT_SEAT_OFF, HEAT_SEAT_LOW, HEAT_SEAT_MED, HEAT_SEAT_HI],
    HEAT_SEAT_RIGHT: [HEAT_SEAT_OFF, HEAT_SEAT_LOW, HEAT_SEAT_MED, HEAT_SEAT_HI],
    MODE: [
        MODE_DEFROST,
        MODE_FEET_DEFROST,
        MODE_FACE,
        MODE_FEET,
        MODE_SPLIT,
        MODE_AUTO,
    ],
    RECIRCULATE: [RECIRCULATE_OFF, RECIRCULATE_ON],
    REAR_AC: [REAR_AC_OFF, REAR_AC_ON],
    REAR_DEFROST: [REAR_DEFROST_OFF, REAR_DEFROST_ON],
    RUNTIME: [RUNTIME_10_MIN, RUNTIME_5_MIN],
    PRESET_NAME: [None],
    CAN_EDIT: [CAN_EDIT_VALUE],
    DISABLED: [DISABLED_VALUE],
    PRESET_TYPE: [PRESET_TYPE_USER],
    START_CONFIGURATION: [START_CONFIGURATION_EV, START_CONFIGURATION_RES],
    PRESET_INDEX: [0, 1, 2, 3],
}

# Unlock doors constants
WHICH_DOOR = "unlockDoorType"
ALL_DOORS = "ALL_DOORS_CMD"
DRIVERS_DOOR = "FRONT_LEFT_DOOR_CMD"
TAILGATE_DOOR = "TAILGATE_DOOR_CMD"
VALID_DOORS = [ALL_DOORS, DRIVERS_DOOR, TAILGATE_DOOR]

# Location data constants
HEADING = "heading"
LATITUDE = "latitude"
LONGITUDE = "longitude"
LOCATION_TIME = "locationTimestamp"
SPEED = "speed"
BAD_LATITUDE = 90.0
BAD_LONGITUDE = 180.0

# Vehicle status constants
AVG_FUEL_CONSUMPTION = "AVG_FUEL_CONSUMPTION"
BATTERY_VOLTAGE = "BATTERY_VOLTAGE"
DIST_TO_EMPTY = "DISTANCE_TO_EMPTY_FUEL"
DOOR_BOOT_POSITION = "DOOR_BOOT_POSITION"
DOOR_ENGINE_HOOD_POSITION = "DOOR_ENGINE_HOOD_POSITION"
DOOR_FRONT_LEFT_POSITION = "DOOR_FRONT_LEFT_POSITION"
DOOR_FRONT_RIGHT_POSITION = "DOOR_FRONT_RIGHT_POSITION"
DOOR_REAR_LEFT_POSITION = "DOOR_REAR_LEFT_POSITION"
DOOR_REAR_RIGHT_POSITION = "DOOR_REAR_RIGHT_POSITION"
EV_CHARGER_STATE_TYPE = "EV_CHARGER_STATE_TYPE"
EV_CHARGE_SETTING_AMPERE_TYPE = "EV_CHARGE_SETTING_AMPERE_TYPE"
EV_CHARGE_VOLT_TYPE = "EV_CHARGE_VOLT_TYPE"
EV_DISTANCE_TO_EMPTY = "EV_DISTANCE_TO_EMPTY"
EV_IS_PLUGGED_IN = "EV_IS_PLUGGED_IN"
EV_STATE_OF_CHARGE_MODE = "EV_STATE_OF_CHARGE_MODE"
EV_STATE_OF_CHARGE_PERCENT = "EV_STATE_OF_CHARGE_PERCENT"
EV_TIME_TO_FULLY_CHARGED = "EV_TIME_TO_FULLY_CHARGED"
EV_TIME_TO_FULLY_CHARGED_UTC = "EV_TIME_TO_FULLY_CHARGED_UTC"
EXTERNAL_TEMP = "EXT_EXTERNAL_TEMP"
ODOMETER = "ODOMETER"
LAST_UPDATED_DATE = "LAST_UPDATED_DATE"
POSITION_TIMESTAMP = "POSITION_TIMESTAMP"
TIMESTAMP = "TIMESTAMP"
TIRE_PRESSURE_FL = "TYRE_PRESSURE_FRONT_LEFT"
TIRE_PRESSURE_FR = "TYRE_PRESSURE_FRONT_RIGHT"
TIRE_PRESSURE_RL = "TYRE_PRESSURE_REAR_LEFT"
TIRE_PRESSURE_RR = "TYRE_PRESSURE_REAR_RIGHT"
VEHICLE_STATE = "VEHICLE_STATE_TYPE"
WINDOW_FRONT_LEFT_STATUS = "WINDOW_FRONT_LEFT_STATUS"
WINDOW_FRONT_RIGHT_STATUS = "WINDOW_FRONT_RIGHT_STATUS"
WINDOW_REAR_LEFT_STATUS = "WINDOW_REAR_LEFT_STATUS"
WINDOW_REAR_RIGHT_STATUS = "WINDOW_REAR_RIGHT_STATUS"
WINDOW_SUNROOF_STATUS = "WINDOW_SUNROOF_STATUS"

CHARGING = "CHARGING"
LOCKED_CONNECTED = "LOCKED_CONNECTED"
UNLOCKED_CONNECTED = "UNLOCKED_CONNECTED"
DOOR_OPEN = "OPEN"
DOOR_CLOSED = "CLOSED"
WINDOW_OPEN = "OPEN"
WINDOW_CLOSED = "CLOSE"
IGNITION_ON = "IGNITION_ON"
NOT_EQUIPPED = "NOT_EQUIPPED"


# vehicleStatus.json keys
VS_AVG_FUEL_CONSUMPTION = "avgFuelConsumptionLitersPer100Kilometers"
VS_DIST_TO_EMPTY = "distanceToEmptyFuelKilometers"
VS_TIMESTAMP = "eventDateStr"
VS_LATITUDE = "latitude"
VS_LONGITUDE = "longitude"
VS_HEADING = "positionHeadingDegree"
VS_ODOMETER = "odometerValueKilometers"
VS_VEHICLE_STATE = "vehicleStateType"
VS_TIRE_PRESSURE_FL = "tirePressureFrontLeft"
VS_TIRE_PRESSURE_FR = "tirePressureFrontRight"
VS_TIRE_PRESSURE_RL = "tirePressureRearLeft"
VS_TIRE_PRESSURE_RR = "tirePressureRearRight"


# Erroneous Values
BAD_AVG_FUEL_CONSUMPTION = "16383"
BAD_DISTANCE_TO_EMPTY_FUEL = "16383"
BAD_EV_TIME_TO_FULLY_CHARGED = "65535"
BAD_TIRE_PRESSURE = "32767"
BAD_ODOMETER = None
BAD_EXTERNAL_TEMP = "-64.0"
BAD_SENSOR_VALUES = [
    BAD_AVG_FUEL_CONSUMPTION,
    BAD_DISTANCE_TO_EMPTY_FUEL,
    BAD_EV_TIME_TO_FULLY_CHARGED,
    BAD_TIRE_PRESSURE,
    BAD_ODOMETER,
    BAD_EXTERNAL_TEMP,
]
UNKNOWN = "UNKNOWN"
VENTED = "VENTED"
BAD_BINARY_SENSOR_VALUES = [UNKNOWN, VENTED, NOT_EQUIPPED]
LOCATION_VALID = "location_valid"

# Timestamp Formats
TIMESTAMP_FMT = "%Y-%m-%dT%H:%M:%S%z"  # "2020-04-25T23:35:55+0000"
VS_TIMESTAMP_FMT = "%Y-%m-%dT%H:%M%z"  # "2020-04-25T23:35+0000"
POSITION_TIMESTAMP_FMT = "%Y-%m-%dT%H:%M:%SZ"  # "2020-04-25T23:35:55Z"

# G2 Error Codes
ERROR_SOA_403 = "403-soa-unableToParseResponseBody"
ERROR_INVALID_CREDENTIALS = "InvalidCredentials"
ERROR_SERVICE_ALREADY_STARTED = "ServiceAlreadyStarted"
ERROR_INVALID_ACCOUNT = "invalidAccount"
ERROR_PASSWORD_WARNING = "passwordWarning"
ERROR_ACCOUNT_LOCKED = "accountLocked"
ERROR_NO_VEHICLES = "noVehiclesOnAccount"
ERROR_NO_ACCOUNT = "accountNotFound"
ERROR_TOO_MANY_ATTEMPTS = "tooManyAttempts"
ERROR_VEHICLE_NOT_IN_ACCOUNT = "vehicleNotInAccount"
ERROR_INVALID_TOKEN = "InvalidToken"
ERROR_VEHICLE_SETUP = "VEHICLESETUPERROR"

# G1 Error Codes
ERROR_G1_NO_SUBSCRIPTION = "SXM40004"
ERROR_G1_STOLEN_VEHICLE = "SXM40005"
ERROR_G1_INVALID_PIN = "SXM40006"
ERROR_G1_SERVICE_ALREADY_STARTED = "SXM40009"
ERROR_G1_PIN_LOCKED = "SXM40017"

# Controller Vehicle Data Dict Keys
VEHICLE_ATTRIBUTES = "attributes"
VEHICLE_STATUS = "status"
VEHICLE_ID = "id"
VEHICLE_MODEL_NAME = "modelName"
VEHICLE_MODEL_YEAR = "modelYear"
VEHICLE_NAME = "nickname"
VEHICLE_API_GEN = "api_gen"
VEHICLE_LOCK = "lock"
VEHICLE_LAST_UPDATE = "last_update_time"
VEHICLE_LAST_FETCH = "last_fetch_time"
VEHICLE_FEATURES = "features"
VEHICLE_SUBSCRIPTION_FEATURES = "subscriptionFeatures"
VEHICLE_SUBSCRIPTION_STATUS = "subscriptionStatus"

FEATURE_PHEV = "PHEV"
FEATURE_REMOTE_START = "RES"
FEATURE_G1_TELEMATICS = "g1"
"""Vehicle has 2016-2018 telematics version."""

FEATURE_G2_TELEMATICS = "g2"
"""Vehicle has 2019+ telematics version."""

FEATURE_REMOTE = "REMOTE"
FEATURE_SAFETY = "SAFETY"
FEATURE_ACTIVE = "ACTIVE"

DEFAULT_UPDATE_INTERVAL = 7200
DEFAULT_FETCH_INTERVAL = 300
