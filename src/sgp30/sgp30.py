from dataclasses import dataclass
from struct import unpack, pack
from time import sleep
from typing import Tuple, Optional, List

from smbus2 import SMBus, i2c_msg


class InvalidCRC(ValueError):
    pass


@dataclass
class SGP30Measurement:
    equivalent_co2: int
    tvoc: int

    def __str__(self) -> str:
        return f"SGP30 measurement: {self.equivalent_co2} ppm CO2, {self.tvoc} ppb TVOC"


class SGP30:
    """Driver for the Sensirion SGP30 multi gas sensor."""

    def __init__(self, bus: SMBus, address: int = 0x58):
        self.bus = bus
        self.address = address
        self.latest_measurement: Optional[SGP30Measurement] = None

    @property
    def serial_id(self) -> int:
        """Get the Serial ID of the sensor.

        The Serial ID can be used to identify the chip and verify the presence of the sensor."""
        data = self._command(b"\x36\x82", read_parameters=3, delay=0.001)
        return (data[0] << 32) + (data[1] << 16) + data[2]

    @property
    def feature_set(self) -> int:
        """Get the feature set of the sensor.

        The SGP30 features a versioning system for the available set of measurement commands and on-chip algorithms.
        The last five bits denote the product version. As of 2022-04-07, the only documented feature set is 0x0020."""
        data = self._command(b"\x20\x2f", read_parameters=1, delay=0.002)
        return data[0]

    def initialise(self, baseline: Optional[Tuple[int, int]] = None) -> None:
        """Initialise the sensor.

        After a restart the baseline compensation algorithm of the sensor must be initialized.
        This process can take up to 20 seconds. However, if recent values of the baseline compensation
        algorithm are passed, initialisation is near-instant."""
        self._command(b"\x20\x03")
        if baseline is None:
            for _ in range(20):
                sleep(1)
                result = self.measure()
                if result.equivalent_co2 != 400:
                    break
        else:
            self.baseline = baseline

    @property
    def baseline(self) -> Tuple[int, int]:
        """Get or get the current baseline compensation values.

        This can be used to prevent having to re-initialise the sensor after a restart, by
        storing the values off-chip and restoring them after the reset."""
        data = self._command(b"\x20\x15", read_parameters=2, delay=0.010)
        return data[0], data[1]  # Read ordered CO2eq / TVOC

    @baseline.setter
    def baseline(self, values: Tuple[int, int]) -> None:
        self._command(
            b"\x20\x1E", parameters=[values[1], values[0]]
        )  # Write ordered TVOC / CO2eq

    def measure(self) -> SGP30Measurement:
        """Perform a measurement and return the results.

        This command has to be executed in regular intervals of 1 second to ensure proper operation of
        the dynamic baseline compensation algorithm."""
        data = self._command(b"\x20\x08", read_parameters=2, delay=0.022)
        self.latest_measurement = SGP30Measurement(equivalent_co2=data[0], tvoc=data[1])
        return self.latest_measurement

    def raw_signals(self) -> Tuple[int, int]:
        """Read the raw sensor signals.

        Returns the sensor signals that are used as inputs for the on-chip calibration and baseline
        compensation algorithms. The signals represent H2 and Ethanol and are used to compute the
        gas concentrations c relative to a (to us unknown) reference concentration c_ref by

        ln(c / c_ref) = (s_ref / s_out) / 512

        where s_ref is the signal at the reference concentration (also unknown to us)."""
        data = self._command(b"\x20\x50", read_parameters=2, delay=0.025)
        return data[0], data[1]

    def set_humidity(self, humidity: float) -> None:
        """Set the humidity.

        Accepts an absolute humidity in g/m3. After setting the new humidity value, this value will be used
        in the on-chip humidity compensation algorithm.

        Restarting the sensor or setting a humidity of 0 sets the humidity value to its default (11.57g/m3)."""
        if int(humidity) > 255:
            raise ValueError(f"Humidity value may not exceed 255 g/m3.")
        value = int(humidity * 255)
        self._command(b"\x20\x61", parameters=[value])

    def _command(
        self,
        command: bytes,
        parameters: Optional[List[int]] = None,
        read_parameters: int = 0,
        delay: float = 0,
    ) -> Optional[List[int]]:
        """Perform a command.

        The SGP30 accepts a two-byte commands, optionally with additional parameters. If a response is
        expected, wait for delay to allow the sensor enough time to prepare the response, and then
        read the data.

        All parameters are two-byte words followed by a single byte CRC."""
        if parameters is not None:
            command += self._encode(parameters=parameters)
        self.bus.i2c_rdwr(i2c_msg.write(self.address, command))
        if read_parameters > 0:
            sleep(delay)
            read_cmd = i2c_msg.read(self.address, read_parameters * 3)
            self.bus.i2c_rdwr(read_cmd)
            return self._decode(bytes(read_cmd), n_parameters=read_parameters)

    @classmethod
    def _decode(cls, raw_data: bytes, n_parameters: int) -> List[int]:
        """Decode incoming data and check CRC."""
        for i in range(n_parameters):
            block = raw_data[3 * i : 3 * (i + 1)]
            if cls._crc(block[:-1]) != block[-1:]:
                raise InvalidCRC(f"CRC of {block[:-1]} != {block[-1:]}")
        return list(unpack(">" + "Hx" * n_parameters, raw_data))

    @classmethod
    def _encode(cls, parameters: List[int]) -> bytes:
        """Encode outgoing data and add CRC."""
        result = b""
        for parameter in parameters:
            packed_parameter = pack(">H", parameter)
            crc = cls._crc(packed_parameter)
            result += packed_parameter + crc
        return result

    @staticmethod
    def _crc(data: bytes) -> bytes:
        """Compute the 8-bit CRC checksum of byte data."""
        crc = 0xFF
        assert len(data) == 2
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc <<= 1
        return pack(">B", crc & 0xFF)
