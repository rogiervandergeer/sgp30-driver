from pytest import mark

from sgp30 import SGP30


class TestSGP30:
    @mark.parametrize(
        "data, crc",
        [
            (b"\x01\x90", b"\x4c"),
            (b"\x00\x00", b"\x81"),
            (b"\xbe\xef", b"\x92"),
        ],
    )
    def test_crc(self, data, crc):
        assert SGP30._crc(data) == crc

    @mark.parametrize(
        "output_data, input_data",
        [
            ([0], b"\x00\x00\x81"),
            ([48879, 0], b"\xbe\xef\x92\x00\x00\x81"),
        ],
    )
    def test_decode(self, input_data, output_data):
        assert SGP30._decode(input_data, int(len(input_data) / 3)) == output_data

    @mark.parametrize(
        "input_data, output_data",
        [
            ([0], b"\x00\x00\x81"),
            ([48879, 0], b"\xbe\xef\x92\x00\x00\x81"),
        ],
    )
    def test_encode(self, input_data, output_data):
        assert SGP30._encode(input_data) == output_data
