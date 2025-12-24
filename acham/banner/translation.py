from modeltranslation.translator import TranslationOptions
from modeltranslation.decorators import register
from .models import FAQ, StaticPage


@register(FAQ)
class FAQTranslationOptions(TranslationOptions):
    fields = (
        "question",
        "answer",
    )


@register(StaticPage)
class StaticPageTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "content",
    )

