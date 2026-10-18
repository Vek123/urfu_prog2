from django.urls import path

from apps.hello.views import (
    HelloWorldView,
    ShowAllLength,
    ShowArrayList,
    ShowHashMap,
    UpdateArrayList,
    UpdateHashMap,
)

app_name = "hello"

urlpatterns = [
    path("hello/", HelloWorldView.as_view(), name="hello_world"),
    path("update-array/", UpdateArrayList.as_view(), name="update_array"),
    path("show-array/", ShowArrayList.as_view(), name="update_array"),
    path("update-map/", UpdateHashMap.as_view(), name="update_array"),
    path("show-map/", ShowHashMap.as_view(), name="update_array"),
    path("show-all-length/", ShowAllLength.as_view(), name="update_array"),
]
