# Developers Reference

This document describes the public API of the `subarulink` package. The package exposes a
single `Controller` class that manages an authenticated session to the MySubaru Connected
Services API and can operate on multiple vehicles belonging to one MySubaru account.

> **NOTE:** This is an unofficial, reverse-engineered API. Subaru publishes no public API,
> so behavior may change or break without warning. Use at your own risk.

## Contents
- [Quick Start](#quick-start)
- [Constructor](#constructor)
- [Connection and Authentication](#connection-and-authentication)
- [Vehicle Discovery and Capabilities](#vehicle-discovery-and-capabilities)
- [Vehicle Data](#vehicle-data)
- [Remote Commands](#remote-commands)
- [Climate Presets](#climate-presets)
- [Update and Fetch Intervals](#update-and-fetch-intervals)
- [Exceptions](#exceptions)
- [Constants](#constants)

All network-bound methods are coroutines (`async def`) and must be awaited.

## Quick Start

```python
import asyncio
import aiohttp
import subarulink


async def main():
    async with aiohttp.ClientSession() as session:
        ctrl = subarulink.Controller(
            session,
            "you@example.com",   # username
            "password",
            "1234567890",        # device_id (any stable identifier)
            "1234",              # PIN
            "my-app",            # device_name
            country="USA",
        )
        await ctrl.connect()

        # Complete 2FA the first time a device_id is used
        if not ctrl.device_registered:
            print(ctrl.contact_methods)
            await ctrl.request_auth_code("userName")
            await ctrl.submit_auth_code(input("Enter 2FA code: "))

        for vin in ctrl.get_vehicles():
            print(vin, ctrl.get_api_gen(vin), ctrl.get_model_name(vin))
            data = await ctrl.get_data(vin)


asyncio.run(main())
```

See [`subarulink/app/cli.py`](subarulink/app/cli.py) for a complete standalone example.

## Constructor

```python
Controller(
    websession,
    username,
    password,
    device_id,
    pin,
    device_name,
    country="USA",
    update_interval=7200,
    fetch_interval=300,
)
```

| Argument | Description |
|----------|-------------|
| `websession` | An `aiohttp.ClientSession` instance. |
| `username` | Your MySubaru account username, normally an email address. |
| `password` | Your MySubaru account password. |
| `device_id` | An identifier for the device accessing the Subaru API. The content does not matter, but it **must be used consistently** for a given MySubaru account. Once authorized via 2FA, it appears in your MySubaru profile's authorized-devices list. Using a different `device_id` each login forces re-validation via 2FA and creates duplicate profile entries. |
| `pin` | The 4-digit PIN for your vehicle (required for remote commands). |
| `device_name` | Human-readable name that maps to a `device_id`; shown in your MySubaru profile. |
| `country` | MySubaru registration country. `"USA"` and `"CAN"` are supported (`subarulink.const.COUNTRY_USA` / `COUNTRY_CAN`). |
| `update_interval` | Minimum seconds between remote `update()` requests. Throttles requests to the vehicle, which can drain the 12V battery. |
| `fetch_interval` | Minimum seconds between `fetch()` calls of Subaru's server-cached data. Throttles polling of the Subaru API. |

## Connection and Authentication

`connect()` authenticates to the Subaru servers and performs the initialization needed for
subsequent API calls.

- `connect()` → `bool` — Authenticate and load the account's vehicles. Returns `True` if at least one vehicle is found, otherwise `False`.

The Subaru API uses 2FA (SMS or email) to register devices, including applications using
this package. An unregistered device cannot perform most API calls.

- `device_registered` *(property)* → `bool` — `False` if 2FA is still required for this session; `True` once 2FA has been completed (or was previously made permanent for this `device_id`).
- `contact_methods` *(property)* → `dict[str, str]` — Available 2FA delivery methods, keyed by method name (pass a key to `request_auth_code`).
- `request_auth_code(contact_method)` → `bool` — Request that a 2FA validation code be sent via the given `contact_method` (a key from `contact_methods`). Returns `True` on success; then check your phone/email for the code.
- `submit_auth_code(code)` → `bool` — Submit the 6-digit numeric validation `code`. On success, the device is permanently registered so that 2FA is no longer required for this `device_id`. Returns `True` on success.

PIN handling for remote services:

- `is_pin_required()` → `bool` — `True` if any vehicle on the account has an active remote-service subscription (and therefore needs a PIN).
- `test_pin()` → `bool` — Validate the stored PIN against Subaru remote services. Returns `True` if valid. Raises `InvalidPIN` if rejected.
- `invalid_pin_entered()` → `bool` — `True` if an invalid PIN was previously rejected, locking out further remote commands until the PIN is updated.
- `update_saved_pin(new_pin)` → `bool` — Replace the PIN used by the controller and clear the lockout flag. Returns `True` if the value changed.

## Vehicle Discovery and Capabilities

Most methods take a `vin` argument. An unknown VIN raises `SubaruException`.

- `get_vehicles()` → `list[str]` — VINs available on the account.
- `vin_to_name(vin)` → `str` — The vehicle's nickname.
- `get_model_year(vin)` → `str`
- `get_model_name(vin)` → `str`
- `get_api_gen(vin)` → `str` — Telematics generation: `"g1"`, `"g2"`, `"g3"`, `"g4"`, or `"unknown"`.
- `get_ev_status(vin)` → `bool` — Whether the vehicle is a PHEV/EV.
- `get_remote_status(vin)` → `bool` — Whether remote lock/horn/light service is available (Security/Companion+ plan, active subscription).
- `get_res_status(vin)` → `bool` — Whether remote engine start is available.
- `get_safety_status(vin)` → `bool` — Whether the vehicle has an active Safety/Companion (info) plan.
- `get_subscription_status(vin)` → `bool` — Whether the vehicle has any active service plan.
- `has_tpms(vin)` → `bool` — Whether the vehicle reports tire pressures.
- `has_sunroof(vin)` → `bool` — Whether the vehicle reports sunroof/moonroof status.
- `has_power_windows(vin)` → `bool` *(async)* — Whether the vehicle reports power window status. May fetch data to infer support on some vehicles.
- `has_lock_status(vin)` → `bool` *(async)* — Whether the vehicle reports door lock status. May fetch data to infer support on some vehicles.

## Vehicle Data

g2, g3, and g4 vehicles push status information back to Subaru servers. Retrieve it with:

- `get_data(vin)` → `VehicleInfo` *(async)* — Locally cached, processed vehicle data. Fetches from the API if nothing has been cached yet.
- `get_raw_data(vin)` → `dict` — Locally cached, unprocessed API responses for the VIN.
- `fetch(vin, force=False)` → `bool` *(async)* — Retrieve Subaru's server-cached vehicle data. This does **not** command the vehicle, so the data may be stale — check its timestamp. Throttled by `fetch_interval` unless `force=True`.
- `update(vin, force=False)` → `bool` *(async)* — Send a remote request asking the vehicle to report fresh status. Excessive use may drain the 12V battery. Throttled by `update_interval` unless `force=True`. Raises `VehicleNotSupported` if the vehicle lacks an active remote-service subscription.
- `get_last_fetch_time(vin)` → `datetime`
- `get_last_update_time(vin)` → `datetime`

## Remote Commands

Remote commands generally take about 10 seconds to complete. All are coroutines that block
until complete and return `True` on success.

- `lock(vin)` → `bool` — Lock all doors.
- `unlock(vin, door=ALL_DOORS)` → `bool` — Unlock the specified door. Options are `subarulink.const.ALL_DOORS` (default), `DRIVERS_DOOR`, and `TAILGATE_DOOR` (tailgate is not supported by all models). An invalid value raises `SubaruException`.
- `horn(vin)` → `bool` — Begin sounding the horn.
- `horn_stop(vin)` → `bool` — Stop sounding the horn.
- `lights(vin)` → `bool` — Begin flashing the lights.
- `lights_stop(vin)` → `bool` — Stop flashing the lights.
- `remote_start(vin, preset_name)` → `bool` — Start the engine/EV using climate preset `preset_name` (see [Climate Presets](#climate-presets)).
- `remote_stop(vin)` → `bool` — Stop the engine/EV. Raises `VehicleNotSupported` if remote start is unavailable.
- `charge_start(vin)` → `bool` — Start EV charging (EV only; there is no stop command). Raises `VehicleNotSupported` for non-EV vehicles.

## Climate Presets

Climate presets are used with `remote_start`. Presets created in the official app or website
are automatically available here.

- `list_climate_preset_names(vin)` → `list[str]` *(async)* — Valid climate preset names.
- `get_climate_preset_by_name(vin, preset_name)` → `dict | None` *(async)* — Preset settings for a given name, or `None` if not found.
- `get_user_climate_preset_data(vin)` → `list[dict]` *(async)* — Up to 4 user-defined presets.
- `delete_climate_preset_by_name(vin, preset_name)` → `bool` *(async)* — Delete a user-defined preset by name. Raises `SubaruException` if the named user preset is not found.
- `update_user_climate_presets(vin, preset_data)` → `bool` *(async)* — Overwrite the stored list of user-defined presets (max 4 entries). To append to an existing list, call `get_user_climate_preset_data()`, modify the returned list, then pass it back here.

## Update and Fetch Intervals

- `get_update_interval()` / `get_fetch_interval()` → `int` — Current interval in seconds.
- `set_update_interval(value)` → `bool` — Set the remote-update interval. Accepts values `>= 300`; returns `False` and keeps the old value otherwise.
- `set_fetch_interval(value)` → `bool` — Set the fetch interval. Accepts values `>= 60`; returns `False` and keeps the old value otherwise.

## Exceptions

All exceptions subclass `subarulink.SubaruException` and are importable from `subarulink`:

| Exception | Raised when |
|-----------|-------------|
| `SubaruException` | Base class for all package errors. |
| `InvalidCredentials` | Username/password authentication failed. |
| `IncompleteCredentials` | Required credentials were not provided. |
| `InvalidPIN` | The vehicle PIN was rejected. |
| `PINLockoutProtect` | A remote command was blocked because a previously rejected PIN locked out further attempts. |
| `VehicleNotSupported` | The requested action is not supported by the vehicle's hardware or service plan. |
| `RemoteServiceFailure` | A remote command was accepted but did not complete successfully. |

## Constants

Useful constants live in `subarulink.const`:

| Constant | Value | Used by |
|----------|-------|---------|
| `COUNTRY_USA` / `COUNTRY_CAN` | `"USA"` / `"CAN"` | `Controller(country=...)` |
| `ALL_DOORS` / `DRIVERS_DOOR` / `TAILGATE_DOOR` | door selectors | `unlock(vin, door=...)` |
| `POLL_INTERVAL` | `7200` | default `update_interval` |
| `FETCH_INTERVAL` | `300` | default `fetch_interval` |
