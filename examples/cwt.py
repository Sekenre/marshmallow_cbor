import binascii

import cbor2
from marshmallow import pre_load, post_dump, ValidationError
from marshmallow_cbor import Schema, fields


class CWTClaimsSchema(Schema):
    iss = fields.Url(data_key=1, schemes=('coap',))
    sub = fields.String(data_key=2)
    aud = fields.Url(data_key=3, schemes=('coap',))
    exp = fields.Integer(data_key=4)
    nbf = fields.Integer(data_key=5)
    iat = fields.Integer(data_key=6)
    cti = fields.Raw(data_key=7)


class AlgSchema(Schema):
    alg = fields.Integer(data_key=1)


class KidSchema(Schema):
    kid = fields.Raw(data_key=4)


class CWTMACSchema(Schema):
    alg = fields.Embedded(fields.Nested(AlgSchema))
    kid = fields.Embedded(fields.Nested(KidSchema))
    payload = fields.Embedded(fields.Nested(CWTClaimsSchema))
    tag = fields.Raw()

    @pre_load
    def unpack_tags(self, data, **kwargs):
        if isinstance(data, cbor2.CBORTag) and data.tag == 61 and data.value.tag == 17:
            return data.value.value
        else:
            raise ValidationError

    def _deserialize(self, data, many, **kwargs):
        row = {}
        row['alg'] = data[0]
        row['kid'] = data[1]
        row['payload'] = data[2]
        row['tag'] = data[3]
        return super()._deserialize(row, many=many, **kwargs)

    def _serialize(self, value, many, **kwargs):
        value = super()._serialize(value, many=many, **kwargs)
        payload = [value['alg'], value['kid'], value['payload'], value['tag']]
        return payload

    @post_dump
    def pack_tags(self, data, **kwargs):
        return cbor2.CBORTag(61, cbor2.CBORTag(17, data))


if __name__ == '__main__':
    schema = CWTClaimsSchema()
    claims = schema.loads(
        binascii.unhexlify(
            b'a70175636f61703a2f2f61732e6578616d706c652e636f6d02656572696b7703'
            b'7818636f61703a2f2f6c696768742e6578616d706c652e636f6d041a5612aeb0'
            b'051a5610d9f0061a5610d9f007420b71'
        )
    )
    print(claims)
    macd_cwt = binascii.unhexlify(
        b'd83dd18443a10104a1044c53796d6d65747269633235365850a70175636f6170'
        b'3a2f2f61732e6578616d706c652e636f6d02656572696b77037818636f61703a'
        b'2f2f6c696768742e6578616d706c652e636f6d041a5612aeb0051a5610d9f006'
        b'1a5610d9f007420b7148093101ef6d789200'
    )
    macd_schema = CWTMACSchema()
    macd_claims = macd_schema.loads(macd_cwt)
    print(macd_claims)
    print(binascii.hexlify(macd_schema.dumps(macd_claims)).decode())
