import json
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q
from django.db.models.deletion import ProtectedError

from .access import ROLES, admin_required, record, writable
from .models import Artist, Song, UserAction

logger = logging.getLogger("apps.music.actions")


def audit(user, action, description):
    authenticated = user is not None and user.is_authenticated
    entry = UserAction.objects.create(
        user=user if authenticated else None,
        username_snapshot=user.get_username() if authenticated else "anonymous",
        action=action,
        description=description[:400],
    )
    payload = {
        "id": entry.pk,
        "date_actions": entry.date_actions.isoformat(),
        "user_id": entry.user_id,
        "username": entry.username_snapshot,
        "action": action,
        "description": entry.description,
    }
    transaction.on_commit(lambda: logger.info(json.dumps(payload, ensure_ascii=False)))
    return entry


@transaction.atomic
def register(form):
    user = form.save()
    role, _ = Group.objects.get_or_create(name="READ_ONLY")
    user.groups.add(role)
    audit(user, "REGISTER", "Регистрация с ролью READ_ONLY")
    return user


class CatalogService:
    model = None
    deletion_error = "Нельзя удалить связанную запись."

    def validate(self, item):
        item.full_clean()

    @transaction.atomic
    def save(self, user, form):
        writable(user)
        item = form.save(commit=False)
        creating = item.pk is None
        if creating:
            item.owner = user
        else:
            original = record(self.model, user, item.pk)
            item.owner_id = original.owner_id
        self.validate(item)
        item.save()
        audit(
            user,
            "CREATE" if creating else "UPDATE",
            f"{self.model._meta.db_table}: id={item.pk}",
        )
        return item

    @transaction.atomic
    def delete(self, user, pk):
        writable(user)
        item = record(self.model, user, pk)
        try:
            item.delete()
        except ProtectedError as error:
            raise ValidationError(self.deletion_error) from error
        audit(user, "DELETE", f"{self.model._meta.db_table}: id={pk}")


class ArtistService(CatalogService):
    model = Artist
    deletion_error = "Нельзя удалить исполнителя, пока в каталоге есть его песни."


class SongService(CatalogService):
    model = Song

    def validate(self, item):
        if item.artist.owner_id != item.owner_id:
            raise ValidationError(
                "Исполнитель и песня должны принадлежать одному владельцу."
            )
        super().validate(item)


@transaction.atomic
def set_role(actor, target_id, new_role):
    admin_required(actor)
    if new_role not in ROLES:
        raise ValidationError("Неизвестная роль.")
    # SQLite serializes writers; the no-op UPDATE obtains its write lock before
    # checking the final administrator. It also locks the row on server databases.
    get_user_model().objects.filter(pk=actor.pk).update(is_active=F("is_active"))
    target = (
        get_user_model().objects.select_for_update().get(pk=target_id, is_active=True)
    )
    if target.is_superuser:
        raise ValidationError("Роль суперпользователя управляется средствами Django.")
    if new_role != "ADMIN" and target.groups.filter(name="ADMIN").exists():
        remaining = (
            get_user_model()
            .objects.filter(is_active=True)
            .exclude(pk=target.pk)
            .filter(Q(is_superuser=True) | Q(groups__name="ADMIN"))
            .distinct()
            .exists()
        )
        if not remaining:
            raise ValidationError(
                "Нельзя понизить последнего активного администратора."
            )
    role, _ = Group.objects.get_or_create(name=new_role)
    target.groups.remove(*target.groups.filter(name__in=ROLES))
    target.groups.add(role)
    audit(actor, "ROLE_CHANGE", f"user_id={target.pk}; role={new_role}")
