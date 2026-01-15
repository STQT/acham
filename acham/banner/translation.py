from modeltranslation.translator import TranslationOptions
from modeltranslation.decorators import register
from .models import FAQ, StaticPage, AboutPageSection


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


@register(AboutPageSection)
class AboutPageSectionTranslationOptions(TranslationOptions):
    fields = (
        "founder_name",
        "founder_title",
        "title",
        "content",
        "process_description",
    )

