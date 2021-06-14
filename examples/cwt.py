"""
Experimenting with RFC 8392 CBOR Web Tokens

>>> import binascii
>>> from pprint import pprint
>>> schema = CWTClaimsSchema()
>>> claims = schema.loads(
...     binascii.unhexlify(
...         b'a70175636f61703a2f2f61732e6578616d706c652e636f6d02656572696b7703'
...         b'7818636f61703a2f2f6c696768742e6578616d706c652e636f6d041a5612aeb0'
...         b'051a5610d9f0061a5610d9f007420b71'
...     )
... )
>>> pprint(claims)
{'aud': 'coap://light.example.com',
 'cti': '0b71',
 'exp': datetime.datetime(2015, 10, 5, 17, 9, 4, tzinfo=datetime.timezone.utc),
 'iat': datetime.datetime(2015, 10, 4, 7, 49, 4, tzinfo=datetime.timezone.utc),
 'iss': 'coap://as.example.com',
 'nbf': datetime.datetime(2015, 10, 4, 7, 49, 4, tzinfo=datetime.timezone.utc),
 'sub': 'erikw'}
>>> macd_cwt = binascii.unhexlify(
...     b'd83dd18443a10104a1044c53796d6d65747269633235365850a70175636f6170'
...     b'3a2f2f61732e6578616d706c652e636f6d02656572696b77037818636f61703a'
...     b'2f2f6c696768742e6578616d706c652e636f6d041a5612aeb0051a5610d9f006'
...     b'1a5610d9f007420b7148093101ef6d789200'
... )
>>> macd_schema = CWTMACSchema()
>>> macd_claims = macd_schema.loads(macd_cwt)
>>> pprint(macd_claims)
{'alg': {'alg': 4},
 'kid': {'kid': 'Symmetric256'},
 'payload': {'aud': 'coap://light.example.com',
         'cti': '0b71',
         'exp': datetime.datetime(2015, 10, 5, 17, 9, 4, tzinfo=datetime.timezone.utc),
         'iat': datetime.datetime(2015, 10, 4, 7, 49, 4, tzinfo=datetime.timezone.utc),
         'iss': 'coap://as.example.com',
         'nbf': datetime.datetime(2015, 10, 4, 7, 49, 4, tzinfo=datetime.timezone.utc),
         'sub': 'erikw'},
 'tag': '093101ef6d789200'}
"""

import cbor2
from marshmallow import pre_load, post_dump, ValidationError
from marshmallow_cbor import Schema, fields


class CWTClaimsSchema(Schema):
    iss = fields.Url(data_key=1, schemes=('coap',))
    sub = fields.String(data_key=2)
    aud = fields.Url(data_key=3, schemes=('coap',))
    exp = fields.Timestamp(data_key=4)
    nbf = fields.Timestamp(data_key=5)
    iat = fields.Timestamp(data_key=6)
    cti = fields.Bytes(data_key=7, load_as='hex')


class AlgSchema(Schema):
    alg = fields.Integer(data_key=1)


class KidSchema(Schema):
    kid = fields.Bytes(data_key=4, load_as='utf8')


class CWTMACSchema(Schema):
    alg = fields.Embedded(fields.Nested(AlgSchema))            # Protected
    kid = fields.Nested(KidSchema)                             # Unprotected
    payload = fields.Embedded(fields.Nested(CWTClaimsSchema))  # Protected
    tag = fields.Bytes(load_as='hex')                          # Unprotected

    @pre_load
    def unpack_tags(self, data, **kwargs):
        if isinstance(data, cbor2.CBORTag) and data.tag == 61 and data.value.tag == 17:
            return data.value.value
        else:
            raise ValidationError

    def _deserialize(self, data, many, **kwargs):
        row = dict(alg=data[0], kid=data[1], payload=data[2], tag=data[3])
        return super()._deserialize(row, many=many, **kwargs)

    def _serialize(self, value, many, **kwargs):
        value = super()._serialize(value, many=many, **kwargs)
        payload = [value['alg'], value['kid'], value['payload'], value['tag']]
        return payload

    @post_dump
    def pack_tags(self, data, **kwargs):
        return cbor2.CBORTag(61, cbor2.CBORTag(17, data))
