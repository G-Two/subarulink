"""Tests for subarulink CLI."""
import asyncio
import os
import sys
from unittest.mock import patch

import pytest

import subarulink.app.cli as cli
import subarulink.const as sc

from tests.api_responses import (
    CONDITION_EV,
    LOCATE_G2,
    REMOTE_SERVICE_EXECUTE,
    REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
    REMOTE_SERVICE_STATUS_STARTED,
)
from tests.conftest import (
    TEST_COUNTRY,
    TEST_DEVICE_ID,
    TEST_PASSWORD,
    TEST_PIN,
    TEST_USERNAME,
    TEST_VIN_2_EV,
    add_ev_vehicle_status,
    add_multi_vehicle_login_sequence,
    add_select_vehicle_sequence,
    add_validate_session,
    server_js_response,
)


@pytest.fixture
async def cli_controller(controller):
    instance = cli.CLI("tests/cli_test.cfg")
    with patch("subarulink.app.cli.CLI._init_controller", return_value=None), patch.object(
        instance, "_ctrl", controller
    ), patch.object(instance, "_session", controller._connection._websession):
        yield instance


@pytest.fixture
async def interactive_session(test_server, cli_controller):
    input_values = ["2"]

    with patch("builtins.input", return_value=input_values.pop()):
        task = asyncio.create_task(cli_controller.run())
        await add_multi_vehicle_login_sequence(test_server)

        await add_validate_session(test_server)
        await add_select_vehicle_sequence(test_server, 2)

        await add_ev_vehicle_status(test_server)

        await add_validate_session(test_server)
        await server_js_response(test_server, CONDITION_EV, path=sc.API_CONDITION)

        await add_validate_session(test_server)
        await server_js_response(test_server, LOCATE_G2, path=sc.API_LOCATE)

        yield task


def test_no_args():
    testargs = ["subarulink"]
    with patch.object(sys, "argv", testargs), patch("argparse.ArgumentParser.print_help") as mock_print_help:
        cli.main()
    assert mock_print_help.call_count == 1


def test_read_config():
    instance = cli.CLI("tests/cli_test.cfg")
    assert instance._config["country"] == TEST_COUNTRY
    assert instance._config["username"] == TEST_USERNAME
    assert instance._config["password"] == TEST_PASSWORD
    assert instance._config["pin"] == TEST_PIN
    assert instance._config["device_id"] == int(TEST_DEVICE_ID)


# def test_input_new_config():
#     input_values = [TEST_COUNTRY, TEST_USERNAME, TEST_PASSWORD, TEST_PIN, "Y"]
#     input_values.reverse()

#     with patch("builtins.input", return_value=input_values.pop()
#     ), patch("stdiomask.getpass", return_value=input_values.pop()):
#         instance = cli.CLI("subarulink_test.cfg")

#     os.remove("subarulink_test.cfg")


@pytest.mark.asyncio
async def test_single_cmds(test_server, cli_controller):
    cmd_list = [
        {
            "command": "horn",
            "path": sc.API_HORN_LIGHTS,
        },
        {
            "command": "lights",
            "path": sc.API_LIGHTS,
        },
        {
            "command": "lock",
            "path": sc.API_LOCK,
        },
        {
            "command": "unlock",
            "path": sc.API_UNLOCK,
        },
        {
            "command": "charge",
            "path": sc.API_EV_CHARGE_NOW,
        },
        {
            "command": "remote_stop",
            "path": sc.API_G2_REMOTE_ENGINE_STOP,
        },
    ]
    for cmd in cmd_list:
        await run_single_cmd(test_server, cli_controller, cmd["command"], cmd["path"])


async def run_single_cmd(test_server, cli_controller, cmd, path):
    task = asyncio.create_task(cli_controller.single_command(cmd, vin=TEST_VIN_2_EV))

    await add_multi_vehicle_login_sequence(test_server)
    await add_validate_session(test_server)
    await add_select_vehicle_sequence(test_server, 2)
    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=path,
    )
    await server_js_response(test_server, REMOTE_SERVICE_STATUS_STARTED, path=sc.API_REMOTE_SVC_STATUS)
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
        path=sc.API_REMOTE_SVC_STATUS,
    )

    with patch("sys.exit") as mock_exit:
        await task
    mock_exit.assert_called_once_with(0)


# @pytest.mark.asyncio
# async def test_interactive_quit(test_server, cli_controller):
#     input_values = ["2", "quit"]#"show summary", "show all", "quit"]
#     input_values.reverse()

#     with patch("builtins.input", return_value=input_values.pop()
#         ), patch("shlex.split", return_value=(input_values.pop(),)):
#         task = asyncio.create_task(cli_controller.run())
#         await add_multi_vehicle_login_sequence(test_server)

#         await add_validate_session(test_server)
#         await add_select_vehicle_sequence(test_server, 2)

#         await add_ev_vehicle_status(test_server)

#         await add_validate_session(test_server)
#         await server_js_response(test_server, CONDITION_EV, path=sc.API_CONDITION)

#         await add_validate_session(test_server)
#         await server_js_response(test_server, LOCATE_G2, path=sc.API_LOCATE)

#         await task

# @pytest.mark.asyncio
# async def test_interactive_show_summary(interactive_session):
#     input_values = [ "show all", "quit"]
#     input_values.reverse()
#     with patch("builtins.input", return_value=input_values.pop()):
#         await interactive_session


@pytest.mark.asyncio
async def test_interactive_quit(interactive_session):
    with patch("builtins.input", return_value="quit"):
        await interactive_session


# TODO: More tests
