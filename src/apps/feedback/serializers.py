from typing import ClassVar

from rest_framework import serializers


class StrictCharField(serializers.CharField):
    default_error_messages: ClassVar = {
        'invalid': 'ожидается строка',
        'blank': 'обязательная непустая строка',
    }

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail('invalid')
        if not self.allow_blank and not data.strip():
            self.fail('blank')
        return super().to_internal_value(data)


class StrictIntegerField(serializers.IntegerField):
    default_error_messages: ClassVar = {'invalid': 'ожидается целое число'}

    def to_internal_value(self, data):
        if type(data) is not int:
            self.fail('invalid')
        return super().to_internal_value(data)


class FeedbackRequestSerializer(serializers.Serializer):
    uid = StrictCharField(max_length=32, trim_whitespace=False)
    operationUid = StrictCharField(max_length=32, trim_whitespace=False)
    systemTime = StrictCharField(trim_whitespace=False)
    communicationId = StrictIntegerField(min_value=1, max_value=100000)
    systemName = StrictCharField(required=False, allow_null=True,
                                 allow_blank=True, trim_whitespace=False)
    source = StrictCharField(required=False, allow_null=True,
                             allow_blank=True, trim_whitespace=False)
    templateId = StrictIntegerField(default=0, min_value=-(2**31), max_value=2**31-1)
    productCode = StrictIntegerField(default=0, min_value=-(2**31), max_value=2**31-1)
    smsCode = StrictIntegerField(default=0, min_value=-(2**31), max_value=2**31-1)


class FeedbackResponseSerializer(serializers.Serializer):
    uid = serializers.CharField(allow_blank=True)
    operationUid = serializers.CharField(allow_blank=True)
    systemTime = serializers.CharField()
    code = serializers.CharField()
    errorCode = serializers.CharField(allow_blank=True)
    errorMessage = serializers.CharField(allow_blank=True)
