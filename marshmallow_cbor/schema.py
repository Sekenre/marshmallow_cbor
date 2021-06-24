import cbor2
from marshmallow import Schema as mSchema, SchemaOpts
from marshmallow.validate import ValidationError


class CBOROptions(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.tag = getattr(meta, "tag", None)
        self.render_module = cbor2


class Schema(mSchema):
    OPTIONS_CLASS = CBOROptions

    def _deserialize(self, data, many, **kwargs):
        if isinstance(data, cbor2.CBORTag):
            if data.tag == self.opts.tag:
                data = data.value
            else:
                raise ValidationError(f'unexpected tag: {data.tag}')
        return super()._deserialize(data, many=many, **kwargs)

    def _serialize(self, value, many, **kwargs):
        value = super()._serialize(value, many=many, **kwargs)
        if self.opts.tag and not many:
            value = cbor2.CBORTag(self.opts.tag, value)
        return value
