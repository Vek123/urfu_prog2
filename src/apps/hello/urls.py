from django.urls import path

from apps.hello.views import HelloWorldView

app_name = "hello"

urlpatterns = [
    path("hello/", HelloWorldView.as_view(), name="hello_world"),
]
