from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from .form_services import StudentFormService, StudyGroupFormService

RESOURCES = {
    'students': {
        'service': StudentFormService, 'title': 'Студенты',
        'add_title': 'Добавление студента', 'edit_title': 'Изменение студента',
        'fields': ('name', 'surname', 'faculty', 'age'),
        'columns': ('Имя', 'Фамилия', 'Факультет', 'Возраст'),
        'prefix': 'web-student', 'id_parameter': 'studentId',
    },
    'groups': {
        'service': StudyGroupFormService, 'title': 'Учебные группы',
        'add_title': 'Добавление учебной группы', 'edit_title': 'Изменение учебной группы',
        'fields': ('name', 'faculty', 'course'),
        'columns': ('Номер группы', 'Факультет', 'Курс'),
        'prefix': 'web-group', 'id_parameter': 'groupId',
    },
}


def _identifier(value):
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        raise Http404('Некорректный идентификатор.')
    # Bound the string before int conversion to handle oversized query parameters.
    if len(value) > 19 or not 1 <= int(value) <= 2**63 - 1:
        raise Http404('Некорректный идентификатор.')
    return int(value)



@method_decorator(never_cache, name='dispatch')
class ResourceTemplateView(LoginRequiredMixin, TemplateView):
    kind = None
    http_method_names = ('get',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = RESOURCES[self.kind]
        context.update(config, kind=self.kind)
        context.update({action + '_url': 'education:' + config['prefix'] + '-' + action
                        for action in ('list', 'add', 'save', 'edit', 'delete')})
        return context


class ResourceListView(ResourceTemplateView):
    template_name = 'education/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instances = context['service']().get_all()
        context['rows'] = [
            {'id': instance.pk,
             'values': [getattr(instance, field) for field in context['fields']]}
            for instance in instances]
        return context


class ResourceAddView(ResourceTemplateView):
    template_name = 'education/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(form=context['service']().get_form(), title=context['add_title'])
        return context


class ResourceEditView(ResourceTemplateView):
    template_name = 'education/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item_id = _identifier(self.request.GET.get(context['id_parameter']))
        context.update(form=context['service']().get_form(item_id=item_id),
                       title=context['edit_title'], item_id=item_id)
        return context


class ResourceSaveView(ResourceTemplateView):
    template_name = 'education/form.html'
    http_method_names = ('post',)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        raw_id = request.POST.get('id', '')
        item_id = _identifier(raw_id) if raw_id else None
        service = context['service']()
        form = service.get_form(request.POST, item_id)
        if service.save(form):
            messages.success(request, 'Изменения сохранены.' if item_id else 'Запись добавлена.')
            return redirect(context['list_url'])
        context.update(form=form, item_id=item_id,
                       title=context['edit_title'] if item_id else context['add_title'])
        return self.render_to_response(context, status=400)


class ResourceDeleteView(ResourceTemplateView):
    http_method_names = ('post',)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        item_id = _identifier(request.POST.get(context['id_parameter']))
        context['service']().delete(item_id)
        messages.success(request, 'Запись удалена.')
        return redirect(context['list_url'])
