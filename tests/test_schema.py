import binascii
import datetime
import decimal
import uuid

import pytest

from marshmallow_cbor import Schema
from marshmallow_cbor.fields import AwareDateTime, Decimal, UUID, Boolean


def test_datetime():
    class MySchema(Schema):
        ts = AwareDateTime(data_key=0)

    schema = MySchema()

    data = schema.load({0: '2012-03-07T14:32:00.769Z'})

    assert data == {
        'ts': datetime.datetime(
            2012, 3, 7, 14, 32, 0, 769000, tzinfo=datetime.timezone.utc
        )
    }

    encoded = schema.dumps(data)
    print(binascii.hexlify(encoded).decode())

    assert encoded == binascii.unhexlify(
        b'a100c0781b323031322d30332d30375431343a33323a30302e3736393030305a'
    )

    data2 = schema.loads(encoded)

    assert data == data2


def test_decimal():
    class MySchema(Schema):
        num = Decimal()

    schema = MySchema()

    data = schema.load({'num': decimal.Decimal(355) / decimal.Decimal(113)})
    encoded = schema.dumps(data)
    assert data == schema.loads(encoded)


def test_uuid():
    class MySchema(Schema):
        uid = UUID()

    schema = MySchema()

    data = schema.load({'uid': uuid.uuid5(uuid.NAMESPACE_DNS, 'example.com')})
    encoded = schema.dumps(data)
    print(binascii.hexlify(encoded).decode())
    assert data == schema.loads(encoded)


def test_tag():
    class MySchema(Schema):
        a = Boolean()
        b = Decimal()
        class Meta:
            tag = 4096
    schema = MySchema()
    data = {'a': True, 'b': decimal.Decimal(1)}
    encoded = schema.dumps(data)
    assert data == schema.loads(encoded)


def test_embed():
    class MySchema(Schema):
        a = Boolean()
        b = Decimal()
        class Meta:
            tag = 4096
            embed = True
    schema = MySchema()
    data = {'a': True, 'b': decimal.Decimal(1)}
    encoded = schema.dumps(data)
    assert data == schema.loads(encoded)

