import datetime as dt
import ipaddress

import cbor2
import pytest

from marshmallow_cbor import Schema, fields

# DateTime


class DTSchema(Schema):
    ts = fields.AwareDateTime()


class TSSchema(Schema):
    ts = fields.Tagged(fields.Timestamp(), tag=1)


class IPSchema(Schema):
    ip = fields.IPv4()


class NetSchema(Schema):
    ip = fields.IPv4Network()


@pytest.mark.parametrize(
    'schema, data, expected',
    [
        (
            DTSchema(),
            {'ts': dt.datetime(2021, 6, 30, 19, tzinfo=dt.timezone.utc)},
            cbor2.dumps({'ts': dt.datetime(2021, 6, 30, 19, tzinfo=dt.timezone.utc)}),
        ),
        (
            TSSchema(),
            {'ts': dt.datetime(2021, 6, 30, 19, tzinfo=dt.timezone.utc)},
            cbor2.dumps(
                {'ts': dt.datetime(2021, 6, 30, 19, tzinfo=dt.timezone.utc)},
                datetime_as_timestamp=True,
            ),
        ),
        (
            IPSchema(),
            {'ip': ipaddress.IPv4Address('192.168.0.1')},
            cbor2.dumps({'ip': ipaddress.IPv4Address('192.168.0.1')}),
        ),
        (
            NetSchema(),
            {'ip': ipaddress.IPv4Network('192.168.0.0/24')},
            cbor2.dumps({'ip': ipaddress.IPv4Network('192.168.0.0/24')}),
        ),
    ],
)
def test_field(schema, data, expected):
    assert schema.dumps(data) == expected
    assert schema.loads(expected) == data
