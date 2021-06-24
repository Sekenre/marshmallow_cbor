"""
Experimenting with European Digital Covid Certificate
Test data from:
    https://github.com/eu-digital-green-certificates/dgc-testdata/blob/main/IE/2DCode/Raw/1.json
Schema: https://github.com/ehn-dcc-development/ehn-dcc-schema
Specification:
    https://github.com/ehn-dcc-development/hcert-spec/blob/main/hcert_spec.md

>>> test_data = ('NCFE70X90T9WTWGVLKX49LDA:4NX35 CPX*42BB3XK2F3U7PF9I2F3Z:N3 Q6JC X'
...    '8Y50.FK6ZK7:EDOLFVC*70B$D% D3IA4W5646946846.966KCN9E%961A6DL6FA7D46XJCCWENF'
...    '6OF63W5NW6C46WJCT3E$B9WJC0FDTA6AIA%G7X+AQB9746QG7$X8SW6/TC4VCHA7LB7$471S6N-'
...    'COA7X577:6 47F-CZIC6UCF%6AK4.JCP9EJY8L/5M/5546.96VF6%JCJQEK69WY8KQEPD09WEQD'
...    'D+Q6TW6FA7C46TPCBEC8ZKW.C8WE7H801AY09ZJC2/D*H8Y3EN3DMPCG/DOUCNB8WY8I3DOUCCE'
...    'CZ CO/EZKEZ964461S6GVC*JC1A6$473W59%6D4627BPFL .4/FQQRJ/2519D+9D831UT8D4KB8'
...    '2JP63-G$C4/1B2SMHXDW2V:CSU6NJIO4U0-T6573C+DM-FARF9.3KMF+PVCBD$%K-4PKOE')
>>> import base45
>>> import zlib
>>> import datetime
>>> result = base45.b45decode(test_data)
>>> decompressed = zlib.decompress(result)
>>> expected = {
...     'header': {'alg': '065178b6cf2835c8', 'kid': -7},
...     'payload': {
...         'exp': datetime.datetime(2021, 6, 14, 9, 0, tzinfo=datetime.timezone.utc),
...         'hcert': {
...             'date_of_birth': datetime.date(1988, 6, 7),
...             'personal_name': {
...                 'family_name': 'Bloggs',
...                 'family_name_std': 'BLOGGS',
...                 'given_name': 'Jane',
...                 'given_name_std': 'JANE',
...             },
...             'vaccine_records': [
...                 {
...                     'certificate_id': 'URN:UVCI:01:IE:52d0dc929c884cf8998a7987f0b9d863#2',
...                     'country': 'IE',
...                     'date': datetime.date(2021, 5, 6),
...                     'dose_series': 2,
...                     'doses': 1,
...                     'issuer': 'HSE',
...                     'manufacturer': 'ORG-100030215',
...                     'product': 'EU/1/20/1528',
...                     'target': '840539006',
...                     'vaccine': '1119349007',
...                 }
...             ],
...             'version': '1.0.4',
...         },
...         'iat': datetime.datetime(2021, 6, 7, 7, 46, 28, tzinfo=datetime.timezone.utc),
...         'iss': 'IE',
...     },
...     'signature': ('a8d9272ad0789b242812686b68920878447f9ef5114533ee85c821e5575bb2f46cb'
...                   '3f5b1dfc4b71bc115054a34b818fb6de97df27b701f267a99f9c468d0a507'),
... }
>>> schema = SignedDCCSchema()
>>> expected == schema.loads(decompressed)
True

"""
import cbor2
from marshmallow import pre_load

from marshmallow_cbor import Schema, fields


class PersonalName(Schema):
    family_name = fields.String(data_key='fn')
    family_name_std = fields.String(data_key='fnt')
    given_name = fields.String(data_key='gn')
    given_name_std = fields.String(data_key='gnt')


class VaccineRecord(Schema):
    target = fields.String(data_key='tg')
    vaccine = fields.String(data_key='vp')
    product = fields.String(data_key='mp')
    manufacturer = fields.String(data_key='ma')
    doses = fields.Integer(data_key='dn')
    dose_series = fields.Integer(data_key='sd')
    date = fields.Date(data_key='dt')
    country = fields.String(data_key='co')
    issuer = fields.String(data_key='is')
    certificate_id = fields.String(data_key='ci')


class DigitalCovidCertSchema(Schema):
    version = fields.String(data_key='ver')
    personal_name = fields.Nested(PersonalName, data_key='nam')
    date_of_birth = fields.Date(data_key='dob')
    vaccine_records = fields.Nested(VaccineRecord, data_key='v', many=True)

    @pre_load
    def unwrap(self, in_data, **kwargs):
        return in_data[1]


class CWTClaims(Schema):
    iss = fields.Raw(data_key=1)
    sub = fields.String(data_key=2)
    aud = fields.Raw(data_key=3)
    exp = fields.Timestamp(data_key=4)
    nbf = fields.Timestamp(data_key=5)
    iat = fields.Timestamp(data_key=6)
    cti = fields.Bytes(data_key=7, load_as='hex')
    hcert = fields.Nested(DigitalCovidCertSchema, data_key=-260)


class CWTHeader(Schema):
    alg = fields.Bytes(data_key=4, load_as='hex')
    kid = fields.Integer(data_key=1)


class SignedDCCSchema(Schema):
    header = fields.Embedded(fields.Nested(CWTHeader))
    payload = fields.Embedded(fields.Nested(CWTClaims))
    signature = fields.Bytes(load_as='hex')

    def _deserialize(self, data, **kwargs):
        if isinstance(data, cbor2.CBORTag):
            if data.tag == 18:
                data = data.value
        dikt = dict(header=data[0], payload=data[2], signature=data[3])
        return super()._deserialize(dikt, **kwargs)
