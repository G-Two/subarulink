# Developers Reference

## Package API Reference
The `subarulink` package provides a `Controller` class that manages a connection to an authenticated Subaru API session and may control access to multiple vehicles on a single MySubaru account:
- `Controller(websession, username, password, device_id, pin, device_name, country="USA", update_interval=7200, fetch_interval=300)`
    - `websession` - `aiohttp.ClientSession` instance
    - `username` - Your MySubaru account username, normally an email address
    - `password` - Your MySubaru account password
    - `device_id` - An identifier string for the device accessing the Subaru API.  The web browser interface uses the integer value (as a string) of the timestamp when the user first logged in.  The Android app uses some sort of hexadecimal string.  It doesn't seem to matter what the content of this string is.  The important thing is to consistently use the same one for a given MySubaru account when using this package.  Once a device is authorized via 2-Factor Authentication, it will appear as one of your authorized devices in your MySubaru profile.  If you do not use the same `device_id` over time, you will need to revalidate via 2FA each time you login, and additional entries will appear in your MySubaru profile each time you login.
    - `pin` - The 4-digit PIN number your vehicle.
    - `device_name` - A human readable string that maps to a particular `device_id`.  This is the string that is shown in your MySubaru profile list of authorized devices.
    - `country` - Country used for MySubaru registration.  Currently `"USA"` and `"CAN"` are supported.
    - `update_interval` - Number of seconds between updates.  Used to prevent excessive remote update requests to the vehicle which can drain the battery.
    - `fetch_interval` -  Number of seconds between fetches of Subaru's cached vehicle information. Used to prevent excessive polling of Subaru API.  

The connect method will authenticate to Subaru servers and perform the necessary initialization and API queries to be ready for subsequent API calls.
- `Controller.connect()` - Returns `True` upon success.

The Subaru API uses 2FA (via SMS or email) to register devices, including applications using this package. If a device is not registered, it will not be allowed to perform most API calls.
- `Controller.device_registered` - If this property is `False`, 2FA needs to be performed. If `True` then 2FA has been completed for this session and/or 2FA was completed with the `make_permanent` option set.

To perform 2FA, a validation code must be requested with:
- `Controller.request_auth_code(contact_method)` - Where `contact_method` is a string from the `Controller.auth_contact_methods` list. This function returns `True` if successful. After calling this function check your mobile phone or email for the validation code.

To submit received validation code, use:
- `Controller.submit_auth_code(code, make_permanent=True)` - Where `code` is a 6-digit numeric validation code, and `make_permanent` is a boolean to permanently register the device (identified by `Controller.device_id`) with Subaru so that 2FA is no longer required for this device.

A list of vehicles on your MySubaru account may be obtained with:
- `Controller.get_vehicles()` - Returns a list of VIN strings.  

Use the VIN as a mandatory argument when interacting with the controller.   Determine your vehicle telematics version with:
- `Controller.get_api_gen(vin)` - Returns `"g1"` or `"g2"`

Remote commands generally take about 10 seconds to complete, and can be invoked with the following methods:
- `Controller.lock(vin)` - Locks all doors
- `Controller.unlock(vin, door=ALL_DOORS)` - Unlocks specified door (default is `ALL_DOORS`). Other options include `DRIVERS_DOOR` and `TAILGATE_DOOR` (tailgate is not supported by all models)
- `Controller.horn(vin)` - Begin sounding horn
- `Controller.horn_stop(vin)` - Stop sounding horn
- `Controller.lights(vin)` - Begin flashing lights
- `Controller.lights_stop(vin)` - Stop flashing lights
- `Controller.remote_start(vin, preset_name)` - Start the engine/EV with climate control `preset_name`. A list of valid presets can be obtained with `Controller.list_climate_preset_names(vin)`.
- `Controller.remote_stop(vin)` - Stop the engine/EV
- `Controller.charge_start(vin)` - EV Only (there is no stop command)

All of the above functions are async and block until complete, returning `True` if successful.


Climate control presets may be managed with the following methods:
- `Controller.list_climate_preset_names(vin)` - Returns a list of valid remote climate control names
- `Controller.get_climate_preset_by_name(vin, preset_name)` - Returns a dict of the preset information about a specific climate control preset
- `Controller.get_user_climate_preset_data(vin)` - Returns a list of up to 4 dicts of user defined climate control presets
- `Controller.delete_climate_preset_by_name(vin, preset_name)` - Deletes a user defined climate control preset by name
- `Controller.update_user_climate_presets(vin, new_preset_data)` - Updates the list of user defined climate control presets. This overwrites the list stored by Subaru. If you would like to add a new preset to an existing list of 3 presets, you would need to call `get_user_climate_preset_data()`, append a new entry, and then submit the modified list as `new_preset_data`. The max length of `new_preset_data` is 4 entries. 


`g2` vehicles push status information back to Subaru servers. This data may be retrieved with the following methods:
- `Controller.get_data(vin)` - Returns locally cached data about vehicle, if available.  Fetches data if not received yet.
- `Controller.fetch(vin)` - Uses Subaru API to fetch Subaru's cached vehicle data.  This does not request a command to be sent to the vehicle.  This data may be stale, so check the timestamp and request an update if necessary.  The Crosstrek PHEV has been observed to automatically push vehicle updates after certain state changes (power off, charging cable inserted).
- `Controller.update(vin)` - Uses Subaru API to send a remote update request to the vehicle. Excessive use may drain vehicle battery.  Throttled with update_interval. 

See [`subarulink/app/cli.py`](subarulink/app/cli.py) for an example of how to use the `subarulink` package in a standalone application.
