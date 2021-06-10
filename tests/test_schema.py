import binascii
import decimal
import uuid

import pytest

from cbor2 import CBORTag
from marshmallow import pre_load, post_dump, ValidationError
from marshmallow_cbor import Schema
from marshmallow_cbor.fields import (
    AwareDateTime,
    Decimal,
    UUID,
    Boolean,
    Tagged,
    Embedded,
    Nested,
)


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


class WithEmbed(Schema):
    payload = Embedded(Nested(EmbedSchema))


class NestedTaggedSchema(Schema):
    a = Tagged(Nested(UUIDSchema), tag=3360)
    b = Boolean()


class TagWithinTagSchema(Schema):
    a = Boolean()
    b = Boolean()

    @pre_load
    def unpack_tags(self, data, **kwargs):
        if data.tag == 5990 and data.value.tag == 5991:
            return data.value.value

    @post_dump
    def pack_tags(self, data, **kwargs):
        return CBORTag(5990, CBORTag(5991, data))


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
            WithEmbed(),
            {'payload': {'a': True, 'b': decimal.Decimal(1)}},
            b'a1677061796c6f61644aa26162c48200016161f5',
        ),
        (
            NestedTaggedSchema(),
            {'a': {'uid': uuid.uuid5(uuid.NAMESPACE_DNS, 'example.com')}, 'b': True},
            b'a26162f56161d90d20a163756964d82550cfbff0d193755685968c48ce8b15ae17',
        ),
        (
            TagWithinTagSchema(),
            CBORTag(5990, CBORTag(5991, {'a': True, 'b': False})),
            b'd91766d91767a26162f46161f5',
        ),
    ],
)
def test_schema_dumps(schema, source, expected):

    data = schema.load(source)
    print(data)

    encoded = schema.dumps(data)

    assert binascii.hexlify(encoded) == expected

    data2 = schema.loads(encoded)

    assert data == data2


class IncorrectTagSchema(Schema):
    a = Boolean()
    b = Boolean()

    class Meta:
        tag = 4096


class IncorrectNestedTag(Schema):
    a = Tagged(Nested(UUIDSchema), tag=3017)
    b = Boolean()


@pytest.mark.parametrize(
    'schema, source, expected',
    [
        (IncorrectTagSchema(), b'D91001A26161F56162F4', ValidationError),
        (
            IncorrectNestedTag(),
            b'a26162f56161d90d20a163756964d82550cfbff0d193755685968c48ce8b15ae17',
            ValidationError,
        ),
    ],
)
def test_exceptions(schema, source, expected):
    with pytest.raises(expected):
        schema.loads(binascii.unhexlify(source))
