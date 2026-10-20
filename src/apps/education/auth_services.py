from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction

ADMIN_ROLE = 'ROLE_ADMIN'


def can_view_users(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=ADMIN_ROLE).exists())


def security_context(request):
    return {'can_view_users': can_view_users(request.user)}


class UserService:
    @transaction.atomic
    def register(self, data):
        user = get_user_model().objects.create_user(
            username=data['email'], email=data['email'],
            first_name=data['first_name'], last_name=data['last_name'],
            password=data['password'])
        # The assignment gives registered accounts access to the users list.
        # This group does not grant Django staff or superuser privileges.
        role, _ = Group.objects.get_or_create(name=ADMIN_ROLE)
        user.groups.add(role)
        return user

    def get_all(self):
        return get_user_model().objects.order_by('id').values(
            'id', 'first_name', 'last_name', 'email')
