from django.http import HttpResponse
from django.views import View


class HelloWorldView(View):
    def get(self, request, *args, **kwargs):
        name = request.GET.get("name", None)
        if name is None:
            name = "world"

        return HttpResponse(f"Hello, {name}!")
