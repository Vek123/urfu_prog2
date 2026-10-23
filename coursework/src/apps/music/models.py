from decimal import ROUND_HALF_UP, Decimal
from typing import ClassVar

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

MAX_STREAMS = 10**12
MAX_RATE = Decimal("999999.999999")


def calculate_income(streams, royalty_rate):
    return (Decimal(streams) * royalty_rate).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


class Artist(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField("Имя исполнителя", max_length=120)
    country = models.CharField("Страна", max_length=80, blank=True)
    description = models.TextField("Описание", max_length=1000, blank=True)

    class Meta:
        db_table = "artists"
        ordering = ("name", "id")
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=("owner", "name"), name="artist_owner_name_unique"
            )
        ]

    def __str__(self):
        return self.name


class Song(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    artist = models.ForeignKey(
        Artist,
        on_delete=models.PROTECT,
        related_name="songs",
        verbose_name="Исполнитель",
    )
    title = models.CharField("Название песни", max_length=150)
    release_date = models.DateField("Дата выпуска", null=True, blank=True)
    streams = models.PositiveBigIntegerField(
        "Прослушивания", validators=[MaxValueValidator(MAX_STREAMS)]
    )
    royalty_rate = models.DecimalField(
        "Ставка за прослушивание, ₽",
        max_digits=12,
        decimal_places=6,
        validators=[MinValueValidator(0), MaxValueValidator(MAX_RATE)],
    )

    class Meta:
        db_table = "songs"
        ordering = ("-id",)
        constraints: ClassVar = [
            models.CheckConstraint(
                condition=models.Q(streams__gte=0, streams__lte=MAX_STREAMS),
                name="song_streams_range",
            ),
            models.CheckConstraint(
                condition=models.Q(royalty_rate__gte=0, royalty_rate__lte=MAX_RATE),
                name="song_rate_range",
            ),
        ]

    @property
    def income(self):
        return calculate_income(self.streams, self.royalty_rate)

    def __str__(self):
        return self.title


class UserAction(models.Model):
    date_actions = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    username_snapshot = models.CharField(max_length=150)
    action = models.CharField(max_length=40)
    description = models.CharField(max_length=400)

    class Meta:
        db_table = "user_actions"
        ordering = ("-id",)
