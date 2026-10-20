from django.db import IntegrityError, transaction
from django.http import Http404

from .dao import StudentDAO, StudyGroupDAO
from .forms import StudentForm, StudyGroupForm


class FormResourceService:
    dao_class = None
    form_class = None

    def __init__(self):
        self.dao = self.dao_class()

    def get_all(self):
        return self.dao.get_all()

    def get_by_id(self, item_id):
        instance = self.dao.get_by_id(item_id)
        if instance is None:
            raise Http404('Запись не найдена.')
        return instance

    def get_form(self, payload=None, item_id=None):
        instance = self.get_by_id(item_id) if item_id is not None else None
        return self.form_class(data=payload, instance=instance)

    def save(self, form):
        if not form.is_valid():
            return False
        try:
            with transaction.atomic():
                self.dao.save(form.save(commit=False))
        except IntegrityError:
            form.add_error(None, 'Запись не сохранена: проверьте уникальность и значения полей.')
            return False
        return True

    def delete(self, item_id):
        self.dao.delete(self.get_by_id(item_id))


class StudentFormService(FormResourceService):
    dao_class = StudentDAO
    form_class = StudentForm


class StudyGroupFormService(FormResourceService):
    dao_class = StudyGroupDAO
    form_class = StudyGroupForm
