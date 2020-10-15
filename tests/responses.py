""" Test Subaru API Responses. """
from copy import deepcopy

login_invalid_password = {
    "errorCode": "invalidAccount",
    "dataName": None,
    "data": None,
    "success": False,
}

login_password_warning = {
    "data": None,
    "dataName": None,
    "errorCode": "passwordWarning",
    "success": False,
}

login_account_locked = {
    "data": None,
    "dataName": None,
    "errorCode": "accountLocked",
    "success": False,
}

login_no_vehicles = {
    "data": None,
    "dataName": None,
    "errorCode": "noVehiclesOnAccount",
    "success": False,
}

login_no_account = {
    "data": None,
    "dataName": None,
    "errorCode": "accountNotFound",
    "success": False,
}

login_invalid_account = {
    "data": None,
    "dataName": None,
    "errorCode": "invalidAccount",
    "success": False,
}

login_too_many_attempts = {
    "data": None,
    "dataName": None,
    "errorCode": "tooManyAttempts",
    "success": False,
}

remote_cmd_invalid_pin = {
    "data": {
        "errorDescription": "The credentials supplied are invalid, tries left 1",
        "errorLabel": "InvalidCredentials",
    },
    "dataName": "errorResponse",
    "errorCode": "InvalidCredentials",
    "success": False,
}

fake_account = {
    "accountKey": 123456,
    "createdDate": 1451606400000,
    "firstName": "Subarulink",
    "lastLoginDate": 1454284800000,
    "lastName": "Tester",
    "marketId": 1,
    "zipCode": "12345",
    "zipCode5": "12345",
}


### Car Data fields used in refreshVehicles.json and selectVehicle.json
### an item in js_resp["data"]["vehicles"]
# This is a Generation 1 with no active subscription
fake_car_data_1 = {
    "accessLevel": -1,
    "active": True,
    "authorizedVehicle": False,
    "cachedStateCode": "AA",
    "customer": {
        "email": "",
        "firstName": "Subarulink",
        "lastName": "Tester",
        "oemCustId": "1-TESTOEM_1",
        "phone": "",
        "sessionCustomer": {
            "address": "123 " "Fake " "St",
            "address2": "",
            "cellularPhone": "",
            "city": "Anytown",
            "countryCode": "USA",
            "createMysAccount": None,
            "dealerCode": None,
            "email": "fake@email.com",
            "firstName": "Subarulink",
            "gender": "",
            "homePhone": "",
            "lastName": "Tester",
            "oemCustId": "1-TESTOEM_1",
            "phone": "",
            "primaryPersonalCountry": "USA",
            "relationshipType": None,
            "sourceSystemCode": "mys",
            "state": "AA",
            "suffix": "",
            "title": "",
            "vehicles": [
                {
                    "oemCustId": "1-TESTOEM_1",
                    "primary": False,
                    "siebelVehicleRelationship": "Previous " "Owner",
                    "status": "",
                    "vin": "JF2ABCDE6L0000001",
                },
                {
                    "oemCustId": "1-TESTOEM_1",
                    "primary": True,
                    "siebelVehicleRelationship": "TM " "Subscriber",
                    "status": "Inactive",
                    "vin": "JF2ABCDE6L0000001",
                },
                {
                    "oemCustId": "1-TESTOEM_2",
                    "primary": False,
                    "siebelVehicleRelationship": "Owner",
                    "status": "",
                    "vin": "JF2ABCDE6L0000002",
                },
                {
                    "oemCustId": "1-TESTOEM_2",
                    "primary": False,
                    "siebelVehicleRelationship": "TM " "Subscriber",
                    "status": "Active",
                    "vin": "JF2ABCDE6L0000002",
                },
                {
                    "oemCustId": "1-TESTOEM_3",
                    "primary": False,
                    "siebelVehicleRelationship": "Owner",
                    "status": "",
                    "vin": "JF2ABCDE6L0000003",
                },
                {
                    "oemCustId": "1-TESTOEM_3",
                    "primary": False,
                    "siebelVehicleRelationship": "TM " "Subscriber",
                    "status": "Active",
                    "vin": "JF2ABCDE6L0000003",
                },
                {
                    "oemCustId": "1-TESTOEM_4",
                    "primary": False,
                    "siebelVehicleRelationship": "Owner",
                    "status": "",
                    "vin": "JF2ABCDE6L0000004",
                },
                {
                    "oemCustId": "1-TESTOEM_4",
                    "primary": False,
                    "siebelVehicleRelationship": "TM " "Subscriber",
                    "status": "Active",
                    "vin": "JF2ABCDE6L0000004",
                },
            ],
            "workPhone": "5555551234",
            "zip": "12345-1234",
            "zip5Digits": "12345",
        },
        "zip": "12345-1234",
    },
    "email": "fake@email.com",
    "engineSize": None,
    "extDescrip": None,
    "features": ["BSD", "REARBRK", "EYESIGHT", "g1"],
    "firstName": "Subarulink",
    "intDescrip": None,
    "lastName": "Tester",
    "licensePlate": "",
    "licensePlateState": "",
    "mileageCalculated": None,
    "mileageEstimate": None,
    "modelName": None,
    "modelYear": None,
    "needEmergencyContactPrompt": False,
    "needMileagePrompt": True,
    "nickname": "TEST_SUBARU_1",
    "oemCustId": "1-TESTOEM_1",
    "phev": None,
    "phone": "",
    "preferredDealer": None,
    "provisioned": True,
    "remoteServicePinExist": True,
    "stolenVehicle": False,
    "subscriptionFeatures": [],
    "subscriptionPlans": [],
    "subscriptionStatus": None,
    "timeZone": "America/New_York",
    "transCode": None,
    "userOemCustId": "1-TESTOEM_1",
    "vehicleGeoPosition": None,
    "vehicleKey": 1000001,
    "vehicleName": "TEST_SUBARU_1",
    "vin": "JF2ABCDE6L0000001",
    "zip": "12345-1234",
}

# This is a PHEV with Safety/Security Plus
fake_car_data_2 = deepcopy(fake_car_data_1)
fake_car_data_2.update(
    {
        "features": [
            "ABS_MIL",
            "ATF_MIL",
            "AWD_MIL",
            "BSD",
            "BSDRCT_MIL",
            "CEL_MIL",
            "EBD_MIL",
            "EOL_MIL",
            "EPAS_MIL",
            "EPB_MIL",
            "ESS_MIL",
            "EYESIGHT",
            "HEV_MIL",
            "HEVCM_MIL",
            "OPL_MIL",
            "PHEV",
            "RAB_MIL",
            "RCC",
            "REARBRK",
            "RPOIA",
            "SRS_MIL",
            "TEL_MIL",
            "TPMS_MIL",
            "VDC_MIL",
            "WASH_MIL",
            "NAV_TOMTOM",
            "g2",
        ],
        "nickname": "TEST_SUBARU_2",
        "oemCustId": "1-TESTOEM-2",
        "subscriptionFeatures": ["REMOTE", "SAFETY", "RetailPHEV"],
        "subscriptionStatus": "ACTIVE",
        "userOemCustId": "1-TESTOEM_2",
        "vehicleGeoPosition": {
            "heading": None,
            "latitude": 90.0,
            "longitude": 180.0,
            "speed": None,
            "timestamp": 1454284800000,
        },
        "vehicleKey": 1000002,
        "vehicleName": "TEST_SUBARU_2",
        "vin": "JF2ABCDE6L0000002",
    }
)

# This is a Generation 2 with Safety/Security Plus
fake_car_data_3 = deepcopy(fake_car_data_1)
fake_car_data_3.update(
    {
        "features": [
            "ABS_MIL",
            "ATF_MIL",
            "AWD_MIL",
            "BSD",
            "BSDRCT_MIL",
            "CEL_MIL",
            "EBD_MIL",
            "EOL_MIL",
            "EPAS_MIL",
            "EPB_MIL",
            "ESS_MIL",
            "EYESIGHT",
            "HEV_MIL",
            "HEVCM_MIL",
            "OPL_MIL",
            "RAB_MIL",
            "RCC",
            "REARBRK",
            "RES",
            "RPOIA",
            "SRS_MIL",
            "TEL_MIL",
            "TPMS_MIL",
            "VDC_MIL",
            "WASH_MIL",
            "NAV_TOMTOM",
            "g2",
        ],
        "nickname": "TEST_SUBARU_3",
        "oemCustId": "1-TESTOEM-3",
        "subscriptionFeatures": ["REMOTE", "SAFETY"],
        "subscriptionStatus": "ACTIVE",
        "userOemCustId": "1-TESTOEM_3",
        "vehicleGeoPosition": {
            "heading": None,
            "latitude": 90.0,
            "longitude": 180.0,
            "speed": None,
            "timestamp": 1454284800000,
        },
        "vehicleKey": 1000003,
        "vehicleName": "TEST_SUBARU_3",
        "vin": "JF2ABCDE6L0000003",
    }
)

# This is a Generation 2 with Safety Plus
fake_car_data_4 = deepcopy(fake_car_data_1)
fake_car_data_4.update(
    {
        "features": [
            "ABS_MIL",
            "ATF_MIL",
            "AWD_MIL",
            "BSD",
            "BSDRCT_MIL",
            "CEL_MIL",
            "EBD_MIL",
            "EOL_MIL",
            "EPAS_MIL",
            "EPB_MIL",
            "ESS_MIL",
            "EYESIGHT",
            "HEV_MIL",
            "HEVCM_MIL",
            "OPL_MIL",
            "RAB_MIL",
            "RCC",
            "REARBRK",
            "RES",
            "RPOIA",
            "SRS_MIL",
            "TEL_MIL",
            "TPMS_MIL",
            "VDC_MIL",
            "WASH_MIL",
            "NAV_TOMTOM",
            "g2",
        ],
        "nickname": "TEST_SUBARU_4",
        "oemCustId": "1-TESTOEM-4",
        "subscriptionFeatures": ["SAFETY"],
        "subscriptionStatus": "ACTIVE",
        "userOemCustId": "1-TESTOEM_4",
        "vehicleGeoPosition": {
            "heading": None,
            "latitude": 90.0,
            "longitude": 180.0,
            "speed": None,
            "timestamp": 1454284800000,
        },
        "vehicleKey": 1000004,
        "vehicleName": "TEST_SUBARU_4",
        "vin": "JF2ABCDE6L0000004",
    }
)


## for login.json, less information is provided about the vehicles but the structure is the same
login_fake_car_1 = {
    "accessLevel": -1,
    "active": True,
    "authorizedVehicle": False,
    "cachedStateCode": "AA",
    "customer": {
        "email": None,
        "firstName": None,
        "lastName": None,
        "oemCustId": None,
        "phone": None,
        "sessionCustomer": None,
        "zip": None,
    },
    "email": None,
    "engineSize": None,
    "extDescrip": None,
    "features": None,
    "firstName": None,
    "intDescrip": None,
    "lastName": None,
    "licensePlate": "",
    "licensePlateState": "",
    "mileageCalculated": None,
    "mileageEstimate": None,
    "modelName": None,
    "modelYear": None,
    "needEmergencyContactPrompt": False,
    "needMileagePrompt": False,
    "nickname": "TEST_SUBARU_1",
    "oemCustId": "1-TESTOEM_1",
    "phev": None,
    "phone": None,
    "preferredDealer": None,
    "provisioned": True,
    "remoteServicePinExist": True,
    "stolenVehicle": False,
    "subscriptionFeatures": None,
    "subscriptionPlans": [],
    "subscriptionStatus": None,
    "timeZone": "America/New_York",
    "transCode": None,
    "userOemCustId": "1-TESTOEM_1",
    "vehicleGeoPosition": None,
    "vehicleKey": 1000001,
    "vehicleName": "TEST_SUBARU_1",
    "vin": "JF2ABCDE6L0000001",
    "zip": None,
}

login_fake_car_2 = deepcopy(login_fake_car_1)
login_fake_car_2.update(
    {
        "nickname": "TEST_SUBARU_2",
        "oemCustId": "1-TESTOEM_2",
        "userOemCustId": "1-TESTOEM_2",
        "vehicleKey": "1000002",
        "vehicleName": "TEST_SUBARU_2",
        "vin": "JF2ABCDE6L0000002",
    }
)

login_fake_car_3 = deepcopy(login_fake_car_1)
login_fake_car_3.update(
    {
        "nickname": "TEST_SUBARU_3",
        "oemCustId": "1-TESTOEM_3",
        "userOemCustId": "1-TESTOEM_3",
        "vehicleKey": "1000003",
        "vehicleName": "TEST_SUBARU_3",
        "vin": "JF2ABCDE6L0000003",
    }
)

login_fake_car_4 = deepcopy(login_fake_car_1)
login_fake_car_4.update(
    {
        "nickname": "TEST_SUBARU_4",
        "oemCustId": "1-TESTOEM_4",
        "userOemCustId": "1-TESTOEM_4",
        "vehicleKey": "1000004",
        "vehicleName": "TEST_SUBARU_4",
        "vin": "JF2ABCDE6L0000004",
    }
)

login_single_registered = {
    "data": {
        "account": fake_account,
        "currentVehicleIndex": 0,
        "deviceId": "1234567890",
        "deviceRegistered": True,
        "digitalGlobeConnectId": "00000000-0000-0000-0000-000000000000",
        "digitalGlobeImageTileService": "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@png/{z}/{x}/{y}.png?connectId=00000000-0000-0000-0000-000000000000",
        "digitalGlobeTransparentTileService": "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/Digitalglobe:OSMTransparentTMSTileService@EPSG:3857@png/{z}/{x}/{-y}.png/?connectId=00000000-0000-0000-0000-000000000000",
        "enableXtime": True,
        "handoffToken": "test",
        "passwordToken": None,
        "resetPassword": False,
        "satelliteViewEnabled": False,
        "sessionChanged": False,
        "sessionId": "0123456789ABCDEF01234567890ABCDE",
        "termsAndConditionsAccepted": True,
        "tomtomKey": "0123456789ABCDEF01234567890ABCDE",
        "vehicleInactivated": False,
        "vehicles": [login_fake_car_1],
    },
    "dataName": "sessionData",
    "errorCode": None,
    "success": True,
}

login_single_not_registered = deepcopy(login_single_registered)
login_single_not_registered["data"]["deviceRegistered"] = False

login_multi_registered = {
    "data": {
        "account": fake_account,
        "currentVehicleIndex": 0,
        "deviceId": "1234567890",
        "deviceRegistered": True,
        "digitalGlobeConnectId": "00000000-0000-0000-0000-000000000000",
        "digitalGlobeImageTileService": "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@png/{z}/{x}/{y}.png?connectId=00000000-0000-0000-0000-000000000000",
        "digitalGlobeTransparentTileService": "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/Digitalglobe:OSMTransparentTMSTileService@EPSG:3857@png/{z}/{x}/{-y}.png/?connectId=00000000-0000-0000-0000-000000000000",
        "enableXtime": True,
        "handoffToken": "test",
        "passwordToken": None,
        "resetPassword": False,
        "satelliteViewEnabled": False,
        "sessionChanged": False,
        "sessionId": "0123456789ABCDEF01234567890ABCDE",
        "termsAndConditionsAccepted": True,
        "tomtomKey": "0123456789ABCDEF01234567890ABCDE",
        "vehicleInactivated": False,
        "vehicles": [
            login_fake_car_1,
            login_fake_car_2,
            login_fake_car_3,
            login_fake_car_4,
        ],
    },
    "dataName": "sessionData",
    "errorCode": None,
    "success": True,
}

login_multi_not_registered = deepcopy(login_multi_registered)
login_multi_not_registered["data"]["deviceRegistered"] = False

refreshVehicles_single = {
    "data": {
        "account": fake_account,
        "currentVehicleIndex": 0,
        "deviceId": "1234567890",
        "deviceRegistered": True,
        "digitalGlobeConnectId": "00000000-0000-0000-0000-000000000000",
        "digitalGlobeImageTileService": "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@png/{z}/{x}/{y}.png?connectId=00000000-0000-0000-0000-000000000000",
        "digitalGlobeTransparentTileService": "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/Digitalglobe:OSMTransparentTMSTileService@EPSG:3857@png/{z}/{x}/{-y}.png/?connectId=00000000-0000-0000-0000-000000000000",
        "enableXtime": True,
        "handoffToken": "test",
        "passwordToken": None,
        "resetPassword": False,
        "satelliteViewEnabled": False,
        "sessionChanged": False,
        "sessionId": "0123456789ABCDEF01234567890ABCDE",
        "termsAndConditionsAccepted": True,
        "tomtomKey": "0123456789ABCDEF01234567890ABCDE",
        "vehicleInactivated": False,
        "vehicles": [fake_car_data_1],
    },
    "dataName": "sessionData",
    "errorCode": None,
    "success": True,
}

# vehicle data fetched by refreshVehicles is incomplete for multicar accounts
refreshVehicles_car_2 = deepcopy(fake_car_data_2)
refreshVehicles_car_2.update(
    {
        "features": None,
        "subscriptionFeatures": None,
    }
)
refreshVehicles_car_2.pop("vehicleGeoPosition")

refreshVehicles_car_3 = deepcopy(fake_car_data_3)
refreshVehicles_car_3.update(
    {
        "features": None,
        "subscriptionFeatures": None,
    }
)
refreshVehicles_car_3.pop("vehicleGeoPosition")

refreshVehicles_car_4 = deepcopy(fake_car_data_4)
refreshVehicles_car_4.update(
    {
        "features": None,
        "subscriptionFeatures": None,
    }
)
refreshVehicles_car_4.pop("vehicleGeoPosition")


refreshVehicles_multi = {
    "data": {
        "account": fake_account,
        "currentVehicleIndex": 0,
        "deviceId": "1234567890",
        "deviceRegistered": True,
        "digitalGlobeConnectId": "00000000-0000-0000-0000-000000000000",
        "digitalGlobeImageTileService": "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/DigitalGlobe:ImageryTileService@EPSG:3857@png/{z}/{x}/{y}.png?connectId=00000000-0000-0000-0000-000000000000",
        "digitalGlobeTransparentTileService": "https://earthwatch.digitalglobe.com/earthservice/tmsaccess/tms/1.0.0/Digitalglobe:OSMTransparentTMSTileService@EPSG:3857@png/{z}/{x}/{-y}.png/?connectId=00000000-0000-0000-0000-000000000000",
        "enableXtime": True,
        "handoffToken": "test",
        "passwordToken": None,
        "resetPassword": False,
        "satelliteViewEnabled": False,
        "sessionChanged": False,
        "sessionId": "0123456789ABCDEF01234567890ABCDE",
        "termsAndConditionsAccepted": True,
        "tomtomKey": "0123456789ABCDEF01234567890ABCDE",
        "vehicleInactivated": False,
        "vehicles": [
            fake_car_data_1,
            refreshVehicles_car_2,
            refreshVehicles_car_3,
            refreshVehicles_car_4,
        ],
    },
    "dataName": "sessionData",
    "errorCode": None,
    "success": True,
}


selectVehicle_1 = {
    "data": fake_car_data_1,
    "dataName": "vehicle",
    "errorCode": None,
    "success": True,
}

selectVehicle_2 = {
    "data": fake_car_data_2,
    "dataName": "vehicle",
    "errorCode": None,
    "success": True,
}

selectVehicle_3 = {
    "data": fake_car_data_3,
    "dataName": "vehicle",
    "errorCode": None,
    "success": True,
}

selectVehicle_4 = {
    "data": fake_car_data_4,
    "dataName": "vehicle",
    "errorCode": None,
    "success": True,
}


validateSession_true = {
    "data": None,
    "dataName": None,
    "errorCode": None,
    "success": True,
}

validateSession_false = {
    "data": None,
    "dataName": None,
    "errorCode": None,
    "success": False,
}

condition_EV = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "finished",
        "remoteServiceType": "condition",
        "result": {
            "lastUpdatedTime": "2020-07-23T23:35:03+0000",
            "odometer": 1000000,
            "vehicleStatus": [
                {"key": "TRANSMISSION_MODE", "value": "UNKNOWN"},
                {"key": "TYRE_PRESSURE_REAR_RIGHT", "value": "32767"},
                {"key": "SEAT_BELT_STATUS_THIRD_MIDDLE", "value": "UNKNOWN"},
                {"key": "SEAT_OCCUPATION_STATUS_FRONT_RIGHT", "value": "UNKNOWN"},
                {"key": "SEAT_BELT_STATUS_FRONT_MIDDLE", "value": "NOT_EQUIPPED"},
                {"key": "DOOR_FRONT_LEFT_LOCK_STATUS", "value": "UNKNOWN"},
                {"key": "EXT_EXTERNAL_TEMP", "value": "21.5"},
                {"key": "WINDOW_BACK_STATUS", "value": "UNKNOWN"},
                {"key": "WINDOW_REAR_LEFT_STATUS", "value": "UNKNOWN"},
                {"key": "EV_IS_PLUGGED_IN", "value": "UNLOCKED_CONNECTED"},
                {"key": "EV_VEHICLE_TIME_DAYOFWEEK", "value": "6"},
                {"key": "SEAT_BELT_STATUS_SECOND_MIDDLE", "value": "UNKNOWN"},
                {"key": "SEAT_OCCUPATION_STATUS_THIRD_RIGHT", "value": "UNKNOWN"},
                {"key": "DOOR_FRONT_LEFT_POSITION", "value": "CLOSED"},
                {"key": "TYRE_PRESSURE_FRONT_RIGHT", "value": "32767"},
                {"key": "SEAT_BELT_STATUS_THIRD_RIGHT", "value": "UNKNOWN"},
                {"key": "EV_CHARGE_SETTING_AMPERE_TYPE", "value": "MAXIMUM"},
                {"key": "EV_CHARGER_STATE_TYPE", "value": "CHARGING_STOPPED"},
                {"key": "DOOR_REAR_RIGHT_POSITION", "value": "CLOSED"},
                {"key": "DISTANCE_TO_EMPTY_FUEL", "value": "16383"},
                {"key": "SEAT_BELT_STATUS_FRONT_LEFT", "value": "BELTED"},
                {"key": "EV_STATE_OF_CHARGE_PERCENT", "value": "100"},
                {"key": "SEAT_OCCUPATION_STATUS_FRONT_MIDDLE", "value": "NOT_EQUIPPED"},
                {"key": "TYRE_STATUS_REAR_LEFT", "value": "UNKNOWN"},
                {"key": "EV_VEHICLE_TIME_MINUTE", "value": "20"},
                {"key": "DOOR_BOOT_POSITION", "value": "CLOSED"},
                {"key": "AVG_FUEL_CONSUMPTION", "value": "16383"},
                {"key": "TYRE_PRESSURE_FRONT_LEFT", "value": "32767"},
                {"key": "DOOR_REAR_RIGHT_LOCK_STATUS", "value": "UNKNOWN"},
                {"key": "SEAT_BELT_STATUS_SECOND_RIGHT", "value": "UNKNOWN"},
                {"key": "POSITION_SPEED_KMPH", "value": "0"},
                {"key": "DOOR_FRONT_RIGHT_POSITION", "value": "CLOSED"},
                {"key": "SEAT_OCCUPATION_STATUS_FRONT_LEFT", "value": "UNKNOWN"},
                {"key": "DOOR_REAR_LEFT_LOCK_STATUS", "value": "UNKNOWN"},
                {"key": "SEAT_OCCUPATION_STATUS_SECOND_MIDDLE", "value": "UNKNOWN"},
                {"key": "POSITION_TIMESTAMP", "value": "2020-01-01T00:00:00Z"},
                {"key": "DOOR_ENGINE_HOOD_POSITION", "value": "CLOSED"},
                {"key": "BATTERY_VOLTAGE", "value": "12.0"},
                {"key": "EV_VEHICLE_TIME_SECOND", "value": "39"},
                {"key": "TYRE_PRESSURE_REAR_LEFT", "value": "32767"},
                {"key": "SEAT_BELT_STATUS_SECOND_LEFT", "value": "UNKNOWN"},
                {"key": "WINDOW_REAR_RIGHT_STATUS", "value": "UNKNOWN"},
                {"key": "WINDOW_FRONT_RIGHT_STATUS", "value": "VENTED"},
                {"key": "TYRE_STATUS_FRONT_LEFT", "value": "UNKNOWN"},
                {"key": "EV_VEHICLE_TIME_HOUR", "value": "14"},
                {"key": "SEAT_OCCUPATION_STATUS_SECOND_LEFT", "value": "UNKNOWN"},
                {"key": "SEAT_OCCUPATION_STATUS_SECOND_RIGHT", "value": "UNKNOWN"},
                {"key": "SEAT_OCCUPATION_STATUS_THIRD_LEFT", "value": "UNKNOWN"},
                {"key": "SEAT_BELT_STATUS_THIRD_LEFT", "value": "UNKNOWN"},
                {"key": "EV_STATE_OF_CHARGE_MODE", "value": "EV_MODE"},
                {"key": "ODOMETER", "value": "1000000"},
                {"key": "POSITION_HEADING_DEGREE", "value": "150"},
                {"key": "EV_CHARGE_VOLT_TYPE", "value": "CHARGE_LEVEL_1"},
                {"key": "WINDOW_FRONT_LEFT_STATUS", "value": "VENTED"},
                {"key": "SEAT_OCCUPATION_STATUS_THIRD_MIDDLE", "value": "UNKNOWN"},
                {"key": "EV_TIME_TO_FULLY_CHARGED", "value": "65535"},
                {"key": "DOOR_REAR_LEFT_POSITION", "value": "CLOSED"},
                {"key": "DOOR_ENGINE_HOOD_LOCK_STATUS", "value": "UNKNOWN"},
                {"key": "VEHICLE_STATE_TYPE", "value": "IGNITION_OFF"},
                {"key": "WINDOW_SUNROOF_STATUS", "value": "UNKNOWN"},
                {"key": "EV_DISTANCE_TO_EMPTY", "value": "17"},
                {"key": "TYRE_STATUS_FRONT_RIGHT", "value": "UNKNOWN"},
                {"key": "SEAT_BELT_STATUS_FRONT_RIGHT", "value": "BELTED"},
                {"key": "TYRE_STATUS_REAR_RIGHT", "value": "UNKNOWN"},
                {"key": "DOOR_BOOT_LOCK_STATUS", "value": "UNKNOWN"},
                {"key": "DOOR_FRONT_RIGHT_LOCK_STATUS", "value": "UNKNOWN"},
            ],
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

condition_G2 = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "finished",
        "remoteServiceType": "condition",
        "result": {
            "lastUpdatedTime": "2020-07-23T23:35:03+0000",
            "odometer": 1000000,
            "vehicleStatus": [
                {"key": "TRANSMISSION_MODE", "value": "UNKNOWN"},
                {"key": "TYRE_PRESSURE_REAR_RIGHT", "value": "32767"},
                {"key": "SEAT_BELT_STATUS_THIRD_MIDDLE", "value": "UNKNOWN"},
                {"key": "SEAT_OCCUPATION_STATUS_FRONT_RIGHT", "value": "UNKNOWN"},
                {"key": "SEAT_BELT_STATUS_FRONT_MIDDLE", "value": "NOT_EQUIPPED"},
                {"key": "DOOR_FRONT_LEFT_LOCK_STATUS", "value": "UNKNOWN"},
                {"key": "EXT_EXTERNAL_TEMP", "value": "21.5"},
                {"key": "WINDOW_BACK_STATUS", "value": "UNKNOWN"},
                {"key": "WINDOW_REAR_LEFT_STATUS", "value": "UNKNOWN"},
                {"key": "SEAT_BELT_STATUS_SECOND_MIDDLE", "value": "UNKNOWN"},
                {"key": "SEAT_OCCUPATION_STATUS_THIRD_RIGHT", "value": "UNKNOWN"},
                {"key": "DOOR_FRONT_LEFT_POSITION", "value": "CLOSED"},
                {"key": "TYRE_PRESSURE_FRONT_RIGHT", "value": "32767"},
                {"key": "SEAT_BELT_STATUS_THIRD_RIGHT", "value": "UNKNOWN"},
                {"key": "DOOR_REAR_RIGHT_POSITION", "value": "CLOSED"},
                {"key": "DISTANCE_TO_EMPTY_FUEL", "value": "16383"},
                {"key": "SEAT_BELT_STATUS_FRONT_LEFT", "value": "BELTED"},
                {"key": "SEAT_OCCUPATION_STATUS_FRONT_MIDDLE", "value": "NOT_EQUIPPED"},
                {"key": "TYRE_STATUS_REAR_LEFT", "value": "UNKNOWN"},
                {"key": "DOOR_BOOT_POSITION", "value": "CLOSED"},
                {"key": "AVG_FUEL_CONSUMPTION", "value": "16383"},
                {"key": "TYRE_PRESSURE_FRONT_LEFT", "value": "32767"},
                {"key": "DOOR_REAR_RIGHT_LOCK_STATUS", "value": "UNKNOWN"},
                {"key": "SEAT_BELT_STATUS_SECOND_RIGHT", "value": "UNKNOWN"},
                {"key": "POSITION_SPEED_KMPH", "value": "0"},
                {"key": "DOOR_FRONT_RIGHT_POSITION", "value": "CLOSED"},
                {"key": "SEAT_OCCUPATION_STATUS_FRONT_LEFT", "value": "UNKNOWN"},
                {"key": "DOOR_REAR_LEFT_LOCK_STATUS", "value": "UNKNOWN"},
                {"key": "SEAT_OCCUPATION_STATUS_SECOND_MIDDLE", "value": "UNKNOWN"},
                {"key": "POSITION_TIMESTAMP", "value": "2020-01-01T00:00:00Z"},
                {"key": "DOOR_ENGINE_HOOD_POSITION", "value": "CLOSED"},
                {"key": "BATTERY_VOLTAGE", "value": "12.0"},
                {"key": "TYRE_PRESSURE_REAR_LEFT", "value": "32767"},
                {"key": "SEAT_BELT_STATUS_SECOND_LEFT", "value": "UNKNOWN"},
                {"key": "WINDOW_REAR_RIGHT_STATUS", "value": "UNKNOWN"},
                {"key": "WINDOW_FRONT_RIGHT_STATUS", "value": "VENTED"},
                {"key": "TYRE_STATUS_FRONT_LEFT", "value": "UNKNOWN"},
                {"key": "SEAT_OCCUPATION_STATUS_SECOND_LEFT", "value": "UNKNOWN"},
                {"key": "SEAT_OCCUPATION_STATUS_SECOND_RIGHT", "value": "UNKNOWN"},
                {"key": "SEAT_OCCUPATION_STATUS_THIRD_LEFT", "value": "UNKNOWN"},
                {"key": "SEAT_BELT_STATUS_THIRD_LEFT", "value": "UNKNOWN"},
                {"key": "ODOMETER", "value": "1000000"},
                {"key": "POSITION_HEADING_DEGREE", "value": "150"},
                {"key": "WINDOW_FRONT_LEFT_STATUS", "value": "VENTED"},
                {"key": "SEAT_OCCUPATION_STATUS_THIRD_MIDDLE", "value": "UNKNOWN"},
                {"key": "DOOR_REAR_LEFT_POSITION", "value": "CLOSED"},
                {"key": "DOOR_ENGINE_HOOD_LOCK_STATUS", "value": "UNKNOWN"},
                {"key": "VEHICLE_STATE_TYPE", "value": "IGNITION_OFF"},
                {"key": "WINDOW_SUNROOF_STATUS", "value": "UNKNOWN"},
                {"key": "TYRE_STATUS_FRONT_RIGHT", "value": "UNKNOWN"},
                {"key": "SEAT_BELT_STATUS_FRONT_RIGHT", "value": "BELTED"},
                {"key": "TYRE_STATUS_REAR_RIGHT", "value": "UNKNOWN"},
                {"key": "DOOR_BOOT_LOCK_STATUS", "value": "UNKNOWN"},
                {"key": "DOOR_FRONT_RIGHT_LOCK_STATUS", "value": "UNKNOWN"},
            ],
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

vehicleStatus_EV = {
    "data": {
        "avgFuelConsumptionLitersPer100Kilometers": 2.3,
        "avgFuelConsumptionMpg": 102.2,
        "distanceToEmptyFuelKilometers": 707,
        "distanceToEmptyFuelKilometers10s": 710,
        "distanceToEmptyFuelMiles": 439.31,
        "distanceToEmptyFuelMiles10s": 440,
        "evDistanceToEmptyByStateKilometers": None,
        "evDistanceToEmptyByStateMiles": None,
        "evDistanceToEmptyKilometers": 707,
        "evDistanceToEmptyMiles": 439.31,
        "evStateOfChargePercent": 22,
        "eventDate": 1595547303000,
        "eventDateStr": "2020-07-23T23:35+0000",
        "latitude": 90.0,
        "longitude": 180.0,
        "odometerValue": 3694,
        "odometerValueKilometers": 5944,
        "positionHeadingDegree": None,
        "tirePressureFrontLeft": "2550",
        "tirePressureFrontLeftPsi": "36.98",
        "tirePressureFrontRight": "2550",
        "tirePressureFrontRightPsi": "36.98",
        "tirePressureRearLeft": "2450",
        "tirePressureRearLeftPsi": "35.53",
        "tirePressureRearRight": "2350",
        "tirePressureRearRightPsi": "34.08",
        "vehicleStateType": "IGNITION_OFF",
        "vhsId": 1722793258,
    },
    "dataName": None,
    "errorCode": None,
    "success": True,
}

vehicleStatus_G2 = {
    "data": {
        "avgFuelConsumptionLitersPer100Kilometers": 2.3,
        "avgFuelConsumptionMpg": 102.2,
        "distanceToEmptyFuelKilometers": 707,
        "distanceToEmptyFuelKilometers10s": 710,
        "distanceToEmptyFuelMiles": 439.31,
        "distanceToEmptyFuelMiles10s": 440,
        "eventDate": 1595547303000,
        "eventDateStr": "2020-07-23T23:35+0000",
        "latitude": 45.234,
        "longitude": -77.0,
        "odometerValue": 3694,
        "odometerValueKilometers": 5944,
        "positionHeadingDegree": 170,
        "tirePressureFrontLeft": "2550",
        "tirePressureFrontLeftPsi": "36.98",
        "tirePressureFrontRight": "2550",
        "tirePressureFrontRightPsi": "36.98",
        "tirePressureRearLeft": "2450",
        "tirePressureRearLeftPsi": "35.53",
        "tirePressureRearRight": "2350",
        "tirePressureRearRightPsi": "34.08",
        "vehicleStateType": "IGNITION_OFF",
        "vhsId": 1722793258,
    },
    "dataName": None,
    "errorCode": None,
    "success": True,
}

vehicleStatus_G2_no_tire_pressure = {
    "data": {
        "avgFuelConsumptionLitersPer100Kilometers": 2.3,
        "avgFuelConsumptionMpg": 102.2,
        "distanceToEmptyFuelKilometers": 707,
        "distanceToEmptyFuelKilometers10s": 710,
        "distanceToEmptyFuelMiles": 439.31,
        "distanceToEmptyFuelMiles10s": 440,
        "eventDate": 1595547303000,
        "eventDateStr": "2020-07-23T23:35+0000",
        "latitude": 45.234,
        "longitude": -77.0,
        "odometerValue": 3694,
        "odometerValueKilometers": 5944,
        "positionHeadingDegree": 170,
        "tirePressureFrontLeft": None,
        "tirePressureFrontLeftPsi": None,
        "tirePressureFrontRight": None,
        "tirePressureFrontRightPsi": None,
        "tirePressureRearLeft": None,
        "tirePressureRearLeftPsi": None,
        "tirePressureRearRight": None,
        "tirePressureRearRightPsi": None,
        "vehicleStateType": "IGNITION_OFF",
        "vhsId": 1722793258,
    },
    "dataName": None,
    "errorCode": None,
    "success": True,
}

# https://mobileapi.prod.subarucs.com/g2v15/service/g2/locate/execute.json
locate_G2 = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "finished",
        "remoteServiceType": "locate",
        "result": {
            "heading": 170,
            "latitude": 45.234,
            "longitude": -77.0,
            "speed": 0,
            "timestamp": 1595547303000,
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

# https://mobileapi.prod.subarucs.com/g2v15/service/g2/lightsOnly/execute.json
remoteService_execute = {
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

# https://mobileapi.prod.subarucs.com/g2v15/service/g2/remoteService/status.json
remoteService_status_started = {
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

remoteService_status_finished_success = {
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

remoteService_status_finished_failed = {
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

vehicleStatus_finished_started = {
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

vehicleStatus_finished_success = {
    "data": {
        "cancelled": False,
        "errorCode": None,
        "remoteServiceState": "finished",
        "remoteServiceType": "locate",
        "result": {
            "heading": 170,
            "latitude": 45.234,
            "longitude": -77.0,
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

get_climate_settings_G2 = {
    "success": True,
    "errorCode": None,
    "dataName": None,
    "data": '{"climateZoneFrontTemp": "71", "climateZoneFrontAirMode": "AUTO", "climateZoneFrontAirVolume": "AUTO", "heatedSeatFrontLeft": "OFF", "heatedSeatFrontRight": "OFF", "heatedRearWindowActive": "false", "outerAirCirculation": "recirculation", "airConditionOn": "true",  "runTimeMinutes": "10", "climateSettings": "climateSettings", "startConfiguration": "START_ENGINE_ALLOW_KEY_IN_IGNITION"}',
}

get_climate_settings_EV = {
    "success": True,
    "errorCode": None,
    "dataName": None,
    "data": '{"climateZoneFrontTemp": "71", "climateZoneFrontAirMode": "AUTO", "climateZoneFrontAirVolume": "AUTO", "heatedSeatFrontLeft": "OFF", "heatedSeatFrontRight": "OFF", "heatedRearWindowActive": "false", "outerAirCirculation": "outsideAir", "airConditionOn": "false", "runTimeMinutes": "10", "climateSettings": "climateSettings", "startConfiguration": "start_Climate_Control_only_allow_key_in_ignition"}',
}

error_403 = {
    "success": False,
    "errorCode": "403-soa-unableToParseResponseBody",
    "dataName": "errorResponse",
    "data": {
        "errorLabel": "403-soa-unableToParseResponseBody",
        "errorDescription": None,
    },
}
