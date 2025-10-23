from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class Collection(models.Model):
    """Collection model for grouping products."""
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Collection Name"),
        help_text=_("Name of the collection")
    )
    
    image = models.ImageField(
        upload_to='collections/',
        verbose_name=_("Image"),
        help_text=_("Image of the collection"),
        blank=True,
        null=True
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly version of the name")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether this collection is active")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Collection")
        verbose_name_plural = _("Collections")
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model with detailed information."""
    
    class ProductType(models.TextChoices):
        CLOTHING = "clothing", _("Clothing")
        ACCESSORIES = "accessories", _("Accessories")
        SHOES = "shoes", _("Shoes")
        BAGS = "bags", _("Bags")
        JEWELRY = "jewelry", _("Jewelry")
        OTHER = "other", _("Other")
    
    class ProductSize(models.TextChoices):
        XS = "xs", _("XS")
        S = "s", _("S")
        M = "m", _("M")
        L = "l", _("L")
        XL = "xl", _("XL")
        XXL = "xxl", _("XXL")
        XXXL = "xxxl", _("XXXL")
        ONE_SIZE = "one_size", _("One Size")
    
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_("Collection"),
        help_text=_("Collection this product belongs to"),
        blank=True,
        null=True
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Product Name"),
        help_text=_("The name of the product")
    )
    
    size = models.CharField(
        max_length=20,
        choices=ProductSize.choices,
        verbose_name=_("Size"),
        help_text=_("Product size")
    )
    
    material = models.CharField(
        max_length=100,
        verbose_name=_("Material"),
        help_text=_("Primary material of the product")
    )
    
    type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        verbose_name=_("Product Type"),
        help_text=_("Category of the product")
    )
    
    color = models.CharField(
        max_length=50,
        verbose_name=_("Color"),
        help_text=_("Primary color of the product")
    )
    
    # Three types of detail text
    short_description = models.TextField(
        max_length=500,
        verbose_name=_("Short Description"),
        help_text=_("Brief description of the product"),
        blank=True
    )
    
    detailed_description = models.TextField(
        verbose_name=_("Detailed Description"),
        help_text=_("Comprehensive description with features and benefits"),
        blank=True
    )
    
    care_instructions = models.TextField(
        verbose_name=_("Care Instructions"),
        help_text=_("How to care for and maintain the product"),
        blank=True
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Price"),
        help_text=_("Product price")
    )
    
    is_available = models.BooleanField(
        default=True,
        verbose_name=_("Available"),
        help_text=_("Whether the product is currently available")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class ProductShot(models.Model):
    """Model for product images."""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='shots',
        verbose_name=_("Product")
    )
    
    image = models.ImageField(
        upload_to='products/shots/',
        verbose_name=_("Image"),
        help_text=_("Product image")
    )
    
    alt_text = models.CharField(
        max_length=200,
        verbose_name=_("Alt Text"),
        help_text=_("Alternative text for accessibility"),
        blank=True
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name=_("Primary Image"),
        help_text=_("Whether this is the main product image")
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Display Order"),
        help_text=_("Order in which images should be displayed")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = _("Product Shot")
        verbose_name_plural = _("Product Shots")
    
    def __str__(self):
        return f"{self.product.name} - Shot {self.order}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductShot.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class UserFavorite(models.Model):
    """Model for user product favorites."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name=_("User")
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name=_("Product")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']
        verbose_name = _("User Favorite")
        verbose_name_plural = _("User Favorites")
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name}"


class ProductShare(models.Model):
    """Model for tracking product shares."""
    
    class SharePlatform(models.TextChoices):
        FACEBOOK = "facebook", _("Facebook")
        TWITTER = "twitter", _("Twitter")
        INSTAGRAM = "instagram", _("Instagram")
        WHATSAPP = "whatsapp", _("WhatsApp")
        TELEGRAM = "telegram", _("Telegram")
        EMAIL = "email", _("Email")
        COPY_LINK = "copy_link", _("Copy Link")
        OTHER = "other", _("Other")
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='shares',
        verbose_name=_("Product")
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='product_shares',
        verbose_name=_("User")
    )
    
    platform = models.CharField(
        max_length=20,
        choices=SharePlatform.choices,
        verbose_name=_("Platform"),
        help_text=_("Platform where the product was shared")
    )
    
    shared_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: Track if share was successful
    is_successful = models.BooleanField(
        default=True,
        verbose_name=_("Successful"),
        help_text=_("Whether the share was successful")
    )
    
    class Meta:
        ordering = ['-shared_at']
        verbose_name = _("Product Share")
        verbose_name_plural = _("Product Shares")
    
    def __str__(self):
        return f"{self.product.name} - {self.get_platform_display()}"
