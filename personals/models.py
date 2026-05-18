from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models

class TreeCodes(models.Model):
    code = models.CharField(max_length=100)
    redeemURL = models.URLField()
    sponsor = models.CharField(max_length=100)
    planted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.sponsor} --> {self.code}'


class UserErweitert(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    mailinglist = models.BooleanField(default=True)
    mail_verified = models.BooleanField(default=False)
    statement = models.TextField(default="Hallo. Ich benutze ClimateQuest.")
    weekly_goal = models.PositiveIntegerField(default=20, validators=[MinValueValidator(1)])
    planted_trees = models.ManyToManyField(TreeCodes, blank=True)
    allows_data_view = models.BooleanField(default=False)
    lang = models.CharField(max_length=2, default='de')
    additional_klimapunkte = models.FloatField(default=0)
    show_tour_banner = models.BooleanField(default=True)

    @property
    def given_credits(self):
        return self.planted_trees.count()

    def plant_tree(self):
        tree_code = TreeCodes.objects.filter(planted=False).first()
        if not tree_code:
            return False
        tree_code.planted = True
        tree_code.save()
        self.planted_trees.add(tree_code)
        return True

    def __str__(self):
        return self.user.username


# Wichtig: Immer auch ein Level ab 0 Punkten haben, sonst kommt es zu Fehlern
class Level(models.Model):
    klimapunkte = models.IntegerField()
    description = models.CharField(max_length=100)
    description_en = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.description}'
