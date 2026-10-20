from rest_framework import serializers

from .models import Discipline, Student


class StrictIntegerField(serializers.IntegerField):
    def to_internal_value(self, data):
        if type(data) is not int:
            raise serializers.ValidationError('Ожидается целое JSON-число.')
        return super().to_internal_value(data)


class StrictCharField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise serializers.ValidationError('Ожидается строка.')
        return super().to_internal_value(data)


class StudentSerializer(serializers.ModelSerializer):
    name = StrictCharField(max_length=15)
    surname = StrictCharField(max_length=25)
    faculty = StrictCharField(max_length=20)
    age = StrictIntegerField(min_value=1, max_value=120)

    class Meta:
        model = Student
        fields = ('id', 'name', 'surname', 'faculty', 'age')
        read_only_fields = ('id',)


class StudentUpdateSerializer(StudentSerializer):
    id = StrictIntegerField(min_value=1)


class DisciplineSerializer(serializers.ModelSerializer):
    name = StrictCharField(max_length=100)
    faculty = StrictCharField(max_length=20)
    hours = StrictIntegerField(min_value=1, max_value=10000)

    class Meta:
        model = Discipline
        fields = ('id', 'name', 'faculty', 'hours')
        read_only_fields = ('id',)


class DisciplineUpdateSerializer(DisciplineSerializer):
    id = StrictIntegerField(min_value=1)
