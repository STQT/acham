from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductShot


class ProductShotInline(admin.TabularInline):
    """Inline admin for ProductShot."""
    model = ProductShot
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']
    ordering = ['order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product model."""
    
    list_display = [
        'name',
        'type',
        'size',
        'color',
        'price',
        'is_available',
        'created_at'
    ]
    
    list_filter = [
        'type',
        'size',
        'color',
        'material',
        'is_available',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'material',
        'color',
        'short_description'
    ]
    
    list_editable = ['is_available', 'price']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'type', 'size', 'color', 'material')
        }),
        ('Descriptions', {
            'fields': ('short_description', 'detailed_description', 'care_instructions'),
            'classes': ('collapse',)
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'is_available')
        }),
    )
    
    inlines = [ProductShotInline]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['created_at', 'updated_at']
        return self.readonly_fields


@admin.register(ProductShot)
class ProductShotAdmin(admin.ModelAdmin):
    """Admin configuration for ProductShot model."""
    
    list_display = [
        'product',
        'image_preview',
        'alt_text',
        'is_primary',
        'order',
        'created_at'
    ]
    
    list_filter = [
        'is_primary',
        'product__type',
        'created_at'
    ]
    
    search_fields = [
        'product__name',
        'alt_text'
    ]
    
    list_editable = ['is_primary', 'order']
    
    fields = [
        'product',
        'image',
        'image_preview',
        'alt_text',
        'is_primary',
        'order'
    ]
    
    readonly_fields = ['image_preview', 'created_at']
    
    def image_preview(self, obj):
        """Display image preview in admin."""
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
                obj.image.url
            )
        return "No image"
    
    image_preview.short_description = "Preview"
