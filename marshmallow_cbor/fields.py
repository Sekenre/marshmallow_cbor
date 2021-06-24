import binascii
import ipaddress
import uuid
from calendar import timegm
from datetime import datetime, timezone

from cbor2 import CBORSimpleValue, CBORTag, dumps, loads
from marshmallow import fields as m_fields, utils


# Fields for custom tags (not handled natively by cbor2)


class Tagged(m_fields.Field):
    """Wrap a field in a CBOR Tag

    :param tagged_field: Any field instance including ``fields.Nested`` schemas
    :param tag: Tag ID.
    """

    default_error_messages = {'wrong_tag': 'unexpected tag'}

    def __init__(self, tagged_field, *, tag, **kwargs):
        if not isinstance(tag, int) or tag < 0:
            raise ValueError('tag must be an int > 0')
        self._tagged_field = tagged_field
        self._tag = tag
        super().__init__(**kwargs)

    def _serialize(self, nested_obj, attr, obj, **kwargs):
        serialized = self._tagged_field._serialize(nested_obj, attr, obj, **kwargs)
        return CBORTag(self._tag, serialized)

    def _deserialize(self, value, attr, data, partial=None, **kwargs):
        if isinstance(value, CBORTag):
            if value.tag == self._tag:
                value = value.value
            else:
                self.make_error('wrong_tag', input=value)
        return self._tagged_field._deserialize(
            value, attr, data, partial=partial, **kwargs
        )


class Embedded(m_fields.Field):
    """Serialize a field as CBOR bytes

    :param embedded_field: Any field instance including ``fields.Nested`` schemas
    """

    def __init__(self, embedded_field, **kwargs):
        self._embedded_field = embedded_field
        super().__init__(**kwargs)

    def _serialize(self, nested_obj, attr, obj, **kwargs):
        serialized = self._embedded_field._serialize(nested_obj, attr, obj, **kwargs)
        return dumps(serialized)

    def _deserialize(self, value, attr, data, partial=None, **kwargs):
        if isinstance(value, bytes):
            value = loads(value)
        return self._embedded_field._deserialize(
            value, attr, data, partial=partial, **kwargs
        )


# Native CBOR fields that can just be passed through


class Bytes(m_fields.Field):
    """Instead of using Python's raw bytes type to represent CBOR bytes
    we can chose to load them as strings. If you don't want to interpret
    bytes objects just use ``fields.Raw()`` instead.

    :param load_as: String representation of bytes object
    """

    LOAD_AS = {
        None: lambda x: x,
        'hex': lambda x: binascii.hexlify(x).decode(),
        'utf8': lambda x: x.decode('utf-8', errors='backslashreplace'),
    }
    DUMP_AS = {
        None: lambda x: x,
        'hex': lambda x: binascii.unhexlify(x),
        'utf8': lambda x: x.encode('utf-8'),
    }

    def __init__(self, *, load_as=None, **kwargs):
        try:
            self._load_func = self.LOAD_AS[load_as]
            self._dump_func = self.DUMP_AS[load_as]
        except KeyError:
            raise ValueError(f'unsupported bytes representation {load_as}')
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        return self._dump_func(value)

    def _deserialize(self, value, attr, data, **kwargs):
        return self._load_func(value)


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
    """
    Passes timezone aware fields directly to cbor encoder to be written as ISO
    tagged timestamp strings.
    """

    _serialize = m_fields.Field._serialize

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, datetime):
            return value
        else:
            return super()._deserialize(value, attr, data, **kwargs)


class UUID(m_fields.UUID):
    """
    Passes UUID fields directly to cbor encoder to be written as tagged UUID in
    bytes form.
    """

    _serialize = m_fields.Field._serialize

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, uuid.UUID):
            return value
        else:
            return super()._deserialize(value, attr, data, **kwargs)


class IP(m_fields.IP):
    """
    Passes IP fields directly to cbor encoder to be written as tagged IP in
    bytes form.
    """

    _serialize = m_fields.Field._serialize

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, self.DESERIALIZATION_CLASS):
            return value
        else:
            return super()._deserialize(value, attr, data, **kwargs)


# Wrap the marshmallow IP deserialization with our passthrough IP class.
IPv4 = type('IPv4', (m_fields.IPv4, IP), {})
IPv6 = type('IPv6', (m_fields.IPv6, IP), {})

# Non-strict ipv4 interface passed as strings as marshmallow normally.
IPv4Interface = m_fields.IPv4Interface
IPv6Interface = m_fields.IPv6Interface


class IPNetwork(m_fields.Field):
    """
    Passes IP network fields directly to cbor encoder to be written as tagged items
    in bytes form. This is the strict kind of network address where the host part
    is not allowed.
    """

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


# Fields specific to CBOR


class SimpleValue(m_fields.Field):
    """
    CBOR Simple Value (positive integer between 0 and 255)
    """

    default_error_messages = {"simple": "Not a CBOR Simple Value"}

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, CBORSimpleValue):
            return value
        else:
            return CBORSimpleValue(value)

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, CBORSimpleValue):
            return value
        else:
            raise self._make_error("simple")


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
DateTime = m_fields.DateTime
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
