from marshmallow_cbor import Schema, fields


class PersonSchema(Schema):
    """
    Simple data with string keys and values, Can be represented with JSON. No difference
    from regular Marshmallow

    >>> from binascii import hexlify
    >>> person = {
    ...     "name": "Simon",
    ...     "occupation": "Skydiving Instructor",
    ...     "homepage": "https://example.com/letsgoskydiving"
    ... }
    >>> expected = (b'a3646e616d656553696d6f6e6a6f636375706174696f6e74536b79646976696e672'
    ... b'0496e7374727563746f7268686f6d6570616765782368747470733a2f2f6578616d706c652e636f'
    ... b'6d2f6c657473676f736b79646976696e67')
    >>> schema = PersonSchema()
    >>> hexlify(schema.dumps(person)) == expected
    True
    """

    name = fields.String()
    occupation = fields.String()
    homepage = fields.Url()
