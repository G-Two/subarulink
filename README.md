# subarulink
A python package for interacting with [Subaru STARLINK](https://www.subaru.com/owners/starlink/safety-security.html) remote vehicle services to obtain information about a vehicle as well as actuate exposed features such as locks, horn, lights and remote start. This package requires an active subscription to Subaru's STARLINK service, which is currently only available in the United States and Canada. 

This package was developed primarily for enabling [Home Assistant](https://www.home-assistant.io/) integration, however it may also be used for standalone applications.  A basic python console application is included as an example.

This package supports Subaru STARLINK equipped vehicles with active service plans. A [MySubaru](https://www.mysubaru.com) account must be setup prior to using this package. The features available will depend on the model year and type of service plan (Safety Plus or Safety/Security Plus).


| Model Year   | Safety Plus | Security Plus |
|--------------|-------------|---------------|
| 2016-2018    |  No Support | Remote Lock/Unlock <br> Remote Horn and/or Lights <br> Remote Vehicle Locator <br> Odometer (updated every 500 miles) 
| 2019+        |  Tire Pressure# <br> Fuel Economy# <br> Fuel Range# <br> Odometer#     |Remote Lock/Unlock <br> Remote Horn and/or Lights <br> Remote Vehicle Locator <br> Remote Engine Start w/ Climate Control <br> EV Start Charge* <br> Door/Window/Sunroof Status** <br> Tire Pressure <br> Fuel Economy <br> Fuel Range <br> Odometer

\# Unclear how often this is updated <br>
\* EV/PHEV only <br>
\*\* Support varies by model/year

> **NOTE:**
> This project was developed based upon analysis of the official MySubaru Android app. Subaru has no official public API; therefore, this library may stop working at any time without warning.  Use at your own risk.


## Home Assistant Integration

There is a Home Assistant [custom component](https://github.com/G-Two/homeassistant-subaru) that uses this package and allows users to add Subaru STARLINK integration to their Home Assistant instance.

In addition, as of 2021.3, Home Assistant Core includes the [Subaru integration](https://www.home-assistant.io/integrations/subaru/) that uses this package. Due to the required incremental additions required by Home Assistant Core, only the sensor and lock platforms are supported at this time. Additional PRs are pending to add full functionality. Users that desire the most recent features should continue using the custom component.

## Standalone Installation
To use this module's included standalone console application or include the package in an application, install from PyPI:

    $ pip install subarulink

For API documentation, see [DEVELOPERS.md](DEVELOPERS.md)

## Usage
The PyPI installation includes a basic console application.  The application can either be run interactively or used to issue a single command.  The single command function requires a working config file to function properly (config file is automatically created during the first interactive run).  Note that not all exposed functions are supported by all vehicles. Consult your subscription details to determine which commands apply to your vehicle.

```
usage: subarulink [-h] [-i] [-c CONFIG_FILE] [-v {0,1,2}]
           {status,lock,unlock,lights,horn,locate,remote_start,remote_stop,charge}
           ...

optional arguments:
  -h, --help            show this help message and exit
  -i, --interactive     interactive mode
  -c CONFIG_FILE, --config CONFIG_FILE
                        specify config file (default is ~/.config/subarulink/subarulink.cfg
  -v {0,1,2}, --verbosity {0,1,2}
                        verbosity level: 0=error[default] 1=info 2=debug

command:
  execute single command and exit

  {status,lock,unlock,lights,horn,locate,remote_start,remote_stop,charge}
    status              get vehicle status information
    lock                lock doors
    unlock              unlock doors
    lights              turn on lights
    horn                sound horn
    locate              locate vehicle
    remote_start        remote engine start
    remote_stop         remote engine stop
    charge              start PHEV charging
```
STARLINK accounts with multiple vehicles will need to specify the VIN for single commands.  This can be done in two ways:
- Set a default VIN while in interactive mode, which will be saved to the configuration file and used for all single commands
- Specify a VIN from the command line with --vin.  This will override the default VIN in the configuration file
Accounts with only one vehicle do not need to specify a VIN

## Configuration
A JSON file is used for configuration. A user provided file can be passed to the CLI via the `--config`. If no config file is provided, two default locations are searched for. First is `~/.subarulink.cfg` and if that is not found, `$XDG_CONFIG_HOME/subarulink/subarulink.cfg` will be used.

## Known Issues
### Battery Discharge
Aggressively polling the vehicle location with subarulink.Controller.update(vin) may discharge the auxiliary 12V battery (in a PHEV).  Intermittent (every 2 hours) use isn't a problem, but polling at 5 minute intervals will drain the auxiliary battery fully after a few consecutive non-driving days.

Effects of aggressive polling on the battery of a gasoline-only vehicle are unknown.

### Stale Data
Sensor data is only sent by the vehicle during certain events (e.g. engine shutdown or a user requested location update) and should not be relied on to indicate a vehicle's real time status. If more recent data is desired, then the user must initiate a location update which will update the data for all sensors (exception: tire pressures will only be updated if the vehicle is in motion).

### Remote climate control preset options vary by model
Options exposed by the API don't necessarily represent the remote capability of the vehicle. Selecting options not supported by your vehicle will either be ignored or cause the remote command to fail. 

Known examples include:
- Crosstreks with front heated seats cannot be activated remotely. The option is ignored by the telematics provider and/or vehicle.
- Crosstrek PHEVs do not support `climateZoneFrontAirVolume = AUTO` or `climateZoneFrontAirMode = AUTO`. Selecting these will cause the command to fail at the telematics gateway or the vehicle.

Best practice is to create presets in the official mobile app or website to ensure they are compatible with your vehicle. Any presets created through official means are automatically available to this package.

### Erroneous data
The data returned by the Subaru API is sometimes invalid. The returned data is checked for erroneous values.  If they are invalid, the local cache will retain the last sane value.

### Incomplete data
Some of the fields that would be useful are always reported back as "UNKNOWN".  Examples include door lock state, window state (on some vehicles), etc.

## Credits
- Inspired by the [teslajsonpy](https://github.com/zabuldon/teslajsonpy) package
- Thanks to all the Subaru owners that have provided feedback and data from their vehicles

## Contributions
- The most recent "g3" telematics generation appears to support more functions (e.g. tailgate unlocking and more useful sensor data). If you have a newer vehicle, please post debug logs (after sanitizing personal info) in the discussion area or open a new issue to ensure this package uses all the data that is provided by your vehicle.
- Feature additions and code quality contributions are always welcome.