import re

# "jpos": "01:12:02.23 +49:28:35.0",
#         "jradeg": "018.0093158",
#         "jdedeg": "+49.4763969",

RA_HOUR_RE = re.compile(r'(2[0-3]|1[0-9]|0?[0-9])')
RA_MIN_RE = re.compile(r'([0-5][0-9]|[0-9])')
RA_SEC_RE = re.compile(r'([0-5][0-9]|[0-9])')
RA_DEG_RE = re.compile(r'(3[0-5][0-9]|[0-2]?[0-9]?[0-9])')
RA_DECIMAL_RE = re.compile(r'(\.[0-9]+)?')

RA_RE = re.compile(
    r"""(({RA_HOUR_RE}(:{RA_MIN_RE})(:{RA_SEC_RE}))|{RA_DEG_RE}){RA_DECIMAL_RE}""".format(
        RA_HOUR_RE=RA_HOUR_RE.pattern, RA_MIN_RE=RA_MIN_RE.pattern, RA_SEC_RE=RA_SEC_RE.pattern,
        RA_DEG_RE=RA_DEG_RE.pattern, RA_DECIMAL_RE=RA_DECIMAL_RE.pattern)
)
# print(RA_RE.pattern)

PLUS_MINUS = re.compile(r'(-|\+)?')
DEC_DEG_RE = re.compile(r'([0-8][0-9]|[0-9])')
DEC_ARCMIN_RE = re.compile(r'(:0*([1-5][0-9]|[0-9]))')
DEC_ARCSEC_RE = re.compile(r'(:0*([1-5][0-9]|[0-9]))')
DEC_DECIMAL_RE = re.compile(r'(\.[0-9]+)?')

DEC_RE = re.compile(
    r"""({PLUS_MINUS}{DEC_DEG_RE})({DEC_ARCMIN_RE}{DEC_ARCSEC_RE})?{DEC_DECIMAL_RE}""".format(
        PLUS_MINUS=PLUS_MINUS.pattern, DEC_DEG_RE=DEC_DEG_RE.pattern, DEC_ARCMIN_RE=DEC_ARCMIN_RE.pattern,
        DEC_ARCSEC_RE=DEC_ARCSEC_RE.pattern, DEC_DECIMAL_RE=DEC_DECIMAL_RE.pattern))

# print(DEC_RE.pattern)

POSITION_RE = re.compile(
    r"""(?P<position>{RA_RE}(.){DEC_RE})""".format(RA_RE=RA_RE.pattern, DEC_RE=DEC_RE.pattern)
)

# RA_REGEX = "(((2[0-3]|1[0-9]|0?[0-9])(:(([0-5][0-9]|[0-9]))){2})|((3[0-5][0-9]|[0-2]?[0-9]?[0-9])))(\.[0-9]+)?"
# DEC_REGEX = '((-|\+)?([0-8][0-9]|[0-9]))((:0*([1-5][0-9]|[0-9])){2})?(\.[0-9]+)?'
# print(POSITION_RE.pattern)