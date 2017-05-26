from rest_framework import serializers, mixins, status
import search.helpers.regex as hre


class AstroObjectList(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=256)
    owner = serializers.CharField(max_length=256)
    surveys = serializers.ListField(max_length=256)
    status = serializers.ListField(max_length=256)
    position = serializers.DictField()
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        _id = obj.id
        try:
            _id = self.context['request'].build_absolute_uri(str(obj.id))
        except Exception:
            pass
        return _id


class AstroObjectRetrieve(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=256)
    owner = serializers.CharField(max_length=256)
    surveys = serializers.ListField(max_length=256)
    status = serializers.ListField(max_length=256)
    position = serializers.DictField()


class FilterBy(serializers.Serializer):
    urls = serializers.ListField(max_length=256, read_only=True)


class FilterById(serializers.Serializer):
    id = serializers.CharField(max_length=256, required=True, label="ID*")


class FilterByName(serializers.Serializer):
    name = serializers.CharField(max_length=256, required=True, label="Name*")


class FilterByPosition(serializers.Serializer):
    ra = serializers.RegexField(hre.RA_RE.pattern, required=True, label="RA*", initial='184.899719198317')
    dec = serializers.RegexField(hre.DEC_RE.pattern, required=True, label="Dec*", initial='0.745403840164056')
    radius = serializers.FloatField(required=False, label="Radius (arcsec)", default=3, initial='300')


class NameResolver(serializers.Serializer):
    name = serializers.CharField(max_length=256)
