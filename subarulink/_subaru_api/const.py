#  SPDX-License-Identifier: Apache-2.0
"""
Constants used by subarulink to interact with the STARLINK HTTP API.

This is an undocumented API derived from analysis of the MySubaru Android app v2.7.39.
"""

API_VERSION = "/g2v27"

API_SERVER = {
    "USA": "mobileapi.prod.subarucs.com",
    "CAN": "mobileapi.ca.prod.subarucs.com",
}

API_MOBILE_APP = {
    "USA": "com.subaru.telematics.app.remote",
    "CAN": "ca.subaru.telematics.remote",
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
API_VEHICLE_HEALTH = "/vehicleHealth.json"

# Similar API for g1 and g2 -- controller must replace 'api_gen' with either 'g1' or 'g2'
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


# vehicleStatus.json fields
API_AVG_FUEL_CONSUMPTION = "avgFuelConsumptionLitersPer100Kilometers"
API_DIST_TO_EMPTY = "distanceToEmptyFuelKilometers"
API_TIMESTAMP = "eventDateStr"
API_LATITUDE = "latitude"
API_LONGITUDE = "longitude"
API_HEADING = "positionHeadingDegree"
API_ODOMETER = "odometerValueKilometers"
API_VEHICLE_STATE = "vehicleStateType"
API_TIRE_PRESSURE_FL = "tirePressureFrontLeft"
API_TIRE_PRESSURE_FR = "tirePressureFrontRight"
API_TIRE_PRESSURE_RL = "tirePressureRearLeft"
API_TIRE_PRESSURE_RR = "tirePressureRearRight"

# vehicleHealth.json fields
API_HEALTH_TROUBLE = "isTrouble"
API_HEALTH_ONDATES = "onDates"
API_HEALTH_FEATURE = "featureCode"

# condition/execute.json fields
API_DOOR_BOOT_POSITION = "doorBootPosition"
API_DOOR_ENGINE_HOOD_POSITION = "doorEngineHoodPosition"
API_DOOR_FRONT_LEFT_POSITION = "doorFrontLeftPosition"
API_DOOR_FRONT_RIGHT_POSITION = "doorFrontRightPosition"
API_DOOR_REAR_LEFT_POSITION = "doorRearLeftPosition"
API_DOOR_REAR_RIGHT_POSITION = "doorRearRightPosition"
API_EV_CHARGER_STATE_TYPE = "evChargerStateType"
API_EV_DISTANCE_TO_EMPTY = "evDistanceToEmpty"
API_EV_IS_PLUGGED_IN = "evIsPluggedIn"
API_EV_STATE_OF_CHARGE_MODE = "evStateOfChargeMode"
API_EV_STATE_OF_CHARGE_PERCENT = "evStateOfChargePercent"
API_EV_TIME_TO_FULLY_CHARGED = "evTimeToFullyCharged"
API_EV_TIME_TO_FULLY_CHARGED_UTC = "evTimeToFullyChargedUTC"
API_REMAINING_FUEL_PERCENT = "remainingFuelPercent"
API_LAST_UPDATED_DATE = "lastUpdatedTime"
API_WINDOW_FRONT_LEFT_STATUS = "windowFrontLeftStatus"
API_WINDOW_FRONT_RIGHT_STATUS = "windowFrontRightStatus"
API_WINDOW_REAR_LEFT_STATUS = "windowRearLeftStatus"
API_WINDOW_REAR_RIGHT_STATUS = "windowRearRightStatus"
API_WINDOW_SUNROOF_STATUS = "windowSunroofStatus"

# Timestamp formats
API_TIMESTAMP_FMT = "%Y-%m-%dT%H:%M:%S%z"  # "2020-04-25T23:35:55+0000"
API_VS_TIMESTAMP_FMT = "%Y-%m-%dT%H:%M%z"  # "2020-04-25T23:35+0000"
API_POSITION_TIMESTAMP_FMT = "%Y-%m-%dT%H:%M:%SZ"  # "2020-04-25T23:35:55Z"

# selectVehicle.json keys
API_VEHICLE_ATTRIBUTES = "attributes"
API_VEHICLE_ID = "id"
API_VEHICLE_MODEL_NAME = "modelName"
API_VEHICLE_MODEL_YEAR = "modelYear"
API_VEHICLE_NAME = "nickname"
API_VEHICLE_API_GEN = "api_gen"
API_VEHICLE_FEATURES = "features"
API_VEHICLE_SUBSCRIPTION_FEATURES = "subscriptionFeatures"
API_VEHICLE_SUBSCRIPTION_STATUS = "subscriptionStatus"

# API_VEHICLE_FEATURES items that determine available functionality
API_FEATURE_PHEV = "PHEV"
API_FEATURE_REMOTE_START = "RES"
API_FEATURE_REMOTE = "REMOTE"
API_FEATURE_SAFETY = "SAFETY"
API_FEATURE_ACTIVE = "ACTIVE"
API_FEATURE_PHEV = "PHEV"
API_FEATURE_REMOTE_START = "RES"
API_FEATURE_MOONROOF_PANORAMIC = "PANPM-DG2G"
API_FEATURE_MOONROOF_POWER = "PANPM-TUIRWAOC"
API_FEATURE_POWER_WINDOWS = "PWAAADWWAP"
API_FEATURE_FRONT_TIRE_RECOMMENDED_PRESSURE_PREFIX = "TIF_"
API_FEATURE_REAR_TIRE_RECOMMENDED_PRESSURE_PREFIX = "TIR_"
API_FEATURE_G1_TELEMATICS = "g1"
API_FEATURE_G2_TELEMATICS = "g2"
API_FEATURE_G3_TELEMATICS = "g3"

# G2 Error Codes
API_ERROR_SOA_403 = "403-soa-unableToParseResponseBody"
API_ERROR_INVALID_CREDENTIALS = "InvalidCredentials"
API_ERROR_SERVICE_ALREADY_STARTED = "ServiceAlreadyStarted"
API_ERROR_INVALID_ACCOUNT = "invalidAccount"
API_ERROR_PASSWORD_WARNING = "passwordWarning"
API_ERROR_ACCOUNT_LOCKED = "accountLocked"
API_ERROR_NO_VEHICLES = "noVehiclesOnAccount"
API_ERROR_NO_ACCOUNT = "accountNotFound"
API_ERROR_TOO_MANY_ATTEMPTS = "tooManyAttempts"
API_ERROR_VEHICLE_NOT_IN_ACCOUNT = "vehicleNotInAccount"
API_ERROR_INVALID_TOKEN = "InvalidToken"
API_ERROR_VEHICLE_SETUP = "VEHICLESETUPERROR"

# G1 Error Codes
API_ERROR_G1_NO_SUBSCRIPTION = "SXM40004"
API_ERROR_G1_STOLEN_VEHICLE = "SXM40005"
API_ERROR_G1_INVALID_PIN = "SXM40006"
API_ERROR_G1_SERVICE_ALREADY_STARTED = "SXM40009"
API_ERROR_G1_PIN_LOCKED = "SXM40017"


API_MAX_SESSION_AGE_MINS = 240
API_SERVICE_REQ_ID = "serviceRequestId"
