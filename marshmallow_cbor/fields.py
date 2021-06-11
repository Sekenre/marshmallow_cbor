import ipaddress
import uuid
from calendar import timegm
from datetime import datetime, timezone

import cbor2
from marshmallow import fields as m_fields, utils


# Fields for custom tags (not handled natively by cbor2)


class Tagged(m_fields.Field):
    default_error_messages = {'wrong_tag': 'unexpected tag'}

    def __init__(self, tagged_field, *, tag, **kwargs):
        if not isinstance(tag, int) or tag < 0:
            raise ValueError('tag must be an int > 0')
        self._tagged_field = tagged_field
        self._tag = tag
        super().__init__(**kwargs)

    def _serialize(self, nested_obj, attr, obj, **kwargs):
        serialized = self._tagged_field._serialize(nested_obj, attr, obj, **kwargs)
        return cbor2.CBORTag(self._tag, serialized)

    def _deserialize(self, value, attr, data, partial=None, **kwargs):
        if isinstance(value, cbor2.CBORTag):
            if value.tag == self._tag:
                value = value.value
            else:
                self.make_error('wrong_tag', input=value)
        return self._tagged_field._deserialize(
            value, attr, data, partial=partial, **kwargs
        )


class Embedded(m_fields.Field):
    def __init__(self, embedded_field, **kwargs):
        self._embedded_field = embedded_field
        super().__init__(**kwargs)

    def _serialize(self, nested_obj, attr, obj, **kwargs):
        serialized = self._embedded_field._serialize(nested_obj, attr, obj, **kwargs)
        return cbor2.dumps(serialized)

    def _deserialize(self, value, attr, data, partial=None, **kwargs):
        if isinstance(value, bytes):
            value = cbor2.loads(value)
        return self._embedded_field._deserialize(
            value, attr, data, partial=partial, **kwargs
        )


# Native CBOR fields that can just be passed through


class Timestamp(m_fields.AwareDateTime):
    """Unix epoch seconds in UTC.

    If you want it to be on the wire as an CBOR Tagged timestamp use
    fields.Tagged(Timestamp(), tag=1)
    """

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, datetime):
            if not value.microsecond:
                return timegm(value.utctimetuple())
            else:
                return timegm(value.utctimetuple()) + value.microsecond / 1000000
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, datetime):
            return value
        elif isinstance(value, str):
            return super()._deserialize(value, attr, data, **kwargs)
        else:
            return datetime.fromtimestamp(value, tz=timezone.utc)


class AwareDateTime(m_fields.AwareDateTime):
    _serialize = m_fields.Field._serialize

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, datetime):
            return value
        else:
            return super()._deserialize(value, attr, data, **kwargs)


class UUID(m_fields.UUID):
    _serialize = m_fields.Field._serialize

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, uuid.UUID):
            return value
        else:
            return super()._deserialize(value, attr, data, **kwargs)


class IP(m_fields.IP):
    _serialize = m_fields.Field._serialize

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, self.DESERIALIZATION_CLASS):
            return value
        else:
            return super()._deserialize(value, attr, data, **kwargs)


IPv4 = type('IPv4', (m_fields.IPv4, IP), {})
IPv6 = type('IPv6', (m_fields.IPv6, IP), {})
IPv4Interface = m_fields.IPv4Interface
IPv6Interface = m_fields.IPv6Interface


class IPNetwork(m_fields.Field):
    default_error_messages = {"invalid_ip_network": "Not a valid IP Network."}

    DESERIALIZATION_CLASS = None

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        if isinstance(value, self.DESERIALIZATION_CLASS):
            return value
        try:
            return (self.DESERIALIZATION_CLASS or ipaddress.ip_interface)(
                utils.ensure_text_type(value)
            )
        except (ValueError, TypeError) as error:
            raise self.make_error("invalid_ip_network") from error


class IPv4Network(IPNetwork):
    """A IPv4 Network field. (without the host part)"""

    default_error_messages = {"invalid_ip_network": "Not a valid IPv4 network."}

    DESERIALIZATION_CLASS = ipaddress.IPv4Network


class IPv6Network(IPNetwork):
    """A IPv6 Network field. (without the host part)"""

    default_error_messages = {"invalid_ip_network": "Not a valid IPv6 network."}

    DESERIALIZATION_CLASS = ipaddress.IPv6Network


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
Method = m_fields.Method
Function = m_fields.Function
Str = m_fields.Str
Bool = m_fields.Bool
Int = m_fields.Int
Constant = m_fields.Constant
Pluck = m_fields.Pluck
