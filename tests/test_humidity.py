from pytest import approx, mark

from sgp30.humidity import absolute_humidity


@mark.parametrize(
    "temperature, relative_humidity, absolute_humidity_value",
    [(30, 0, 0), (10, 30, 2.8), (-5, 80, 2.7), (40, 60, 30.7), (25, 50, 11.5)],
)
def test_absolute_humidity(temperature, relative_humidity, absolute_humidity_value):
    assert absolute_humidity(temperature, relative_humidity) == approx(
        absolute_humidity_value, abs=0.1
    )
