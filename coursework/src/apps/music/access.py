from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

ROLES = ("READ_ONLY", "USER", "ADMIN")


def role_for(user):
    if not user.is_authenticated:
        return "READ_ONLY"
    if user.is_superuser:
        return "ADMIN"
    names = set(user.groups.values_list("name", flat=True))
    return next((role for role in reversed(ROLES) if role in names), "READ_ONLY")


def visible(model, user):
    query = model.objects.all()
    return query.filter(owner=user) if role_for(user) == "USER" else query


def writable(user):
    if not user.is_authenticated or role_for(user) == "READ_ONLY":
        raise PermissionDenied("Ваша роль разрешает только чтение.")


def admin_required(user):
    if not user.is_authenticated or role_for(user) != "ADMIN":
        raise PermissionDenied("Требуется роль ADMIN.")


def record(model, user, pk):
    return get_object_or_404(visible(model, user), pk=pk)


def navigation(request):
    role = role_for(request.user)
    return {
        "current_role": role,
        "can_write": request.user.is_authenticated and role != "READ_ONLY",
        "is_admin": request.user.is_authenticated and role == "ADMIN",
    }
