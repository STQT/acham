from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from acham.utils.image_processing import optimize_image


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
    
    video = models.FileField(
        upload_to='collections/videos/',
        verbose_name=_("Video"),
        help_text=_("Video file for the collection (optional)"),
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
    
    is_new_arrival = models.BooleanField(
        default=False,
        verbose_name=_("New Arrival"),
        help_text=_("Whether this collection should appear in new arrivals page")
    )

    is_featured_banner = models.BooleanField(
        default=False,
        verbose_name=_("Featured Banner"),
        help_text=_("Mark this collection to appear as the main banner on the storefront")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Collection")
        verbose_name_plural = _("Collections")
        constraints = [
            models.UniqueConstraint(
                fields=['is_featured_banner'],
                condition=models.Q(is_featured_banner=True),
                name='unique_featured_collection_banner'
            )
        ]
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.image and getattr(self.image, "_file", None):
            optimize_image(self.image, force=False)
        super().save(*args, **kwargs)


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
        # XS = "xs", _("XS")
        # S = "s", _("S")
        # M = "m", _("M")
        # L = "l", _("L")
        # XL = "xl", _("XL")
        # XXL = "xxl", _("XXL")
        # XXXL = "xxxl", _("XXXL")
        # ONE_SIZE = "one_size", _("One Size")
        OVERSIZE = "oversize", _("Oversize")
    
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
        help_text=_("Product price (USD)")
    )
    
    price_uzs = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Price (UZS)"),
        help_text=_("Product price in Uzbekistani Som (required for Uzbekistan)")
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
        if self.image and getattr(self.image, "_file", None):
            optimize_image(self.image, force=False)

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


class Cart(models.Model):
    """Shopping cart model for users."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_("User")
    )
    
    shipment_amount = models.DecimalField(
        _("Shipment Amount"),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_("Fixed shipping/delivery fee amount")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")
    
    def __str__(self):
        return f"Cart for {self.user.email}"
    
    @property
    def total_items(self):
        """Get total number of items in cart."""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def subtotal_price(self):
        """Calculate subtotal price of all items in cart (without shipment)."""
        from decimal import Decimal
        total = Decimal("0")
        for item in self.items.all():
            total += Decimal(str(item.product.price)) * item.quantity
        return total
    
    @property
    def total_price(self):
        """Calculate total price of all items in cart including shipment."""
        from decimal import Decimal
        subtotal = self.subtotal_price
        shipment = Decimal(str(self.shipment_amount))
        return subtotal + shipment
    
    @property
    def item_count(self):
        """Get count of unique items in cart."""
        return self.items.count()
    
    def update_shipment_amount(self, currency: str = "USD") -> None:
        """Update shipment amount based on currency from DeliveryFee model."""
        from acham.orders.models import DeliveryFee
        from decimal import Decimal
        
        delivery_fee = DeliveryFee.get_fee_for_currency(currency)
        self.shipment_amount = delivery_fee
        self.save(update_fields=['shipment_amount', 'updated_at'])


class CartItem(models.Model):
    """Individual items in a shopping cart."""
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Cart")
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_("Product")
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Quantity"),
        help_text=_("Number of this product in cart")
    )
    
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['cart', 'product']
        ordering = ['-added_at']
        verbose_name = _("Cart Item")
        verbose_name_plural = _("Cart Items")
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.cart}"
    
    @property
    def total_price(self):
        """Calculate total price for this cart item."""
        return self.product.price * self.quantity


class ProductRelation(models.Model):
    """Model for defining relationships between products."""
    
    class RelationType(models.TextChoices):
        COMPLETE_THE_LOOK = "complete_the_look", _("Complete the Look")
        YOU_MAY_ALSO_LIKE = "you_may_also_like", _("You May Also Like")
        FREQUENTLY_BOUGHT_TOGETHER = "frequently_bought_together", _("Frequently Bought Together")
        SIMILAR_PRODUCTS = "similar_products", _("Similar Products")
        ACCESSORIES = "accessories", _("Accessories")
        OUTFIT_COMPLETE = "outfit_complete", _("Outfit Complete")
    
    source_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='related_products',
        verbose_name=_("Source Product")
    )
    
    target_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='related_from_products',
        verbose_name=_("Target Product")
    )
    
    relation_type = models.CharField(
        max_length=30,
        choices=RelationType.choices,
        verbose_name=_("Relation Type"),
        help_text=_("Type of relationship between products")
    )
    
    priority = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Priority"),
        help_text=_("Higher numbers appear first (0 = lowest priority)")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether this relationship is active")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['source_product', 'target_product', 'relation_type']
        ordering = ['-priority', '-created_at']
        verbose_name = _("Product Relation")
        verbose_name_plural = _("Product Relations")
    
    def __str__(self):
        return f"{self.source_product.name} → {self.target_product.name} ({self.get_relation_type_display()})"
