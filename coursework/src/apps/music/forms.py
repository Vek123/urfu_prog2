from typing import ClassVar

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .access import ROLES
from .models import MAX_RATE, MAX_STREAMS, Artist, Song


def bootstrap(form):
    for field in form.fields.values():
        field.widget.attrs["class"] = (
            "form-select" if isinstance(field.widget, forms.Select) else "form-control"
        )


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bootstrap(self)
        self.fields["username"].widget.attrs["autocomplete"] = "username"


class RegisterForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bootstrap(self)


class ArtistForm(forms.ModelForm):
    class Meta:
        model = Artist
        fields = ("name", "country", "description")
        widgets: ClassVar = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, owner, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.owner = owner
        bootstrap(self)

    def clean_name(self):
        name = self.cleaned_data["name"]
        duplicates = Artist.objects.filter(owner=self.instance.owner, name=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise ValidationError(
                "Исполнитель с таким именем уже есть в вашем каталоге."
            )
        return name


class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ("title", "artist", "release_date", "streams", "royalty_rate")
        widgets: ClassVar = {
            "release_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "royalty_rate": forms.NumberInput(
                attrs={"min": 0, "max": str(MAX_RATE), "step": "0.000001"}
            ),
            "streams": forms.NumberInput(
                attrs={"min": 0, "max": MAX_STREAMS, "step": 1}
            ),
        }

    def __init__(self, *args, owner, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.owner = owner
        self.fields["artist"].queryset = Artist.objects.filter(owner=owner)
        bootstrap(self)


class CalculationForm(forms.Form):
    streams = forms.IntegerField(
        label="Число прослушиваний", min_value=0, max_value=MAX_STREAMS
    )
    royalty_rate = forms.DecimalField(
        label="Ставка за прослушивание, ₽",
        min_value=0,
        max_value=MAX_RATE,
        max_digits=12,
        decimal_places=6,
        widget=forms.NumberInput(attrs={"step": "0.000001"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bootstrap(self)


class RoleForm(forms.Form):
    user = forms.ModelChoiceField(
        label="Пользователь", queryset=get_user_model().objects.none()
    )
    role = forms.ChoiceField(label="Роль", choices=[(r, r) for r in ROLES])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = (
            get_user_model()
            .objects.filter(is_active=True, is_superuser=False)
            .order_by("username")
        )
        bootstrap(self)
