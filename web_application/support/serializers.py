from rest_framework import serializers
import support.models


class SpamValidationSerializer(serializers.Serializer):
    """
    Spam validation serializer provides a 'honey pot' field
    that 
    """
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
        return self.Meta.model.objects.create(**validated_data)

    def to_representation(self, obj):
        # on model instance ==> representation (after create, instance
        # is sent back to user)

        # get the original representation
        ret = super(SpamValidationSerializer, self).to_representation(obj)

        # remove the honeypot field from the representation
        if "contact_complex_question" in ret:
            del ret["contact_complex_question"]

        # return the modified representation
        return ret


class ContactSerializer(SpamValidationSerializer):
    """
    Contact Form Serializer.
    """
    name = serializers.CharField(required=True, max_length=100)
    email = serializers.EmailField(required=True, max_length=100)
    message = serializers.CharField(max_length=10000, required=True)

    # contact_complex_question = serializers.IntegerField(
    #     required=True, label="Solve this simple problem and enter the result.*", write_only=True
    # )
    #
    # def validate_contact_complex_question(self, value):
    #     if value is not 3:
    #         raise serializers.ValidationError("Validation failed. Are you a robot?")
    #     return value
    #
    # def create(self, validated_data):
    #     # on save
    #
    #     # remove spam honeypot field
    #     if "contact_complex_question" in validated_data:
    #         del validated_data["contact_complex_question"]
    #     return support.models.Contact.objects.create(**validated_data)
    #
    # def to_representation(self, obj):
    #     # on model instance ==> representation (after create, instance
    #     # is sent back to user)
    #
    #     # get the original representation
    #     ret = super(ContactSerializer, self).to_representation(obj)
    #
    #     # remove the honeypot field from the representation
    #     if "contact_complex_question" in ret:
    #         del ret["contact_complex_question"]
    #
    #     # return the modified representation
    #     return ret

    class Meta:
        model = support.models.Contact
        fields = ('name', 'email', 'message', 'complex_question')


class BugReportSerializer(SpamValidationSerializer):
    """
    Bug Report Serializer.
    """
    message = serializers.CharField(
        max_length=10000, required=True, label="Message*",
        style={'placeholder': 'Please be as specific as possible when describing your issue.',
               'base_template': 'textarea.html', 'rows': 6}
    )
    url = serializers.CharField(required=False, label='URL (optional)', max_length=100,
                                style={'placeholder': 'e.g., /asvo/sov/'})
    name = serializers.CharField(max_length=100, required=True, label="Name*", style={'placeholder': 'Name'})
    email = serializers.EmailField(max_length=100, label="Email*", required=True, style={'placeholder': 'Email'})
    survey_team = serializers.ChoiceField(choices=support.models.BugReport.SURVEY_TEAM, default='NA')

    class Meta:
        model = support.models.BugReport
        fields = ('name', 'email', 'message', 'url', 'survey_team', 'complex_question')
