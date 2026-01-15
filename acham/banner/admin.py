from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import FAQ, StaticPage, ContactMessage, ReturnRequest, EmailSubscription, AboutPageSection


@admin.register(FAQ)
class FAQAdmin(TranslationAdmin):
    """Admin configuration for FAQ model with translation support."""

    list_display = [
        'question',
        'created_at'
    ]

    list_filter = [
        'created_at'
    ]

    search_fields = [
        'question',
        'answer'
    ]

    # TranslationAdmin automatically handles language tabs
    class Media:
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }


@admin.register(StaticPage)
class StaticPageAdmin(TranslationAdmin):
    """Admin configuration for StaticPage model with translation support."""

    list_display = [
        'page_type',
        'title',
        'created_at',
        'updated_at'
    ]

    list_filter = [
        'page_type',
        'created_at'
    ]

    search_fields = [
        'title',
        'content'
    ]

    fields = [
        'page_type',
        'title',
        'image',
        'content'
    ]

    readonly_fields = []

    # TranslationAdmin automatically handles language tabs
    class Media:
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Admin configuration for ContactMessage model."""

    list_display = [
        'first_name',
        'last_name',
        'email',
        'phone',
        'subject',
        'created_at'
    ]

    list_filter = [
        'created_at'
    ]

    search_fields = [
        'first_name',
        'last_name',
        'email',
        'phone',
        'subject',
        'message'
    ]

    fields = [
        'first_name',
        'last_name',
        'email',
        'phone',
        'subject',
        'message',
        'created_at',
        'updated_at'
    ]

    readonly_fields = ['created_at', 'updated_at']

    ordering = ['-created_at']


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    """Admin configuration for ReturnRequest model."""

    list_display = [
        'order_number',
        'email_or_phone',
        'created_at'
    ]

    list_filter = [
        'created_at'
    ]

    search_fields = [
        'order_number',
        'email_or_phone',
        'message'
    ]

    fields = [
        'order_number',
        'email_or_phone',
        'message',
        'created_at',
        'updated_at'
    ]

    readonly_fields = ['created_at', 'updated_at']

    ordering = ['-created_at']


@admin.register(EmailSubscription)
class EmailSubscriptionAdmin(admin.ModelAdmin):
    """Admin configuration for EmailSubscription model."""

    list_display = [
        'email',
        'language',
        'is_active',
        'created_at',
        'updated_at'
    ]

    list_filter = [
        'language',
        'is_active',
        'created_at'
    ]

    search_fields = [
        'email'
    ]

    fields = [
        'email',
        'language',
        'is_active',
        'created_at',
        'updated_at'
    ]

    readonly_fields = ['created_at', 'updated_at']

    ordering = ['-created_at']


@admin.register(AboutPageSection)
class AboutPageSectionAdmin(TranslationAdmin):
    """Admin configuration for AboutPageSection model with translation support."""

    list_display = [
        'section_type',
        'title',
        'is_active',
        'order',
        'created_at',
        'updated_at'
    ]

    list_filter = [
        'section_type',
        'is_active',
        'created_at'
    ]

    search_fields = [
        'title',
        'content',
        'founder_name'
    ]

    fieldsets = (
        (_("Basic Information"), {
            "fields": (
                "section_type",
                "is_active",
                "order",
            )
        }),
        (_("Hero Section"), {
            "fields": (
                "founder_name",
                "founder_title",
                "hero_image",
            ),
            "classes": ("collapse",),
        }),
        (_("Content"), {
            "fields": (
                "title",
                "content",
                "image",
            )
        }),
        (_("Additional Images (for Fabrics section)"), {
            "fields": (
                "image_2",
                "image_3",
            ),
            "classes": ("collapse",),
        }),
        (_("Process Section"), {
            "fields": (
                "process_description",
                "process_items",
            ),
            "classes": ("collapse",),
        }),
        (_("Timeline"), {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    ordering = ['order', 'section_type']

    # TranslationAdmin automatically handles language tabs
    class Media:
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }