import datetime as dt
import ipaddress
from binascii import hexlify, unhexlify

import cbor2
import pytest

from marshmallow_cbor import Schema, fields
from marshmallow import ValidationError


def dumper(data, **kwargs):
    encoded = cbor2.dumps(data, **kwargs)
    return hexlify(encoded).decode()


# DateTime


class DTSchema(Schema):
    ts = fields.AwareDateTime()


class TSSchema(Schema):
    ts = fields.Tagged(fields.Timestamp(), tag=1)


class BareTSSchema(Schema):
    ts = fields.Timestamp()


# IP addresses


class IPSchema(Schema):
    ip = fields.IPv4()


class NetSchema(Schema):
    ip = fields.IPv4Network()


# Bytes as strings


class HexSchema(Schema):
    data = fields.Bytes(load_as="hex")


class Utf8bytesSchema(Schema):
    data = fields.Bytes(load_as="utf8")


class SVSchema(Schema):
    data = fields.SimpleValue()


@pytest.mark.parametrize(
    'schema, data, expected',
    [
        (
            DTSchema(),
            {'ts': dt.datetime(2021, 6, 30, 19, tzinfo=dt.timezone.utc)},
            dumper({'ts': dt.datetime(2021, 6, 30, 19, tzinfo=dt.timezone.utc)}),
        ),
        (
            TSSchema(),
            {'ts': dt.datetime(2021, 6, 30, 19, tzinfo=dt.timezone.utc)},
            dumper(
                {'ts': dt.datetime(2021, 6, 30, 19, tzinfo=dt.timezone.utc)},
                datetime_as_timestamp=True,
            ),
        ),
        (
            TSSchema(),
            {'ts': dt.datetime(2021, 6, 30, 19, 8, 7, 6, tzinfo=dt.timezone.utc)},
            dumper(
                {'ts': dt.datetime(2021, 6, 30, 19, 8, 7, 6, tzinfo=dt.timezone.utc)},
                datetime_as_timestamp=True,
            ),
        ),
        (
            BareTSSchema(),
            {'ts': dt.datetime(1970, 1, 2, 10, 17, 36, tzinfo=dt.timezone.utc)},
            dumper(
                {'ts': 123456},
            ),
        ),
        (
            IPSchema(),
            {'ip': ipaddress.IPv4Address('192.168.0.1')},
            dumper({'ip': ipaddress.IPv4Address('192.168.0.1')}),
        ),
        (
            NetSchema(),
            {'ip': ipaddress.IPv4Network('192.168.0.0/24')},
            dumper({'ip': ipaddress.IPv4Network('192.168.0.0/24')}),
        ),
        (HexSchema(), {'data': '010203'}, dumper({'data': b'\x01\x02\x03'})),
        (
            Utf8bytesSchema(),
            {'data': '\u0001\u0002\u0003'},
            dumper({'data': b'\x01\x02\x03'}),
        ),
        (
            SVSchema(),
            {'data': cbor2.CBORSimpleValue(9)},
            dumper({'data': cbor2.CBORSimpleValue(9)}),
        ),
    ],
)
def test_field(schema, data, expected):
    assert hexlify(schema.dumps(data)).decode() == expected
    assert schema.loads(unhexlify(expected)) == data


@pytest.mark.parametrize(
    'schema, data, expected',
    [
        (
            Utf8bytesSchema(),
            dumper({'data': b'\x01\x02\x03\x80'}),
            {'data': '\x01\x02\x03\\x80'},
        ),
    ],
)
def test_loads_one_way(schema, data, expected):
    assert schema.loads(unhexlify(data)) == expected


def test_invalid_string_display():
    with pytest.raises(ValueError):

        class Fake(Schema):
            a = fields.Bytes(load_as="extra spicy")


def test_simple_error():
    schema = SVSchema()
    with pytest.raises(ValidationError) as exc_info:
        schema.loads(cbor2.dumps({'data': 97}))
    assert exc_info.value.args[0] == {'data': ['Not a CBOR Simple Value']}
