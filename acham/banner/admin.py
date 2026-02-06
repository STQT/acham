import csv
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from modeltranslation.admin import TranslationAdmin
from .models import FAQ, StaticPage, ContactMessage, ReturnRequest, EmailSubscription, AboutPageSection
from django.utils.translation import gettext_lazy as _

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
    
    actions = ['export_emails_csv', 'export_all_emails_csv']
    
    def export_emails_csv(self, request, queryset):
        """Экспорт выбранных email в CSV."""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="email_subscriptions.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Email', 'Language', 'Is Active', 'Created At', 'Updated At'])
        
        for subscription in queryset:
            writer.writerow([
                subscription.email,
                subscription.get_language_display(),
                'Yes' if subscription.is_active else 'No',
                subscription.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                subscription.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])
        
        self.message_user(request, f'Экспортировано {queryset.count()} email адресов.')
        return response
    
    export_emails_csv.short_description = "Экспортировать выбранные email в CSV"
    
    def export_all_emails_csv(self, request, queryset):
        """Экспорт всех email в CSV."""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="all_email_subscriptions.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Email', 'Language', 'Is Active', 'Created At', 'Updated At'])
        
        all_subscriptions = EmailSubscription.objects.all()
        count = 0
        for subscription in all_subscriptions:
            writer.writerow([
                subscription.email,
                subscription.get_language_display(),
                'Yes' if subscription.is_active else 'No',
                subscription.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                subscription.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])
            count += 1
        
        self.message_user(request, f'Экспортировано {count} email адресов.')
        return response
    
    export_all_emails_csv.short_description = "Экспортировать ВСЕ email в CSV"


@admin.register(AboutPageSection)
class AboutPageSectionAdmin(TranslationAdmin):
    """Admin configuration for AboutPageSection singleton model with translation support."""

    def changelist_view(self, request, extra_context=None):
        """Redirect to the singleton instance edit form."""
        instance = AboutPageSection.get_instance()
        return redirect(reverse('admin:banner_aboutpagesection_change', args=[instance.pk]))

    def has_add_permission(self, request):
        """Disable adding new instances (singleton pattern)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deleting the singleton instance."""
        return False

    fieldsets = (
        (_("Basic Information"), {
            "fields": (
                "is_active",
            )
        }),
        (_("Hero Section"), {
            "fields": (
                "founder_name",
                "founder_title",
                "hero_image",
            ),
        }),
        (_("History Section"), {
            "fields": (
                "history_title",
                "history_content",
                "history_image",
            ),
        }),
        (_("Philosophy Section"), {
            "fields": (
                "philosophy_title",
                "philosophy_content",
                "philosophy_image",
            ),
        }),
        (_("Fabrics Section"), {
            "fields": (
                "fabrics_title",
                "fabrics_content",
                "fabrics_image",
                "fabrics_image_2",
                "fabrics_image_3",
            ),
        }),
        (_("Process Section"), {
            "fields": (
                "process_title",
                "process_description",
                "process_items",
            ),
        }),
        (_("Timeline"), {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

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