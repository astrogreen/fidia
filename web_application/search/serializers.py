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


class NameResolver(serializers.Serializer):
    name = serializers.CharField(max_length=256)


class FilterById(serializers.Serializer):
    id = serializers.CharField(max_length=256, required=True, label="ID*")


class FilterByName(serializers.Serializer):
    name = serializers.CharField(max_length=256, required=True, label="Name*")


class FilterByPosition(serializers.Serializer):
    ra = serializers.RegexField(hre.RA_RE.pattern, required=True, label="RA*")
    dec = serializers.RegexField(hre.DEC_RE.pattern, required=True, label="Dec*")
    radius = serializers.FloatField(required=False, label="Radius (arcsec)", default=3)
