from abc import ABC, abstractmethod

from .models import Discipline, Student, StudyGroup


class ResourceDAO(ABC):
    @abstractmethod
    def get_all(self):
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, item_id):
        raise NotImplementedError

    @abstractmethod
    def save(self, instance):
        raise NotImplementedError

    @abstractmethod
    def delete(self, instance):
        raise NotImplementedError


class DjangoResourceDAO(ResourceDAO):
    model = None

    def get_all(self):
        return self.model.objects.order_by('id')

    def get_by_id(self, item_id):
        return self.model.objects.filter(pk=item_id).first()

    def save(self, instance):
        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()


class StudentDAO(DjangoResourceDAO):
    model = Student


class DisciplineDAO(DjangoResourceDAO):
    model = Discipline


class StudyGroupDAO(DjangoResourceDAO):
    model = StudyGroup
