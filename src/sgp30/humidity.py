from math import exp


def absolute_humidity(
    temperature: float,
    relative_humidity: float,
) -> float:
    """Convert temperature in °C and humidity in %RH into absolute humidity in g/m3."""
    return (
        13.2471
        * relative_humidity
        * exp((17.67 * temperature) / (243.5 + temperature))
        / (273.15 + temperature)
    )
