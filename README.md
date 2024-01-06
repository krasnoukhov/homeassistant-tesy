# Home Assistant Tesy integration

This Unofficial Tesy integration allows you to controll smart wifi devices based on external esp32 WiFi module (black pcb). 
It won't work if you have older device based on Atheros AR9331 chipsed since the local API are different.In this case the module could be replaced with esp32 replacement module as they are compatible with most of tesy water heaters, even if not comming with WiFi from the factory.

Tested with:

- [Tesy Modeco Cloud GCV 150 47 24D C22 ECW](https://tesy.com/products/electric-water-heaters/modeco-series/modeco-cloud/?product=gcv-1504724d-c22-ecw)



## Highlights
This intergation allows you to change modes of the water heater ass well as controling the temperature setpoint in manual mode(defined as Performance in HA). 

Also energy counter is working. It uses long term counter from the device that has the seconds the heater/s was/ware on. In order for this to work propperly you need to enter your heater power rating in the setup dialog. This information could be found on the device's label. For double tank devices this is read from the device and leaving it as zero is recommended.

This integration exposes boost mode of the heaters as a switch. It can be switched on and off, but in order to work the heater should on. 

Temperature setpoint is only used in manual(PERFORMANCE) mode. In any other modes it is ignored. If setpoint is manually changed operation mode will jump to performance in case the heater is powered on.


### Have the heater device in HA

<img src="https://github.com/krasnoukhov/homeassistant-tesy/assets/944286/a08289f7-d7cc-49a0-9747-9fbd765e58d1" alt="heater" width="400">
![image](https://github.com/artin961/homeassistant-tesy/assets/11786511/d0b60f99-f17a-4327-a417-dc084d2a84db)

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
