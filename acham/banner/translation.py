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
        # Hero section
        "founder_name",
        "founder_title",
        # History section
        "history_title",
        "history_content",
        # Philosophy section
        "philosophy_title",
        "philosophy_content",
        # Fabrics section
        "fabrics_title",
        "fabrics_content",
        # Process section
        "process_title",
        "process_description",
    )

