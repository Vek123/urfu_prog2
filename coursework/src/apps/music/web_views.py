from decimal import Decimal
from typing import ClassVar

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView

from .access import admin_required, record, role_for, visible, writable
from .forms import (
    ArtistForm,
    CalculationForm,
    LoginForm,
    RegisterForm,
    RoleForm,
    SongForm,
)
from .models import UserAction, calculate_income
from .services import ArtistService, SongService, audit, register, set_role


def page(query, request, size=20):
    return Paginator(query, size).get_page(request.GET.get("page"))


@method_decorator(never_cache, name="dispatch")
class IndexView(TemplateView):
    template_name = "music/index.html"
    extra_context: ClassVar = {"title": "Музыкальный каталог"}


class AboutView(IndexView):
    template_name = "music/about.html"
    extra_context: ClassVar = {"title": "О приложении"}


@method_decorator(never_cache, name="dispatch")
class SecureView(LoginRequiredMixin, TemplateView):
    pass


class SongViewMixin:
    service_class = SongService
    form_class = SongForm
    title = "Песни"
    singular = "песни"
    list_url_name = "music:songs"
    add_url_name = "music:songs-add"
    edit_url_name = "music:songs-edit"
    delete_url_name = "music:songs-delete"
    help_text = (
        "Доступны исполнители владельца песни. Сначала добавьте исполнителя в его каталог. "
        "Ставка задаётся в рублях за одно прослушивание."
    )


class ArtistViewMixin:
    service_class = ArtistService
    form_class = ArtistForm
    title = "Исполнители"
    singular = "исполнителя"
    list_url_name = "music:artists"
    add_url_name = "music:artists-add"
    edit_url_name = "music:artists-edit"
    delete_url_name = "music:artists-delete"
    help_text = ""


class CatalogListView(SecureView):
    template_name = "music/list.html"
    columns = ()

    def get_queryset(self):
        return visible(self.service_class.model, self.request.user).select_related(
            "owner"
        )

    def get_row_values(self, item):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        current = page(self.get_queryset(), self.request)
        rows = [
            {
                "id": item.pk,
                "values": self.get_row_values(item),
                "edit_url": reverse(self.edit_url_name, args=[item.pk]),
                "delete_url": reverse(self.delete_url_name, args=[item.pk]),
            }
            for item in current
        ]
        return super().get_context_data(
            title=self.title,
            columns=self.columns,
            add_url=reverse(self.add_url_name),
            page_obj=current,
            rows=rows,
            **kwargs,
        )


class SongListView(SongViewMixin, CatalogListView):
    columns = (
        "Название",
        "Исполнитель",
        "Дата выпуска",
        "Прослушивания",
        "Ставка, ₽",
        "Доход, ₽",
        "Владелец",
    )

    def get_queryset(self):
        return super().get_queryset().select_related("artist")

    def get_row_values(self, item):
        return (
            item.title,
            item.artist.name,
            item.release_date or "—",
            item.streams,
            item.royalty_rate,
            item.income,
            item.owner.username,
        )


class ArtistListView(ArtistViewMixin, CatalogListView):
    columns = ("Имя", "Страна", "Описание", "Доход от песен, ₽", "Владелец")

    def get_queryset(self):
        return super().get_queryset().prefetch_related("songs")

    def get_row_values(self, item):
        income = sum((song.income for song in item.songs.all()), Decimal("0.00"))
        return (
            item.name,
            item.country or "—",
            item.description or "—",
            income,
            item.owner.username,
        )


class CatalogFormView(SecureView):
    template_name = "music/form.html"
    http_method_names = ("get", "post")

    def get_form(self, data=None):
        writable(self.request.user)
        instance = (
            record(self.service_class.model, self.request.user, self.kwargs["pk"])
            if "pk" in self.kwargs
            else None
        )
        owner = instance.owner if instance else self.request.user
        return self.form_class(data=data, instance=instance, owner=owner)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context.get("form") is None:
            context["form"] = self.get_form()
        context.update(
            title=("Изменение " if "pk" in self.kwargs else "Добавление ")
            + self.singular,
            list_url=reverse(self.list_url_name),
            help_text=self.help_text,
        )
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form(request.POST)
        if form.is_valid():
            try:
                self.service_class().save(request.user, form)
            except (ValidationError, IntegrityError) as error:
                form.add_error(
                    None,
                    error
                    if isinstance(error, ValidationError)
                    else "Запись с такими данными уже существует.",
                )
            else:
                request.audit_logged = True
                messages.success(
                    request,
                    "Изменения сохранены." if "pk" in kwargs else "Запись добавлена.",
                )
                return redirect(self.list_url_name)
        return self.render_to_response(
            self.get_context_data(form=form, **kwargs), status=400
        )


class SongFormView(SongViewMixin, CatalogFormView):
    pass


class ArtistFormView(ArtistViewMixin, CatalogFormView):
    pass


class CatalogDeleteView(SecureView):
    template_name = "music/error.html"
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        try:
            self.service_class().delete(request.user, kwargs["pk"])
        except ValidationError as error:
            return self.render_to_response(
                {
                    "title": "Удаление невозможно",
                    "errors": error.messages,
                    "back_url": reverse(self.list_url_name),
                },
                status=400,
            )
        request.audit_logged = True
        messages.success(request, "Запись удалена.")
        return redirect(self.list_url_name)


class SongDeleteView(SongViewMixin, CatalogDeleteView):
    pass


class ArtistDeleteView(ArtistViewMixin, CatalogDeleteView):
    pass


@method_decorator(never_cache, name="dispatch")
@method_decorator(sensitive_post_parameters("password"), name="dispatch")
class LoginView(TemplateView):
    template_name = "music/auth.html"
    http_method_names = ("get", "post")

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            title="Вход",
            form=LoginForm(self.request),
            next=self.request.POST.get("next", self.request.GET.get("next", "")),
            **kwargs,
        )

    def post(self, request, *args, **kwargs):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            audit(request.user, "LOGIN", "Успешный вход")
            request.audit_logged = True
            target = request.POST.get("next", "")
            return redirect(
                target
                if url_has_allowed_host_and_scheme(
                    target, {request.get_host()}, require_https=request.is_secure()
                )
                else "/songs"
            )
        audit(None, "LOGIN_FAILED", "Неверные или отключённые учётные данные")
        request.audit_logged = True
        context = self.get_context_data(**kwargs)
        context["form"] = form
        return self.render_to_response(context, status=400)


@method_decorator(sensitive_post_parameters("password1", "password2"), name="dispatch")
class RegisterView(LoginView):
    def get_context_data(self, **kwargs):
        return {"title": "Регистрация", "form": RegisterForm(), "registration": True}

    def post(self, request, *args, **kwargs):
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                register(form)
            except IntegrityError:
                form.add_error("username", "Имя пользователя уже занято.")
            else:
                request.audit_logged = True
                messages.success(
                    request,
                    "Регистрация завершена. Войдите в учётную запись. Ваша роль — READ_ONLY.",
                )
                return redirect("/login")
        context = self.get_context_data(**kwargs)
        context["form"] = form
        return self.render_to_response(context, status=400)


@method_decorator(never_cache, name="dispatch")
class LogoutView(TemplateView):
    http_method_names = ("post",)

    def post(self, request, *args, **kwargs):
        audit(request.user, "LOGOUT", "Выход из учётной записи")
        request.audit_logged = True
        logout(request)
        messages.success(request, "Вы вышли из учётной записи.")
        return redirect("/login")


class CalculationView(SecureView):
    template_name = "music/calculate.html"
    http_method_names = ("get", "post")

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            title="Расчёт дохода", form=CalculationForm(), **kwargs
        )

    def post(self, request, *args, **kwargs):
        form = CalculationForm(request.POST)
        context = self.get_context_data(**kwargs)
        context["form"] = form
        if form.is_valid():
            context["income"] = calculate_income(**form.cleaned_data)
            audit(
                request.user,
                "CALCULATE",
                "Расчёт дохода по числу прослушиваний и ставке",
            )
            request.audit_logged = True
        return self.render_to_response(context, status=200 if form.is_valid() else 400)


class LogsView(SecureView):
    template_name = "music/logs.html"

    def get_context_data(self, **kwargs):
        query = UserAction.objects.all()
        if role_for(self.request.user) != "ADMIN":
            query = query.filter(user=self.request.user)
        return super().get_context_data(
            title="Журнал действий", page_obj=page(query, self.request, 30), **kwargs
        )


class RolesView(SecureView):
    template_name = "music/roles.html"
    http_method_names = ("get", "post")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            admin_required(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        users = get_user_model().objects.prefetch_related("groups").order_by("username")
        current = page(users, self.request)
        return super().get_context_data(
            title="Назначение ролей",
            form=RoleForm(),
            page_obj=current,
            accounts=[(user, role_for(user)) for user in current],
            **kwargs,
        )

    def post(self, request, *args, **kwargs):
        form = RoleForm(request.POST)
        if form.is_valid():
            try:
                set_role(
                    request.user,
                    form.cleaned_data["user"].pk,
                    form.cleaned_data["role"],
                )
            except ValidationError as error:
                form.add_error(None, error)
            else:
                request.audit_logged = True
                messages.success(request, "Роль назначена.")
                return redirect("/roles")
        context = self.get_context_data(**kwargs)
        context["form"] = form
        return self.render_to_response(context, status=400)
