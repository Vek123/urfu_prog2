from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView

from .auth_forms import DUPLICATE_EMAIL, EmailAuthenticationForm, RegistrationForm
from .auth_services import UserService, can_view_users


@method_decorator(never_cache, name='dispatch')
class IndexView(TemplateView):
    template_name = 'education/index.html'
    extra_context = {'title': 'Главная'}


@method_decorator(never_cache, name='dispatch')
@method_decorator(sensitive_post_parameters('password'), name='dispatch')
class RegistrationView(TemplateView):
    template_name = 'education/auth_form.html'
    http_method_names = ('get',)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('education:web-student-list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            title='Регистрация', form=RegistrationForm(),
            action_url=reverse('education:register-save'),
            button='Зарегистрироваться', registration=True,
            success='success' in self.request.GET, **kwargs)


class RegistrationSaveView(RegistrationView):
    http_method_names = ('post',)

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                UserService().register(form.cleaned_data)
            except IntegrityError:
                form.add_error('email', DUPLICATE_EMAIL)
            else:
                return redirect(reverse('education:register') + '?success=1')
        context = self.get_context_data(**kwargs)
        context.update(form=form, success=False)
        return self.render_to_response(context, status=400)


@method_decorator(never_cache, name='dispatch')
@method_decorator(sensitive_post_parameters('password'), name='dispatch')
class LoginView(TemplateView):
    template_name = 'education/auth_form.html'
    http_method_names = ('get', 'post')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('education:web-student-list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            title='Вход', form=EmailAuthenticationForm(self.request),
            action_url=reverse('education:login'), button='Войти',
            next=self.request.POST.get('next', self.request.GET.get('next', '')),
            logged_out='logout' in self.request.GET, **kwargs)

    def post(self, request, *args, **kwargs):
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.POST.get('next', '')
            if url_has_allowed_host_and_scheme(
                    next_url, allowed_hosts={request.get_host()},
                    require_https=request.is_secure()):
                return redirect(next_url)
            return redirect('education:web-student-list')
        context = self.get_context_data(**kwargs)
        context.update(form=form, logged_out=False)
        return self.render_to_response(context, status=400)


@method_decorator(never_cache, name='dispatch')
class LogoutView(TemplateView):
    http_method_names = ('post',)

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse('education:login') + '?logout=1')


@method_decorator(never_cache, name='dispatch')
class UsersView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'education/users.html'
    http_method_names = ('get',)

    def test_func(self):
        return can_view_users(self.request.user)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            title='Пользователи', kind='users', users=UserService().get_all(), **kwargs)
