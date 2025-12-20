from django.contrib import admin
from .models import Banner, FAQ, StaticPage
# Register your models here.

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """Admin configuration for Banner model."""

    list_display = [
        'title',
        'has_video',
        'is_active',
        'created_at'
    ]

    list_filter = [
        'is_active',
        'created_at'
    ]

    search_fields = [
        'title'
    ]

    fields = [
        'title',
        'video',
        'image',
        'is_active'
    ]

    readonly_fields = []

    def has_video(self, obj):
        return bool(obj.video)

    has_video.boolean = True
    has_video.short_description = 'Video?'

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
        'content'
    ]

    readonly_fields = []