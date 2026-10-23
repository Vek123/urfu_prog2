from django.urls import include, path

urlpatterns = [path("", include("apps.music.urls"))]
