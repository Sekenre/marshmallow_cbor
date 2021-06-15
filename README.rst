marshmallow for CBOR (RFC 8949)
###############################

This module allows serializing and deserializing `marshmallow`_ schemas as `CBOR`_
data. `CBOR`_ is a compact binary data format similar to JSON in it's data model,
but supporting many more datatypes and an extensible tag system. `marshmallow`_ 
out of the box only supports serialization to JSON.

.. _marshmallow: https://marshmallow.readthedocs.io/en/stable/index.html
.. _CBOR: https://cbor.io


Install
=======

::

    pip install marshmallow-cbor


Examples
========

Please see the ``examples/`` folder in this repository.

* `Plain string keys & values, regular marshmallow validation <examples/person.py>`_
* `CBOR Tagged item schemas <examples/tags.py>`_
* `CWT (RFC 8392) token validation <examples/cwt.py>`_


TODO
====

* Add marshmallow DateTime fields back in as string only fields
* Tag single items in addition to schemas and nested schemas ✅
* Field support for all cbor2 supported datatypes ✅(partial)
* Add it to PyPI ✅
