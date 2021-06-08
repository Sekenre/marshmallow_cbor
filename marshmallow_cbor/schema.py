import cbor2
from marshmallow import Schema as mSchema
from marshmallow import SchemaOpts, post_dump, post_load, pre_dump, pre_load
from marshmallow.validate import ValidationError


class TagHandler:
    def loads(self, data, **kwargs):
        kwargs['tag_hook'] = self._tag_hook
        return cbor2.loads(data, **kwargs)

    def dumps(self, data, **kwargs):
        return cbor2.dumps(data, **kwargs)

    @staticmethod
    def _tag_hook(decoder, tag, **kwargs):
        return {'__cbortag': tag.tag, '__value': tag.value}


class CBOROptions(SchemaOpts):
    def __init__(self, meta, **kwargs):
        SchemaOpts.__init__(self, meta, **kwargs)
        self.tag = getattr(meta, "tag", None)
        self.embed = getattr(meta, "embed", False)
        self.embed_first = getattr(meta, "embed_first", True)
        self.render_module = TagHandler()


class Schema(mSchema):
    OPTIONS_CLASS = CBOROptions

    def _deserialize(self, data, many, **kwargs):
        print('deserialize called with:', data, many, kwargs)
        if isinstance(data, dict) and data.get('__cbortag', 0) == self.opts.tag:
            data = data.get('__value', {})
        elif isinstance(data, cbor2.CBORTag) and data.tag == self.opts.tag:
            data = data.value
        return super()._deserialize(data, many=many, **kwargs)

    def _serialize(self, value, many, **kwargs):
        value = super()._serialize(value, many=many, **kwargs)
        if self.opts.tag:
            value = cbor2.CBORTag(self.opts.tag, value.get('payload', value))
        return value
