# sgp30-driver
Easy-to-use python driver for the [Sensirion SGP30](https://sensirion.com/us/products/catalog/SGP30/) multi gas sensor

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/rogiervandergeer/sgp30-driver/Continuous%20Integration) 
![PyPI](https://img.shields.io/pypi/v/sgp30-driver)
![PyPI - License](https://img.shields.io/pypi/l/sgp30-driver)
![PyPI - Downloads](https://img.shields.io/pypi/dm/sgp30-driver) 

## Installation

The package is available on [PyPI](https://pypi.org/project/sgp30-driver/). Installation is can be done with your favourite package manager. For example:

```bash
pip install sgp30-driver
```

## Usage

In order to initialise the device we need an open `SMBus` object. 
Depending on the machine that you are running on you may need to provide another bus number or path:
```python
from sgp30 import SGP30
from smbus2 import SMBus


with SMBus(1) as bus:
    device = SGP30(bus=bus)
```

The address of the `SGP30` defaults to `0x58`. This is the (fixed) address of the SGP30 devices, so you should
never have to change it. If you _do_ want to change it, you can provide it like `SGP30(bus=bus, address=0x59)`.

### Initialisation

After every restart the SGP30 has to be initialised:
```python
device.initialise()
```
This process can take up to 20 seconds.

This process can be sped up by passing recent values of the baseline compensation algorithm: store the result
of `device.baseline` somewhere in non-volatile memory, and restore it with:
```python
device.initialise(baseline)
```

### Measuring

After initialisation the device is ready for taking measurements. The `measure()` method returns
an `SGP30Measurement` object which has two attributes: `equivalent_co2` which represents the CO2 concentration
in ppm (parts-per-million) and `tvoc` which represents the TVOC (total volatile organic compounds) in ppb
(parts-per-billion).
```python
measurement = device.measure()
print(f"{measurement.equivalent_co2} ppm CO2, {measurement.tvoc} ppb TVOC")
```

In order to ensure the proper working of the baseline compensation algorithm one should call the `measure()` method
 in regular intervals of 1 second.

### Humidity compensation

The SGP30 has on-chip humidity compensation. In order to enable the compensation, set
the humidity using `set_humidity()`:
```python
device.set_humidity(15.2)
```
The accepted humidity value is the absolute humidity in `g/m3`.
