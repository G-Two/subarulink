# subarulink
A python package for interacting with the Subaru Starlink remote vehicle services API.  The API is useful to obtain information about a vehicle as well as actuate exposed features such as locks, horn, lights and remote start.

This package was developed primarily for enabling Home-Assistant integration, however it may also be used for standalone applications.  A basic python console application is included as an example.

This package only supports Subaru Starlink equipped vehicles with active Starlink subscriptions.  New PHEV Crosstreks include a 10 year subscription.  Your [MySubaru](https://www.mysubaru.com) account must be setup prior to using this package.

**NOTE:** The functionality of this package has only been tested on a 2019 Subaru Crosstrek PHEV.  Newer (g2 API) vehicles should also work.  Older (g1 API) vehicles have not been tested.  Subaru has no official API; therefore, this library may stop working at any time without warning.  Use at your own risk.


## Credits

Based upon the [teslajsonpy](https://github.com/zabuldon/teslajsonpy) package developed by @zabuldon, licensed under Apache 2.0.


## Home Assistant Integration
Development of a Home Assistant integration is in progress (using the Tesla integration as a template, credit to @zabuldon).  Once completed, a PR will be submitted to add the integration into the main Home Assistant repo.  Until then, it is available [here](https://github.com/G-Two/home-assistant/tree/subaru). 

## Installation
Once Home Assistant integration is complete, this package will be automatically installed as a dependency.  For those that would like to try the console application or use the package in their own application, install from PyPI:

    $ pip install subarulink

## Usage
The PyPI installation includes a basic interactive console application.  

```
usage: subarulink [-h] [-v {0,1,2}] [-r]

optional arguments:
  -h, --help            show this help message and exit
  -v {0,1,2}, --verbosity {0,1,2}
                        Verbosity Level: 0=Error[default] 1=Info 2=Debug
  -r, --reset           Reset saved account information
```


## Known Issues
### Battery Discharge
Aggressively polling the vehicle location with subarulink.Controller.update(vin) may discharge the auxiliary battery (in a PHEV).  Intermittent use isn't a problem, but polling at 5 minute intervals will drain the auxiliary battery fully after a few consecutive non-driving days.  The vehicle does report the auxiliary battery voltage with every update, so this can be avoided.  

Effects of aggressive polling on the battery of a gasoline-only vehicle are unknown.

### Erroneous data
The data returned by the Subaru API is sometimes invalid.
* Tire Pressure returns invalid values unless queried immediately after vehicle is turned off.
* EV Range is invalid immediately after vehicle is driven and turned off (vehicle seems to report a value that is near the hybrid drive range).
* Data fields are sometimes omitted.

### Incomplete data
Some of the fields that would be useful are always reported back as "UNKNOWN".  Examples include door lock state, window state, etc.