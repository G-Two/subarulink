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
    if path:
        assert request.path == path
    if query:
        assert query.get("vin") == request.query.get("vin")
    js_resp = json.dumps(response)
    server.send_response(request, text=js_resp, content_type='application/json', status=status)
      

async def setup_multi_session(server, http_redirect):
    """ 

    Helper function to setup an authenticated session. Use in a test case to obtain
    a controller object that is logged into a multi-vehicle account.  The vehicle 
    context is vehicle #4.

    """
    http_redirect.add_server('mobileapi.prod.subarucs.com', 443, server.port)
    controller = subarulink.Controller(
        http_redirect.session,
        TEST_USERNAME,
        TEST_PASSWORD,
        TEST_DEVICE_ID,
        TEST_PIN,
        TEST_DEVICE_NAME,
    )
    task = asyncio.create_task(controller.connect())

    await server_js_response(server, login_multi_registered, path='/g2v15/login.json')
    await server_js_response(server, refreshVehicles_multi, path='/g2v15/refreshVehicles.json', query={"_":str(int(time.time()))})
    await server_js_response(server, selectVehicle_1, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_1_G1, "_":str(int(time.time()))})
    await server_js_response(server, selectVehicle_2, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_2_EV, "_":str(int(time.time()))})
    await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
    await server_js_response(server, selectVehicle_4, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_4_SAFETY_PLUS, "_":str(int(time.time()))})
    assert await task
    return controller

async def setup_single_session(server, http_redirect):
    """ 

    Helper function to setup an authenticated session. Use in a test case to obtain
    a controller object that is logged into a single-vehicle account.  

    """
    http_redirect.add_server('mobileapi.prod.subarucs.com', 443, server.port)
    controller = subarulink.Controller(
        http_redirect.session,
        TEST_USERNAME,
        TEST_PASSWORD,
        TEST_DEVICE_ID,
        TEST_PIN,
        TEST_DEVICE_NAME,
    )
    task = asyncio.create_task(controller.connect())

    await server_js_response(server, login_single_registered, path='/g2v15/login.json')
    await server_js_response(server, refreshVehicles_single, path='/g2v15/refreshVehicles.json', query={"_":str(int(time.time()))})
    assert await task
    return controller

@pytest.mark.asyncio
async def test_connect_incomplete_credentials(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server('mobileapi.prod.subarucs.com', 443, server.port)
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
async def test_connect_fail_authenticate(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server('mobileapi.prod.subarucs.com', 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session,
            TEST_USERNAME,
            TEST_PASSWORD,
            TEST_DEVICE_ID,
            TEST_PIN,
            TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        await server_js_response(server, login_invalid_password, path='/g2v15/login.json')
        with pytest.raises(subarulink.SubaruException):
            await task

@pytest.mark.asyncio
async def test_connect_device_registration(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            http_redirect.add_server('mobileapi.prod.subarucs.com', 443, server.port)
            http_redirect.add_server('www.mysubaru.com', 443, server.port)
            controller = subarulink.Controller(
                http_redirect.session,
                TEST_USERNAME,
                TEST_PASSWORD,
                TEST_DEVICE_ID,
                TEST_PIN,
                TEST_DEVICE_NAME,
            )
            task = asyncio.create_task(controller.connect())

            await server_js_response(server, login_single_not_registered, path='/g2v15/login.json')
            await server_js_response(server, refreshVehicles_single, path='/g2v15/refreshVehicles.json', query={"_":str(int(time.time()))})
            await server_js_response(server, True, path='/login')
            await server_js_response(server, True, path='/profile/updateDeviceEntry.json')     
            await server_js_response(server, True, path='/profile/addDeviceName.json')
            await server_js_response(server, login_single_not_registered, path='/g2v15/login.json')
            await server_js_response(server, login_single_not_registered, path='/g2v15/login.json')
            await server_js_response(server, login_single_registered, path='/g2v15/login.json')

            response = await task
            assert response 

@pytest.mark.asyncio
async def test_connect_single_car(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server('mobileapi.prod.subarucs.com', 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session,
            TEST_USERNAME,
            TEST_PASSWORD,
            TEST_DEVICE_ID,
            TEST_PIN,
            TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        await server_js_response(server, login_single_registered, path='/g2v15/login.json')
        await server_js_response(server, refreshVehicles_single, path='/g2v15/refreshVehicles.json', query={"_":str(int(time.time()))})

        response = await task
        assert response == True
        assert controller.get_vehicles() == [TEST_VIN_1_G1]
        assert controller.get_ev_status(TEST_VIN_1_G1) == False


@pytest.mark.asyncio
async def test_connect_multi_car(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        http_redirect.add_server('mobileapi.prod.subarucs.com', 443, server.port)
        controller = subarulink.Controller(
            http_redirect.session,
            TEST_USERNAME,
            TEST_PASSWORD,
            TEST_DEVICE_ID,
            TEST_PIN,
            TEST_DEVICE_NAME,
        )
        task = asyncio.create_task(controller.connect())

        await server_js_response(server, login_multi_registered, path='/g2v15/login.json')
        await server_js_response(server, refreshVehicles_multi, path='/g2v15/refreshVehicles.json', query={"_":str(int(time.time()))})
        await server_js_response(server, selectVehicle_1, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_1_G1, "_":str(int(time.time()))})
        await server_js_response(server, selectVehicle_2, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_2_EV, "_":str(int(time.time()))})
        await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
        await server_js_response(server, selectVehicle_4, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_4_SAFETY_PLUS, "_":str(int(time.time()))})

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
async def test_get_vehicle_status_ev_security_plus(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)
        
        task = asyncio.create_task(controller.get_data(TEST_VIN_2_EV.lower()))
        await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
        await server_js_response(server, selectVehicle_2, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_2_EV, "_":str(int(time.time()))})
        await server_js_response(server, vehicleStatus_EV, path='/g2v15/vehicleStatus.json')
        await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
        await server_js_response(server, condition_EV, path='/g2v15/service/g2/condition/execute.json')
        await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
        await server_js_response(server, locate_G2, path='/g2v15/service/g2/locate/execute.json')
        status = (await task)["status"]
        assert_vehicle_status(status, vehicleStatus_G2)

@pytest.mark.asyncio
async def test_get_vehicle_status_g2_security_plus(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)
        
        task = asyncio.create_task(controller.get_data(TEST_VIN_3_G2))
        await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
        await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
        await server_js_response(server, vehicleStatus_G2, path='/g2v15/vehicleStatus.json')
        await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
        await server_js_response(server, condition_G2, path='/g2v15/service/g2/condition/execute.json')
        await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
        await server_js_response(server, locate_G2, path='/g2v15/service/g2/locate/execute.json')
        status = (await task)["status"]
        assert_vehicle_status(status, vehicleStatus_G2)

@pytest.mark.asyncio
async def test_get_vehicle_status_safety_plus(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)
        
        task = asyncio.create_task(controller.get_data(TEST_VIN_4_SAFETY_PLUS))
        await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
        await server_js_response(server, vehicleStatus_G2, path='/g2v15/vehicleStatus.json')
        status = (await task)["status"]
        assert_vehicle_status(status, vehicleStatus_G2)

@pytest.mark.asyncio
async def test_get_vehicle_status_no_tire_pressure(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)
        
        task = asyncio.create_task(controller.get_data(TEST_VIN_4_SAFETY_PLUS))
        await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
        await server_js_response(server, vehicleStatus_G2_no_tire_pressure, path='/g2v15/vehicleStatus.json')
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
async def test_lights_success(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)
            
            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))
            await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
            await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
            await server_js_response(server, remoteService_execute, path='/g2v15/service/g2/lightsOnly/execute.json')
            await server_js_response(server, remoteService_status_started, path='/g2v15/service/g2/remoteService/status.json')
            await server_js_response(server, remoteService_status_finished_success, path='/g2v15/service/g2/remoteService/status.json')
            assert await task

@pytest.mark.asyncio
async def test_vehicle_remote_cmd_invalid_pin(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))

            assert not controller.invalid_pin_entered()
            await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
            await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
            await server_js_response(server, remote_cmd_invalid_pin, path='/g2v15/service/g2/lightsOnly/execute.json')
            with pytest.raises(subarulink.InvalidPIN):
                assert not await task
                assert controller.invalid_pin_entered()

@pytest.mark.asyncio
async def test_vehicle_remote_cmd_invalid_pin_twice(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))

            assert not controller.invalid_pin_entered()
            await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
            await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
            await server_js_response(server, remote_cmd_invalid_pin, path='/g2v15/service/g2/lightsOnly/execute.json')
            with pytest.raises(subarulink.InvalidPIN):
                assert not await task
                assert controller.invalid_pin_entered()
            
            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))
            with pytest.raises(subarulink.PINLockoutProtect):
                await task

@pytest.mark.asyncio
async def test_lights_failure(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))

            await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
            await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
            await server_js_response(server, remoteService_execute, path='/g2v15/service/g2/lightsOnly/execute.json')
            await server_js_response(server, remoteService_status_started, path='/g2v15/service/g2/remoteService/status.json')
            await server_js_response(server, remoteService_status_finished_failed, path='/g2v15/service/g2/remoteService/status.json')
            assert not await task

@pytest.mark.asyncio
async def test_lights_timeout(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_3_G2))

            await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
            await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
            await server_js_response(server, remoteService_execute, path='/g2v15/service/g2/lightsOnly/execute.json')
            for i in range(0, 20):
                await server_js_response(server, remoteService_status_started, path='/g2v15/service/g2/remoteService/status.json')
            
            assert not await task

@pytest.mark.asyncio
async def test_get_climate_settings(http_redirect, ssl_certificate):
    async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
        controller = await setup_multi_session(server, http_redirect)
        
        task = asyncio.create_task(controller.get_climate_settings(TEST_VIN_3_G2))
        await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
        await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
        await server_js_response(server, get_climate_settings_G2, path='/g2v15/service/g2/remoteEngineStart/fetch.json')
        assert await task

@pytest.mark.asyncio
async def test_remote_start_no_args(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)
            
            task = asyncio.create_task(controller.remote_start(TEST_VIN_3_G2))
            await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
            await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
            await server_js_response(server, get_climate_settings_G2, path='/g2v15/service/g2/remoteEngineStart/fetch.json')
            await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
            await server_js_response(server, remoteService_execute, path='/g2v15/service/g2/engineStart/execute.json')
            await server_js_response(server, remoteService_status_started, path='/g2v15/service/g2/remoteService/status.json')
            await server_js_response(server, remoteService_status_finished_success, path='/g2v15/service/g2/remoteService/status.json')
                    
            assert await task

@pytest.mark.asyncio
async def test_remote_start_bad_args(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)            
            task = asyncio.create_task(controller.remote_start(TEST_VIN_3_G2, {"Bad":"Params"}))     
            with pytest.raises(subarulink.SubaruException):
                await task  

@pytest.mark.asyncio
async def test_remote_cmd_unsupported(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)          
            task = asyncio.create_task(controller.lights(TEST_VIN_4_SAFETY_PLUS))
            with pytest.raises(subarulink.SubaruException):
                await task  

@pytest.mark.asyncio
async def test_switch_vehicle(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.lights(TEST_VIN_2_EV))

            await server_js_response(server, validateSession_true, path='/g2v15/validateSession.json')
            await server_js_response(server, selectVehicle_2, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_2_EV, "_":str(int(time.time()))})
            await server_js_response(server, remoteService_execute, path='/g2v15/service/g2/lightsOnly/execute.json')
            await server_js_response(server, remoteService_status_started, path='/g2v15/service/g2/remoteService/status.json')
            await server_js_response(server, remoteService_status_finished_success, path='/g2v15/service/g2/remoteService/status.json')
            
            assert await task

@pytest.mark.asyncio
async def test_expired_session(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.horn(TEST_VIN_3_G2))

            await server_js_response(server, validateSession_false, path='/g2v15/validateSession.json')
            await server_js_response(server, login_multi_registered, path='/g2v15/login.json')
            await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
            await server_js_response(server, remoteService_execute, path='/g2v15/service/g2/hornLights/execute.json')
            await server_js_response(server, remoteService_status_started, path='/g2v15/service/g2/remoteService/status.json')
            await server_js_response(server, remoteService_status_finished_success, path='/g2v15/service/g2/remoteService/status.json')
    
            assert await task

@pytest.mark.asyncio
async def test_403_during_remote_req(http_redirect, ssl_certificate):
    with patch('asyncio.sleep', new=CoroutineMock()):
        async with CaseControlledTestServer(ssl=ssl_certificate.server_context()) as server:
            controller = await setup_multi_session(server, http_redirect)

            task = asyncio.create_task(controller.horn(TEST_VIN_3_G2))

            await server_js_response(server, validateSession_false, path='/g2v15/validateSession.json')
            await server_js_response(server, login_multi_registered, path='/g2v15/login.json')
            await server_js_response(server, selectVehicle_3, path='/g2v15/selectVehicle.json', query={"vin": TEST_VIN_3_G2, "_":str(int(time.time()))})
            await server_js_response(server, remoteService_execute, path='/g2v15/service/g2/hornLights/execute.json')
            await server_js_response(server, error_403, path='/g2v15/service/g2/remoteService/status.json', status=403)
            await server_js_response(server, remoteService_status_finished_success, path='/g2v15/service/g2/remoteService/status.json')
    
            assert await task

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
