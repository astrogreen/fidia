from rest_framework import serializers, mixins, status
import search.helpers.regex as hre


class AstroObjectList(serializers.Serializer):
    adcid = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=256)
    survey = serializers.CharField(max_length=256)
    surveys = serializers.ListField(max_length=256)
    status = serializers.ListField(max_length=256)
    position = serializers.DictField()
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        _adcid = obj.adcid
        try:
            _adcid = self.context['request'].build_absolute_uri(str(obj.adcid))
        except Exception:
            pass
        return _adcid


class AstroObjectRetrieve(serializers.Serializer):
    adcid = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=256)
    survey = serializers.CharField(max_length=256)
    surveys = serializers.ListField(max_length=256)
    status = serializers.ListField(max_length=256)
    position = serializers.DictField()

class FilterBy(serializers.Serializer):
    urls = serializers.ListField(max_length=256, read_only=True)


class FilterByADCID(serializers.Serializer):
    adcid = serializers.CharField(max_length=256, required=True, label="ADCID*")


class FilterByName(serializers.Serializer):
    name = serializers.CharField(max_length=256, required=True, label="Name*")


class FilterBySurvey(serializers.Serializer):
    survey = serializers.CharField(max_length=256, required=True, label="Survey*")


class FilterByPosition(serializers.Serializer):
    ra = serializers.RegexField(hre.RA_RE.pattern, required=True, label="RA*", initial='184.899719198317')
    dec = serializers.RegexField(hre.DEC_RE.pattern, required=True, label="Dec*", initial='0.745403840164056')
    radius = serializers.FloatField(required=False, label="Radius (arcsec)", default=3, initial='300')
    equinox = serializers.ChoiceField(choices=[('J2000', 'J2000'), ('B1950', 'B1950')], allow_blank=False)


class NameResolver(serializers.Serializer):
    name = serializers.CharField(max_length=256)


class AOListByName(AstroObjectList):
    pass


class AOListBySurvey(AstroObjectList):
    pass


class AOListByADCID(AstroObjectList):
    pass


class AOListByPosition(AstroObjectList):
    separation = serializers.CharField(max_length=256)
