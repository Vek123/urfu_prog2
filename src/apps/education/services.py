from rest_framework.exceptions import NotFound

from .dao import DisciplineDAO, StudentDAO
from .serializers import (DisciplineSerializer, DisciplineUpdateSerializer,
                          StudentSerializer, StudentUpdateSerializer)


class ResourceService:
    dao_class = None
    serializer_class = None
    update_serializer_class = None
    label = 'Запись'

    def __init__(self, dao=None):
        self.dao = dao if dao is not None else self.dao_class()

    def get_all(self):
        return self.serializer_class(self.dao.get_all(), many=True).data

    def get_by_id(self, item_id):
        return self.serializer_class(self._find(item_id)).data

    def create(self, payload):
        serializer = self.serializer_class(data=payload)
        serializer.is_valid(raise_exception=True)
        instance = self.dao.model(**serializer.validated_data)
        return self.serializer_class(self.dao.save(instance)).data

    def update(self, payload):
        serializer = self.update_serializer_class(data=payload)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        instance = self._find(values.pop('id'))
        for name, value in values.items():
            setattr(instance, name, value)
        return self.serializer_class(self.dao.save(instance)).data

    def delete(self, item_id):
        instance = self._find(item_id)
        self.dao.delete(instance)
        return {'id': item_id}

    def _find(self, item_id):
        instance = self.dao.get_by_id(item_id)
        if instance is None:
            raise NotFound(f'{self.label} с id={item_id} не найдена.')
        return instance


class StudentService(ResourceService):
    dao_class = StudentDAO
    serializer_class = StudentSerializer
    update_serializer_class = StudentUpdateSerializer
    label = 'Запись студента'


class DisciplineService(ResourceService):
    dao_class = DisciplineDAO
    serializer_class = DisciplineSerializer
    update_serializer_class = DisciplineUpdateSerializer
    label = 'Учебная дисциплина'
