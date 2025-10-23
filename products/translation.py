from modeltranslation.translator import TranslationOptions
from modeltranslation.decorators import register
from .models import Collection, Product

@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'short_description', 'detailed_description', 'care_instructions')

@register(Collection)
class CollectionTranslationOptions(TranslationOptions):
    fields = ('name','description')

