import uuid
from datetime import datetime

import cbor2
from marshmallow import fields as m_fields


# Fields for custom tags (not handled natively by cbor2)


class NestedTagged(m_fields.Nested):
    def __init__(self, schema, *, tag=None, **kwargs):
        super().__init__(schema, **kwargs)
        self._tag = tag

    def _serialize(self, nested_obj, attr, obj, **kwargs):
        serialized = super()._serialize(nested_obj, attr, obj, **kwargs)
        if self._tag is not None:
            return cbor2.CBORTag(self._tag, serialized)
        else:
            return serialized

    def _deserialize(self, value, attr, data, partial=None, **kwargs):
        if isinstance(value, cbor2.CBORTag):
            if value.tag == self._tag:
                value = value.value
            else:
                raise ValueError
        if isinstance(value, dict):
            if value.get('__cbortag', -1) == self._tag:
                value = value.get('__value', None)
        return super()._deserialize(value, attr, data, partial, **kwargs)


class NestedEmbedded(m_fields.Nested):
    def _serialize(self, nested_obj, attr, obj, **kwargs):
        serialized = super()._serialize(nested_obj, attr, obj, **kwargs)
        return cbor2.dumps(serialized)

    def _deserialize(self, value, attr, data, partial=None, **kwargs):
        if isinstance(value, bytes):
            value = cbor2.loads(value)
        return super()._deserialize(value, attr, data, partial, **kwargs)


# Native CBOR fields that can just be passed through


class AwareDateTime(m_fields.AwareDateTime):
    def _serialize(self, value, attr, obj, **kwargs):
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, datetime):
            return value
        else:
            return super()._deserialize(value, attr, data, **kwargs)


class UUID(m_fields.UUID):
    def _serialize(self, value, attr, obj, **kwargs):
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, uuid.UUID):
            return value
        else:
            return super()._deserialize(value, attr, data, **kwargs)


# Unchanged fields from marshmallow

Field = m_fields.Field
Raw = m_fields.Raw
Nested = m_fields.Nested
Mapping = m_fields.Mapping
Dict = m_fields.Dict
List = m_fields.List
Tuple = m_fields.Tuple
String = m_fields.String
Number = m_fields.Number
Integer = m_fields.Integer
Decimal = m_fields.Decimal
Boolean = m_fields.Boolean
Float = m_fields.Float
Time = m_fields.Time
Date = m_fields.Date
TimeDelta = m_fields.TimeDelta
Url = m_fields.Url
URL = m_fields.URL
Email = m_fields.Email
IP = m_fields.IP
IPv4 = m_fields.IPv4
IPv6 = m_fields.IPv6
IPInterface = m_fields.IPInterface
IPv4Interface = m_fields.IPv4Interface
IPv6Interface = m_fields.IPv6Interface
Method = m_fields.Method
Function = m_fields.Function
Str = m_fields.Str
Bool = m_fields.Bool
Int = m_fields.Int
Constant = m_fields.Constant
Pluck = m_fields.Pluck
