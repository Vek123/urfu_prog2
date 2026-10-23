from typing import ClassVar

from rest_framework import serializers

from .models import Artist, Song


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ("id", "owner", "name", "country", "description")
        read_only_fields = ("id", "owner")
        validators: ClassVar = []


class SongSerializer(serializers.ModelSerializer):
    income = serializers.DecimalField(max_digits=22, decimal_places=2, read_only=True)

    class Meta:
        model = Song
        fields = (
            "id",
            "owner",
            "title",
            "artist",
            "release_date",
            "streams",
            "royalty_rate",
            "income",
        )
        read_only_fields = ("id", "owner", "income")

    def get_fields(self):
        fields = super().get_fields()
        owner = (
            self.instance.owner
            if isinstance(self.instance, Song)
            else self.context["request"].user
        )
        fields["artist"].queryset = Artist.objects.filter(owner=owner)
        return fields
