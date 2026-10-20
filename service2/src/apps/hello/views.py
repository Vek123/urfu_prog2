from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View


class HelloWorldView(View):
    def get(self, request, *args, **kwargs):
        name = request.GET.get("name", None)
        if name is None:
            name = "world"

        return HttpResponse(f"Hello, {name}!")


array = None
hash_map = None


class UpdateArrayList(View):
    def get(self, request, *args, **kwargs):
        global array

        if "s" not in request.GET:
            return HttpResponseBadRequest("You need to provide GET-param <s>")

        s = request.GET["s"]
        if array is None:
            array = []

        array.append(s)
        return HttpResponse()


class ShowArrayList(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(str(array))


class UpdateHashMap(View):
    def get(self, request, *args, **kwargs):
        global hash_map

        if "s" not in request.GET:
            return HttpResponseBadRequest("You need to provide GET-param <s>")

        s = request.GET["s"]
        if hash_map is None:
            hash_map = {}

        try:
            key, val = s.strip().split("=")
            hash_map[key] = val
        except Exception:  # noqa: BLE001
            return HttpResponseBadRequest("Provided key-value pair is not valid")

        return HttpResponse()


class ShowHashMap(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(str(hash_map))


class ShowAllLength(View):
    def get(self, request, *args, **kwargs):
        array_length = len(array) if array is not None else 0
        hash_map_length = len(hash_map) if hash_map is not None else 0

        return HttpResponse(array_length + hash_map_length)
