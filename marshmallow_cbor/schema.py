import cbor2
from marshmallow import Schema as mSchema, SchemaOpts, post_dump, pre_load


class CBOROptions(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.tag = getattr(meta, "tag", None)
        self.embed = getattr(meta, "embed", False)
        self.render_module = cbor2


class Schema(mSchema):
    OPTIONS_CLASS = CBOROptions

    @post_dump
    def wrap_tag(self, data, many, **kwargs):
        if self.opts.embed:
            data = cbor2.dumps(data)
        if self.opts.tag:
            return cbor2.CBORTag(self.opts.tag, data)
        else:
            return data

    @pre_load
    def unwrap_tag(self, tag, many, **kwargs):
        if self.opts.tag is not None:
            if tag.tag == self.opts.tag:
                data = tag.value
            else:
                raise ValueError
        else:
            data = tag
        if self.opts.embed:
            data = cbor2.loads(data)
        return data

