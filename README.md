# Home Assistant Tesy integration

The Tesy integration allows you to control a smart water heater.

Tested with:

- [Tesy Modeco Cloud GCV 150 47 24D C22 ECW](https://tesy.com/products/electric-water-heaters/modeco-series/modeco-cloud/?product=gcv-1504724d-c22-ecw)

## Highlights

### Have the heater device in HA

<img src="https://github.com/krasnoukhov/homeassistant-tesy/assets/944286/27a325d1-5713-4b4f-827b-c6272eca8415" alt="heater" width="400">

## Installation

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

### Via HACS
* Add this repo as a ["Custom repository"](https://hacs.xyz/docs/faq/custom_repositories/) with type "Integration"
* Click "Install" in the new "Tesy" card in HACS.
* Install
* Restart Home Assistant

### Manual Installation (not recommended)
* Copy the entire `custom_components/tesy/` directory to your server's `<config>/custom_components` directory
* Restart Home Assistant
