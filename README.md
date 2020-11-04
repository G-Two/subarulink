# subarulink
A python package for interacting with the [Subaru Starlink](https://www.subaru.com/owners/starlink/safety-security.html) remote vehicle services API.  The API is useful to obtain information about a vehicle as well as actuate exposed features such as locks, horn, lights and remote start.

This package was developed primarily for enabling [Home Assistant](https://www.home-assistant.io/) integration, however it may also be used for standalone applications.  A basic python console application is included as an example.

This package supports Subaru Starlink equipped vehicles with active service plans. Your [MySubaru](https://www.mysubaru.com) account must be setup prior to using this package. The features available will depend on your model year and type of service plan (Safety Plus or Safety/Security Plus).

**NOTE:** The functionality of this package has only been tested on newer models (model year 2019+). Older (model years 2016-2018) vehicles have not been tested, but should also work.  Subaru has no official API; therefore, this library may stop working at any time without warning.  Use at your own risk.


## Credits
Based upon the [teslajsonpy](https://github.com/zabuldon/teslajsonpy) package developed by @zabuldon, licensed under Apache 2.0.


## Home Assistant Integration
Development of a Home Assistant integration is in progress (using the Tesla integration as a template, credit to @zabuldon).  A [PR has been submitted](https://github.com/home-assistant/core/pull/35760) and is pending review/approval.

## Installation
Once Home Assistant integration is complete, this package will be automatically installed as a dependency.  For those that would like to try the console application or use the package in their own application, install from PyPI:

    $ pip install subarulink

## Usage
The PyPI installation includes a basic interactive console application.  The console can be either run interactively or used to issue a single command.  The single command function requires a working config file to function properly (config file is automatically created during the first interactive run).  Note that not all exposed functions are supported by all vehicles. Consult your Starlink subscription details to determine which commands apply to your vehicle.

```
usage: subarulink [-h] [-i] [-c CONFIG_FILE] [-v {0,1,2}]
           {status,lock,unlock,lights,horn,locate,remote_start,remote_stop,charge}
           ...

optional arguments:
  -h, --help            show this help message and exit
  -i, --interactive     interactive mode
  -c CONFIG_FILE, --config CONFIG_FILE
                        specify config file (default is ~/.subarulink.cfg
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
Starlink accounts with multiple vehicles will need to specify the VIN for single commands.  This can be done in two ways:
- Set a default VIN while in interactive mode, which will be saved to the configuration file and used for all single commands
- Specify a VIN from the command line with --vin.  This will override the default VIN in the configuration file
Accounts with only one vehicle do not need to specify a VIN


## Known Issues
### Battery Discharge
Aggressively polling the vehicle location with subarulink.Controller.update(vin) may discharge the auxiliary battery (in a PHEV).  Intermittent (every 2 hours) use isn't a problem, but polling at 5 minute intervals will drain the auxiliary battery fully after a few consecutive non-driving days.  The vehicle does report the auxiliary battery voltage with every update, so this can be avoided.  

Effects of aggressive polling on the battery of a gasoline-only vehicle are unknown.

### Erroneous data
The data returned by the Subaru API is sometimes invalid. The returned data is checked for erroneous values.  If they are invalid, the local cache will retain the last sane value.

### Incomplete data
Some of the fields that would be useful are always reported back as "UNKNOWN".  Examples include door lock state, window state, etc.