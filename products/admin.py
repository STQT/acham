from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductShot, UserFavorite, ProductShare, Cart, CartItem, ProductRelation


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
        'collection',
        'type',
        'size',
        'color',
        'price',
        'is_available',
        'created_at'
    ]
    
    list_filter = [
        'collection',
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
            'fields': ('name', 'type', 'size', 'collection', 'color', 'material')
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


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    """Admin configuration for Collection model."""

    list_display = [
        'name',
        'image',
        'slug',
        'is_active',
        'is_new_arrival',
        'created_at'
    ]

    list_filter = [
        'is_active',
        'is_new_arrival',
        'created_at'
    ]

    search_fields = [
        'name',
        'slug'
    ]

    prepopulated_fields = {
        'slug': ('name',)
    }
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'image')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_new_arrival')
        }),
    )


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    """Admin configuration for UserFavorite model."""
    
    list_display = [
        'user',
        'product',
        'created_at'
    ]
    
    list_filter = [
        'created_at',
        'product__type'
    ]
    
    search_fields = [
        'user__email',
        'product__name'
    ]
    
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product')


@admin.register(ProductShare)
class ProductShareAdmin(admin.ModelAdmin):
    """Admin configuration for ProductShare model."""
    
    list_display = [
        'product',
        'user',
        'platform',
        'is_successful',
        'shared_at'
    ]
    
    list_filter = [
        'platform',
        'is_successful',
        'shared_at'
    ]
    
    search_fields = [
        'product__name',
        'user__email'
    ]
    
    readonly_fields = ['shared_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'user')


class CartItemInline(admin.TabularInline):
    """Inline admin for CartItem."""
    model = CartItem
    extra = 0
    fields = ['product', 'quantity', 'total_price', 'added_at']
    readonly_fields = ['total_price', 'added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin configuration for Cart model."""
    
    list_display = [
        'user',
        'item_count',
        'total_items',
        'total_price',
        'created_at',
        'updated_at'
    ]
    
    list_filter = [
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'user__email'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'total_items', 'total_price', 'item_count']
    
    inlines = [CartItemInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin configuration for CartItem model."""
    
    list_display = [
        'cart',
        'product',
        'quantity',
        'total_price',
        'added_at'
    ]
    
    list_filter = [
        'added_at',
        'product__type'
    ]
    
    search_fields = [
        'cart__user__email',
        'product__name'
    ]
    
    readonly_fields = ['total_price', 'added_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cart__user', 'product')


@admin.register(ProductRelation)
class ProductRelationAdmin(admin.ModelAdmin):
    """Admin configuration for ProductRelation model."""
    
    list_display = [
        'source_product',
        'target_product',
        'relation_type',
        'priority',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'relation_type',
        'is_active',
        'created_at'
    ]
    
    search_fields = [
        'source_product__name',
        'target_product__name'
    ]
    
    list_editable = ['priority', 'is_active']
    
    fields = [
        'source_product',
        'target_product',
        'relation_type',
        'priority',
        'is_active'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('source_product', 'target_product')
