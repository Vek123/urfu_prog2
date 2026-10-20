from typing import ClassVar
from calendar import isleap
from math import isfinite

from django.conf import settings
from rest_framework import serializers

from .enums import Positions, Systems
from .util import DateTimeUtil


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


class SystemsField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        choices = [system.value for system in Systems
                   if system != Systems.SERVICE1
                   or settings.FEEDBACK_ALLOW_SERVICE_SYSTEM]
        super().__init__(choices=choices, **kwargs)

    def to_internal_value(self, data):
        return Systems(super().to_internal_value(data))


class PositionField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        super().__init__(choices=[position.value for position in Positions], **kwargs)

    def to_internal_value(self, data):
        return Positions(super().to_internal_value(data))


class StrictFloatField(serializers.FloatField):
    default_error_messages: ClassVar = {'invalid': 'ожидается конечное JSON-число'}

    def to_internal_value(self, data):
        if type(data) not in (int, float):
            self.fail('invalid')
        value = super().to_internal_value(data)
        if not isfinite(value):
            self.fail('invalid')
        return value


class FeedbackRequestSerializer(serializers.Serializer):
    uid = StrictCharField(max_length=32, trim_whitespace=False)
    operationUid = StrictCharField(max_length=32, trim_whitespace=False)
    systemTime = StrictCharField(trim_whitespace=False)
    communicationId = StrictIntegerField(min_value=1, max_value=100000)
    position = PositionField()
    salary = StrictFloatField(min_value=0)
    bonus = StrictFloatField(min_value=0)
    workDays = StrictIntegerField(min_value=1, max_value=366)
    year = StrictIntegerField(min_value=1, max_value=9999,
                              default=DateTimeUtil.current_year)
    systemName = SystemsField(required=False, allow_null=True)
    source = StrictCharField(required=False, allow_null=True,
                             allow_blank=True, trim_whitespace=False)
    templateId = StrictIntegerField(default=0, min_value=-(2**31), max_value=2**31-1)
    productCode = StrictIntegerField(default=0, min_value=-(2**31), max_value=2**31-1)
    smsCode = StrictIntegerField(default=0, min_value=-(2**31), max_value=2**31-1)

    def validate(self, attrs):
        days = 366 if isleap(attrs['year']) else 365
        if attrs['workDays'] > days:
            raise serializers.ValidationError({
                'workDays': f'в {attrs["year"]} году не больше {days} дней'})
        return attrs


class FeedbackResponseSerializer(serializers.Serializer):
    uid = serializers.CharField(allow_blank=True)
    operationUid = serializers.CharField(allow_blank=True)
    systemTime = serializers.CharField()
    code = serializers.CharField()
    errorCode = serializers.CharField(allow_blank=True)
    errorMessage = serializers.SerializerMethodField()
    annualBonus = serializers.FloatField(allow_null=True)
    quarterlyBonus = serializers.FloatField(allow_null=True)

    def get_errorMessage(self, instance):
        message = instance.errorMessage.value
        if instance.errorDetails:
            return f'{message}: {instance.errorDetails}'
        return message
