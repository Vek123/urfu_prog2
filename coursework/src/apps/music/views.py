from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework import generics, serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated

from .access import visible, writable
from .forms import ArtistForm, SongForm
from .serializers import ArtistSerializer, SongSerializer
from .services import ArtistService, SongService


class CatalogPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if (
            request.method not in SAFE_METHODS
            and request.method.lower() in view.http_method_names
        ):
            writable(request.user)
        return True


class CatalogAPIMixin:
    authentication_classes = (SessionAuthentication,)
    permission_classes = (CatalogPermission,)
    service_class = None
    form_class = None

    def get_queryset(self):
        return visible(self.service_class.model, self.request.user).select_related(
            "owner"
        )

    def save_serializer(self, serializer):
        item = serializer.instance
        payload = (
            {field: getattr(item, field) for field in self.form_class.Meta.fields}
            if item
            else {}
        )
        payload.update(serializer.validated_data)
        form = self.form_class(
            payload, instance=item, owner=item.owner if item else self.request.user
        )
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)
        try:
            serializer.instance = self.service_class().save(self.request.user, form)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                error.message_dict if hasattr(error, "message_dict") else error.messages
            ) from error
        except IntegrityError as error:
            raise serializers.ValidationError(
                "Запись с такими данными уже существует."
            ) from error
        self.request._request.audit_logged = True

    def perform_create(self, serializer):
        self.save_serializer(serializer)

    def perform_update(self, serializer):
        self.save_serializer(serializer)

    def perform_destroy(self, instance):
        try:
            self.service_class().delete(self.request.user, instance.pk)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        self.request._request.audit_logged = True


class CatalogListAPIView(CatalogAPIMixin, generics.ListCreateAPIView):
    http_method_names = ("get", "post", "head", "options")


class CatalogDetailAPIView(CatalogAPIMixin, generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ("get", "put", "patch", "delete", "head", "options")


class SongAPIMixin:
    serializer_class = SongSerializer
    form_class = SongForm
    service_class = SongService

    def get_queryset(self):
        return super().get_queryset().select_related("artist")


class ArtistAPIMixin:
    serializer_class = ArtistSerializer
    form_class = ArtistForm
    service_class = ArtistService


class SongListAPIView(SongAPIMixin, CatalogListAPIView):
    pass


class SongDetailAPIView(SongAPIMixin, CatalogDetailAPIView):
    pass


class ArtistListAPIView(ArtistAPIMixin, CatalogListAPIView):
    pass


class ArtistDetailAPIView(ArtistAPIMixin, CatalogDetailAPIView):
    pass
