"""Tests for subarulink CLI."""
import asyncio
import sys
from unittest.mock import patch

import pytest

import subarulink._subaru_api.const as api
import subarulink.app.cli as cli

from tests.api_responses import (
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
    add_ev_vehicle_condition,
    add_ev_vehicle_status,
    add_fetch_climate_presets,
    add_g2_vehicle_locate,
    add_multi_vehicle_login_sequence,
    add_select_vehicle_sequence,
    add_validate_session,
    add_vehicle_health,
    server_js_response,
)


@pytest.fixture
async def cli_controller(controller):
    instance = cli.CLI("tests/cli_test.cfg")
    instance.ctrl = controller
    instance.session = controller._connection._websession
    with patch("subarulink.app.cli.CLI._init_controller", return_value=None):
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
        await add_ev_vehicle_condition(test_server)

        await add_validate_session(test_server)
        await add_g2_vehicle_locate(test_server)

        await add_validate_session(test_server)
        await add_vehicle_health(test_server)

        await add_fetch_climate_presets(test_server)

        yield task


def test_no_args():
    testargs = ["subarulink"]
    with patch.object(sys, "argv", testargs), patch("argparse.ArgumentParser.print_help") as mock_print_help:
        cli.main()
    assert mock_print_help.call_count == 1


def test_read_config():
    instance = cli.CLI("tests/cli_test.cfg")
    assert instance.config["country"] == TEST_COUNTRY
    assert instance.config["username"] == TEST_USERNAME
    assert instance.config["password"] == TEST_PASSWORD
    assert instance.config["pin"] == TEST_PIN
    assert instance.config["device_id"] == int(TEST_DEVICE_ID)


async def test_single_cmds(test_server, cli_controller):
    cmd_list = [
        {
            "command": "horn",
            "path": api.API_HORN_LIGHTS,
        },
        {
            "command": "lights",
            "path": api.API_LIGHTS,
        },
        {
            "command": "lock",
            "path": api.API_LOCK,
        },
        {
            "command": "unlock",
            "path": api.API_UNLOCK,
        },
        {
            "command": "charge",
            "path": api.API_EV_CHARGE_NOW,
        },
        {
            "command": "remote_stop",
            "path": api.API_G2_REMOTE_ENGINE_STOP,
        },
    ]
    cli_test = cli.CLI("tests/cli_test.cfg")
    for cmd in cmd_list:
        await run_single_cmd(test_server, cli_controller, cmd["command"], cmd["path"], cli_test.config)


async def run_single_cmd(test_server, cli_controller, cmd, path, config):
    task = asyncio.create_task(cli_controller.single_command(cmd, TEST_VIN_2_EV, config))

    await add_multi_vehicle_login_sequence(test_server)
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
    await add_validate_session(test_server)

    await server_js_response(
        test_server,
        REMOTE_SERVICE_EXECUTE,
        path=path,
    )
    await server_js_response(test_server, REMOTE_SERVICE_STATUS_STARTED, path=api.API_REMOTE_SVC_STATUS)
    await server_js_response(
        test_server,
        REMOTE_SERVICE_STATUS_FINISHED_SUCCESS,
        path=api.API_REMOTE_SVC_STATUS,
    )

    with patch("sys.exit") as mock_exit:
        await task
    mock_exit.assert_called_once_with(0)


async def test_interactive_quit(interactive_session):
    with patch("builtins.input", return_value="quit"):
        await interactive_session


# TODO: More tests
