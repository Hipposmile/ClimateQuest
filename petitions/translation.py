from modeltranslation.translator import TranslationOptions, register

from .models import Petition, Update


@register(Petition)
class PetitionTranslationOptions(TranslationOptions):
    fields = ("title", "content")


@register(Update)
class PetitionUpdateTranslationOptions(TranslationOptions):
    fields = ("title", "content")
