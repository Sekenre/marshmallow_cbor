import cbor2
from marshmallow import Schema as mSchema
from marshmallow import SchemaOpts, post_dump, post_load, pre_dump, pre_load
from marshmallow.validate import ValidationError


class CBOROptions(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.tag = getattr(meta, "tag", None)
        self.embed = getattr(meta, "embed", False)
        self.embed_first = getattr(meta, "embed_first", True)
        self.render_module = cbor2


class Schema(mSchema):
    OPTIONS_CLASS = CBOROptions

    @post_dump(pass_original=True)
    def embed(self, value, original, **kwargs):
        if self.opts.tag and self.opts.embed:
            if self.opts.embed_first:
                return cbor2.CBORTag(self.opts.tag, cbor2.dumps(value))
            else:
                value = cbor2.CBORTag(self.opts.tag, value)
                return cbor2.dumps(value)
        elif self.opts.tag:
            return cbor2.CBORTag(self.opts.tag, value)
        elif self.opts.embed:
            return cbor2.dumps(value)
        else:
            return value

    @pre_load
    def disembed(self, data, many, **kwargs):
        if self.opts.embed and isinstance(data, bytes):
            data = cbor2.loads(data)
        if self.opts.tag is not None and isinstance(data, cbor2.CBORTag):
            if data.tag == self.opts.tag:
                data = data.value
                if (
                    self.opts.embed
                    and self.opts.embed_first
                    and isinstance(data, bytes)
                ):
                    data = cbor2.loads(data)
            else:
                raise ValidationError('incorrect tag', data=data)
        return data
