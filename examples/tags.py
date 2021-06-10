from marshmallow_cbor import Schema, fields


class PointSchema(Schema):
    """
    Simple tagged schema, this as set as an option on the Meta class

    >>> from binascii import hexlify, unhexlify
    >>> point = {'x': 1.2, 'y': 1.3, 'z': 1.4}
    >>> schema = PointSchema()
    >>> hexlify(schema.dumps(point))
    b'd93039a36178fb3ff33333333333336179fb3ff4cccccccccccd617afb3ff6666666666666'
    >>> schema.loads(unhexlify(_))
    {'x': 1.2, 'y': 1.3, 'z': 1.4}
    """

    x = fields.Float()
    y = fields.Float()
    z = fields.Float()

    class Meta:
        tag = 12345
