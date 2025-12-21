from django.contrib import admin
from .models import FAQ, StaticPage, ContactMessage, ReturnRequest
# Register your models here.

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin configuration for FAQ model."""

    list_display = [
        'question',
        'answer',
        'created_at'
    ]

    list_filter = [
        'created_at'
    ]


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    """Admin configuration for StaticPage model."""

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