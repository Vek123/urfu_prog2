from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q

DUPLICATE_EMAIL = 'На этот email уже зарегистрирована учётная запись.'


class RegistrationForm(forms.Form):
    first_name = forms.CharField(label='Имя', max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'given-name'}))
    last_name = forms.CharField(label='Фамилия', max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'family-name'}))
    email = forms.EmailField(label='Email', max_length=150,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}))
    password = forms.CharField(label='Пароль', strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text='Не менее 8 символов. Пароль не должен быть распространённым, '
                  'полностью числовым или похожим на ваши данные.')

    def clean_email(self):
        email = self.cleaned_data['email'].casefold()
        if len(email) > 150:
            raise ValidationError('Email должен содержать не более 150 символов.')
        if get_user_model().objects.filter(
                Q(username__iexact=email) | Q(email__iexact=email)).exists():
            raise ValidationError(DUPLICATE_EMAIL)
        return email

    def clean(self):
        data = super().clean()
        if data.get('password'):
            user = get_user_model()(
                username=data.get('email', ''), email=data.get('email', ''),
                first_name=data.get('first_name', ''), last_name=data.get('last_name', ''))
            try:
                validate_password(data['password'], user)
            except ValidationError as error:
                self.add_error('password', error)
        return data


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email', max_length=150,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'username'}))
    password = forms.CharField(label='Пароль', strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}))
    error_messages = {
        'invalid_login': 'Неверный email или пароль.',
        'inactive': 'Эта учётная запись отключена.',
    }

    def clean_username(self):
        return self.cleaned_data['username'].casefold()
