# Developers Reference

## Core

The `subarulink` package provides a `Controller` class that manages a connection to an authenticated Subaru API session and may control access to multiple vehicles on a single MySubaru account.  Use your MySubaru credentials with the connect method:
- `Controller.connect(websession, username, password, device_id, pin, device_name, [update_interval], [fetch_interval])`
    - `websession` - `aiohttp.ClientSession` instance
    - `username` - Your MySubaru account username, normally an email address
    - `password` - Your MySubaru account password
    - `device_id` - An identifier string for the device accessing the Subaru API.  The web browser interface uses the integer value (as a string) of the timestamp when the user first logged in.  The Android app uses some sort of hexadecimal string.  It doesn't seem to matter what the content of this string is.  The important thing is to consistently use the same one for a given MySubaru account when using this package.  Once a device is "authorized" to perform remote commands, it will appear as one of your authorized devices in your MySubaru profile.  If you do not use the same `device_id` over time, additional entries will appear in your MySubaru profile each time you login. 
    - `device_name` - A human readable string that maps to a particular `device_id`.  This is the string that is shown in your MySubaru profile list of authorized devices.
    - `update_interval` - Number of seconds between updates.  Used to prevent excessive remote update requests to the vehicle which can drain the battery.
    - `fetch_interval` -  Number of seconds between fetches of Subaru's cached vehicle information. Used to prevent excessive polling of Subaru API.  

A list of vehicles on your MySubaru account may be obtained with:
- `Controller.get_vehicles()` - Returns a list of VIN strings.  

Use the VIN as a mandatory argument when interacting with the controller.   Determine your vehicle telematics version with:
- `Controller.get_api_gen(vin)` - Returns `"g1"` or `"g2"`

Although an attempt has been made to properly invoke `"g1"` API calls, nothing in this package has been tested with a `"g1"` vehicle, and results may be unpredictable. 

Remote commands generally take about 10 seconds to complete, and can be invoked with the following methods:
- `Controller.lock(vin)`
- `Controller.unlock(vin)`
- `Controller.horn(vin)`
- `Controller.lights(vin)`
- `Controller.remote_start(vin, climate args)`
- `Controller.remote_stop(vin)`
- `Controller.charge_start(vin)`  - PHEV Only

Starlink Subarus also sends vehicle status information.  `"g1"` vehicles do not support this.  This data can be retrieved with the following methods:
- `Controller.get_data(vin)` - Returns locally cached data about vehicle, if available.  Fetches data if not received yet.
- `Controller.fetch(vin)` - Uses Subaru API to fetch Subaru's cached vehicle data.  This does not request a command to be sent to the vehicle.  This data may be stale, so check the timestamp and request an update if necessary.  The Crosstrek PHEV has been observed to automatically push vehicle updates after certain state changes (power off, charging cable inserted).
- `Controller.update(vin)` - Uses Subaru API to send a remote update request to the vehicle. Excessive use may drain vehicle battery.  Throttled with update_interval. 

See [`examples/cli.py`](examples/cli.py) for an example of how to use the `subarulink` package in a standalone application.

## Home Assistant
The subpackage `subarulink.hass` is deprecated for `subarulink>=0.3.0`.  All code to integrate this package's functionality into Home Assistant will be maintained [here](https://github.com/G-Two/home-assistant/tree/subaru). 
