from rest_framework import serializers
import support.models


class ContactSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=100)
    email = serializers.EmailField(required=True, max_length=100)
    message = serializers.CharField(max_length=10000, required=True)
    contact_complex_question = serializers.IntegerField(
        required=True, label="Solve this simple problem and enter the result.*", write_only=True
    )

    def validate_contact_complex_question(self, value):
        if value is not 3:
            raise serializers.ValidationError("Validation failed. Are you a robot?")
        return value

    def create(self, validated_data):
        # on save

        # remove spam honeypot field
        if "contact_complex_question" in validated_data:
            del validated_data["contact_complex_question"]
        return support.models.Contact.objects.create(**validated_data)

    def to_representation(self, obj):
        # on model instance ==> representation (after create, instance
        # is sent back to user)

        # get the original representation
        ret = super(ContactSerializer, self).to_representation(obj)

        # remove the honeypot field from the representation
        if "contact_complex_question" in ret:
            del ret["contact_complex_question"]

        # return the modified representation
        return ret

    class Meta:
        model = support.models.Contact
        fields = ('name', 'email', 'message', 'complex_question')
        # extra_kwargs = {'complex_question': {'write_only': True}}
