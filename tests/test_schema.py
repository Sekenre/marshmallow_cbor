import binascii
import decimal
import uuid

import pytest

from marshmallow_cbor import Schema
from marshmallow_cbor.fields import AwareDateTime, Decimal, UUID, Boolean


class DateTimeSchema(Schema):
    ts = AwareDateTime(data_key=0)


class DecimalSchema(Schema):
    num = Decimal()


class UUIDSchema(Schema):
    uid = UUID()


class TaggedSchema(Schema):
    a = Boolean()
    b = Decimal()

    class Meta:
        tag = 4096


class EmbedSchema(Schema):
    a = Boolean()
    b = Decimal()

    class Meta:
        tag = 4096
        embed = True


@pytest.mark.parametrize(
    'schema, source, expected',
    [
        (
            DateTimeSchema(),
            {0: '2012-03-07T14:32:00.769Z'},
            b'a100c0781b323031322d30332d30375431343a33323a30302e3736393030305a',
        ),
        (
            DecimalSchema(),
            {'num': decimal.Decimal(355) / decimal.Decimal(113)},
            b'a1636e756dc482381ac24c0a26aa2d773467d3bb65f268',
        ),
        (
            UUIDSchema(),
            {'uid': uuid.uuid5(uuid.NAMESPACE_DNS, 'example.com')},
            b'a163756964d82550cfbff0d193755685968c48ce8b15ae17',
        ),
        (
            TaggedSchema(),
            {'a': True, 'b': decimal.Decimal(1)},
            b'd91000a26162c48200016161f5',
        ),
        (
            EmbedSchema(),
            {'a': True, 'b': decimal.Decimal(1)},
            b'd910004aa26162c48200016161f5',
        ),
    ],
)
def test_schema_dumps(schema, source, expected):

    data = schema.load(source)

    encoded = schema.dumps(data)

    assert binascii.hexlify(encoded) == expected

    data2 = schema.loads(encoded)

    assert data == data2
