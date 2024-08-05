# Home Assistant Tesy integration

This unofficial Tesy integration allows you to control smart wifi devices based on external esp32 wifi module (black pcb).
It won't work if you have older device based on Atheros AR9331 chipset since the local API is different. In this case the module could be replaced with esp32 replacement module as they are compatible with most of Tesy water heaters, even if not comming with WiFi from the factory.

Tested with:

- [Tesy Modeco Cloud GCV 150 47 24D C22 ECW](https://tesy.com/products/electric-water-heaters/modeco-series/modeco-cloud/?product=gcv-1504724d-c22-ecw)
- BilightSmart
- BeliSlimo

## Highlights

This intergation allows you to change modes of the water heater as well as controling the temperature setpoint in manual mode (defined as Performance in HA).

Energy counter is also working. It uses long term counter from the device that counts the seconds the heater was on. In order for this to work propperly you need to enter your heater power rating in the setup dialog. This information could be found on the device's label. For double tank devices this is read from the device and leaving it as zero is recommended.

This integration exposes boost mode of the heaters as a switch. It can be switched on and off, but in order to work the heater should on.

Temperature setpoint is only used in manual (Performance) mode. In any other modes it is ignored. If setpoint is manually changed operation mode will jump to performance in case the heater is powered on.

<img src="https://github.com/krasnoukhov/homeassistant-tesy/assets/944286/a08289f7-d7cc-49a0-9747-9fbd765e58d1" alt="heater" width="400">

## Installation

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

### Via HACS
* Add this repo as a ["Custom repository"](https://hacs.xyz/docs/faq/custom_repositories/) with type "Integration"
* Click "Install" in the new "Tesy" card in HACS.
* Install
* Restart Home Assistant
* Click Add Integration and choose Tesy, follow the configuration flow

### Manual Installation (not recommended)
* Copy the entire `custom_components/tesy/` directory to your server's `<config>/custom_components` directory
* Restart Home Assistant
