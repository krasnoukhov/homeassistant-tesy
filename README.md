# Home Assistant Tesy integration

This Unofficial Tesy integration allows you to controll smart wifi devices based on external esp32 WiFi module (black pcb). 
It won't work if you have older device based on Atheros AR9331 chipsed since the local API are different.In this case the module could be replaced with esp32 replacement module as they are compatible with most of tesy water heaters, even if not comming with WiFi from the factory.

Tested with:

- [Tesy Modeco Cloud GCV 150 47 24D C22 ECW](https://tesy.com/products/electric-water-heaters/modeco-series/modeco-cloud/?product=gcv-1504724d-c22-ecw)



## Highlights
This intergation allows you to change modes of the water heater ass well as controling the temperature setpoint in manual mode(defined as Performance in HA). 

Also energy counter is working. It uses long term counter from the device that has the seconds the heater/s was/ware on. In order for this to work propperly you need to enter your heater power rating in the setup dialog. This information could be found on the device's label. For double tank devices this is read from the device and leaving it as zero is recommended.


### Have the heater device in HA

<img src="https://github.com/krasnoukhov/homeassistant-tesy/assets/944286/a08289f7-d7cc-49a0-9747-9fbd765e58d1" alt="heater" width="400">

## Installation

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

### Via HACS
* Add this repo as a ["Custom repository"](https://hacs.xyz/docs/faq/custom_repositories/) with type "Integration"
* Click "Install" in the new "Tesy" card in HACS.
* Install
* Restart Home Assistant
* Click add Integration and choose Tesy as integration and put your IP, power rating as prompted.

### Manual Installation (not recommended)
* Copy the entire `custom_components/tesy/` directory to your server's `<config>/custom_components` directory
* Restart Home Assistant


#TODO Ask for power on single tank heaters, now hardcoded to 2400w for ceramic heaters
#TODO Add convector heaters with id of 1005,1006 


