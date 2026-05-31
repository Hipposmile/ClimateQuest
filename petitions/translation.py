from .models import Petition, Update
from modeltranslation.translator import register, TranslationOptions

@register(Petition)
class PetitionTranslationOptions(TranslationOptions):
    fields = ('title', 'content')

@register(Update)
class PetitionUpdateTranslationOptions(TranslationOptions):
    fields = ('title', 'content')