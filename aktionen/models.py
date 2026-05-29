from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class AktionenListe(models.Model):
    name = models.CharField(max_length=100, unique=True)
    name_en = models.CharField(max_length=100)

    klimapunkte = models.FloatField()

    mengeBeschreibung = models.CharField(max_length=100)
    mengeBeschreibung_en = models.CharField(max_length=100)

    mengeBeschreibungSingular = models.CharField(max_length=100)
    mengeBeschreibungSingular_en = models.CharField(max_length=100)

    anmerkung = models.CharField(max_length=500)
    anmerkung_en = models.CharField(max_length=500)

    source = models.CharField(max_length=1000)
    source_en = models.CharField(max_length=1000)

    max = models.FloatField(default=0.0)

    track_weekly = models.BooleanField(default=False)

    track_kilometerly = models.BooleanField(default=False)

    forbidden_in_same_period = models.ManyToManyField('self', blank=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='actions', null=True, blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    name_en = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Aktion(models.Model):
    description = models.CharField(max_length=200, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quantity = models.FloatField()
    aktion = models.ForeignKey(AktionenListe, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    @property
    def impact(self):
        return self.quantity * self.aktion.klimapunkte

    def __str__(self):
        return f"{self.aktion.name} ({self.user})"


class TrackedActions(models.Model):
    action = models.ForeignKey(AktionenListe, on_delete=models.CASCADE, related_name='tracked_actions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tracked_actions')
    since = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.action.name} --> ({self.user})"
