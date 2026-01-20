from rest_framework import serializers
from ..models import Product, ProductShot, UserFavorite, ProductShare, Cart, CartItem, Collection


def is_uzbekistan_country(country: str | None) -> bool:
    """Check if country is Uzbekistan."""
    if not country:
        return False
    country_lower = country.lower().strip()
    return country_lower in [
        "uzbekistan", "узбекистан", "o'zbekiston", 
        "ozbekiston", "uzbek", "uz", "uzb"
    ]


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection model."""
    
    product_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()
    
    class Meta:
        model = Collection
        fields = [
            'id',
            'name',
            'image',
            'video',
            'slug',
            'is_active',
            'is_new_arrival',
            'is_featured_banner',
            'product_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_product_count(self, obj):
        """Get the number of available products in this collection."""
        return obj.products.filter(is_available=True).count()

    def get_image(self, obj) -> str | None:
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request:
            return request.build_absolute_uri(url)
        return url
    
    def get_video(self, obj) -> str | None:
        """Get the absolute URL of the video file."""
        if not obj.video:
            return None
        request = self.context.get('request')
        url = obj.video.url
        if request:
            return request.build_absolute_uri(url)
        return url


class ChoiceItemSerializer(serializers.Serializer):
    """Serializer for simple value/label pairs."""
    value = serializers.CharField()
    label = serializers.CharField()


class ProductShotSerializer(serializers.ModelSerializer):
    """Serializer for ProductShot model."""
    
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductShot
        fields = [
            'id',
            'image',
            'alt_text',
            'is_primary',
            'order',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_image(self, obj) -> str | None:
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request:
            return request.build_absolute_uri(url)
        return url


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model with nested shots and collection."""
    
    shots = ProductShotSerializer(many=True, read_only=True)
    collection = CollectionSerializer(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    size_display = serializers.CharField(source='get_size_display', read_only=True)
    is_favorited = serializers.SerializerMethodField()
    favorite_count = serializers.SerializerMethodField()
    share_count = serializers.SerializerMethodField()
    display_price = serializers.SerializerMethodField()
    display_currency = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'collection',
            'name',
            'size',
            'size_display',
            'material',
            'type',
            'type_display',
            'color',
            'short_description',
            'detailed_description',
            'care_instructions',
            'price',
            'price_uzs',
            'display_price',
            'display_currency',
            'is_available',
            'shots',
            'is_favorited',
            'favorite_count',
            'share_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_favorited(self, obj):
        """Check if the current user has favorited this product."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserFavorite.objects.filter(user=request.user, product=obj).exists()
        return False
    
    def get_favorite_count(self, obj):
        """Get the number of users who favorited this product."""
        return obj.favorited_by.count()
    
    def get_share_count(self, obj):
        """Get the number of times this product was shared."""
        return obj.shares.count()
    
    def get_display_price(self, obj):
        """Get display price based on user's country."""
        request = self.context.get('request')
        country = None
        
        if request:
            # Check query parameter first
            country = request.query_params.get('country')
            # If not in query, check header
            if not country:
                country = request.META.get('HTTP_X_COUNTRY') or request.META.get('HTTP_COUNTRY')
        
        if is_uzbekistan_country(country):
            return str(obj.price_uzs)
        return str(obj.price)
    
    def get_display_currency(self, obj):
        """Get display currency based on user's country."""
        request = self.context.get('request')
        country = None
        
        if request:
            # Check query parameter first
            country = request.query_params.get('country')
            # If not in query, check header
            if not country:
                country = request.META.get('HTTP_X_COUNTRY') or request.META.get('HTTP_COUNTRY')
        
        if is_uzbekistan_country(country):
            return 'UZS'
        return 'USD'
    
    def validate_price(self, value):
        """Validate that price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class ProductListSerializer(serializers.ModelSerializer):
    """Simplified serializer for product lists."""
    
    primary_image = serializers.SerializerMethodField()
    shots = ProductShotSerializer(many=True, read_only=True)
    collection = CollectionSerializer(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    size_display = serializers.CharField(source='get_size_display', read_only=True)
    display_price = serializers.SerializerMethodField()
    display_currency = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'collection',
            'name',
            'size',
            'size_display',
            'material',
            'type',
            'type_display',
            'color',
            'short_description',
            'price',
            'price_uzs',
            'display_price',
            'display_currency',
            'is_available',
            'primary_image',
            'shots',
            'created_at'
        ]
    
    def get_primary_image(self, obj) -> str | None:
        """Get the primary image URL for the product."""
        primary_shot = obj.shots.filter(is_primary=True).first()
        if primary_shot:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_shot.image.url)
            return primary_shot.image.url
        return None
    
    def get_display_price(self, obj):
        """Get display price based on user's country."""
        request = self.context.get('request')
        country = None
        
        if request:
            # Check query parameter first
            country = request.query_params.get('country')
            # If not in query, check header
            if not country:
                country = request.META.get('HTTP_X_COUNTRY') or request.META.get('HTTP_COUNTRY')
        
        if is_uzbekistan_country(country):
            return str(obj.price_uzs)
        return str(obj.price)
    
    def get_display_currency(self, obj):
        """Get display currency based on user's country."""
        request = self.context.get('request')
        country = None
        
        if request:
            # Check query parameter first
            country = request.query_params.get('country')
            # If not in query, check header
            if not country:
                country = request.META.get('HTTP_X_COUNTRY') or request.META.get('HTTP_COUNTRY')
        
        if is_uzbekistan_country(country):
            return 'UZS'
        return 'USD'


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products."""
    
    class Meta:
        model = Product
        fields = [
            'name',
            'size',
            'material',
            'type',
            'color',
            'short_description',
            'detailed_description',
            'care_instructions',
            'price',
            'price_uzs',
            'is_available'
        ]
    
    def validate_price(self, value):
        """Validate that price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value
    
    def validate_price_uzs(self, value):
        """Validate that price_uzs is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price (UZS) must be greater than zero.")
        return value


class UserFavoriteSerializer(serializers.ModelSerializer):
    """Serializer for UserFavorite model."""
    
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = UserFavorite
        fields = [
            'id',
            'product',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductShareSerializer(serializers.ModelSerializer):
    """Serializer for ProductShare model."""
    
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    
    class Meta:
        model = ProductShare
        fields = [
            'id',
            'product',
            'platform',
            'platform_display',
            'shared_at',
            'is_successful'
        ]
        read_only_fields = ['id', 'shared_at']


class ProductShareCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating product shares."""
    
    class Meta:
        model = ProductShare
        fields = ['product', 'platform', 'is_successful']
    
    def create(self, validated_data):
        # Set user from request if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for CartItem model."""
    
    product = ProductListSerializer(read_only=True)
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'quantity',
            'total_price',
            'added_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'added_at', 'updated_at']


class CartItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating cart items."""
    
    class Meta:
        model = CartItem
        fields = ['product', 'quantity']
    
    def validate_quantity(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class CartSerializer(serializers.ModelSerializer):
    """Serializer for Cart model."""
    
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    subtotal_price = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()
    shipment_amount_usd = serializers.SerializerMethodField()
    shipment_amount_uzs = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'id',
            'user',
            'items',
            'total_items',
            'subtotal_price',
            'shipment_amount',
            'shipment_amount_usd',
            'shipment_amount_uzs',
            'total_price',
            'item_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_shipment_amount_usd(self, obj):
        """Get delivery fee in USD."""
        from acham.orders.models import DeliveryFee
        from decimal import Decimal
        try:
            fee_usd = DeliveryFee.objects.get(currency="USD", is_active=True)
            return str(fee_usd.amount)
        except DeliveryFee.DoesNotExist:
            return "0"
    
    def get_shipment_amount_uzs(self, obj):
        """Get delivery fee in UZS."""
        from acham.orders.models import DeliveryFee
        from decimal import Decimal
        try:
            fee_uzs = DeliveryFee.objects.get(currency="UZS", is_active=True)
            # Если есть amount_uzs, используем его, иначе amount
            if fee_uzs.amount_uzs is not None:
                return str(fee_uzs.amount_uzs)
            return str(fee_uzs.amount)
        except DeliveryFee.DoesNotExist:
            return "0"


class CartSummarySerializer(serializers.ModelSerializer):
    """Simplified cart serializer for quick overview."""
    
    total_items = serializers.ReadOnlyField()
    subtotal_price = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()
    shipment_amount_usd = serializers.SerializerMethodField()
    shipment_amount_uzs = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'id',
            'total_items',
            'subtotal_price',
            'shipment_amount',
            'shipment_amount_usd',
            'shipment_amount_uzs',
            'total_price',
            'item_count',
            'updated_at'
        ]
    
    def get_shipment_amount_usd(self, obj):
        """Get delivery fee in USD."""
        from acham.orders.models import DeliveryFee
        from decimal import Decimal
        try:
            fee_usd = DeliveryFee.objects.get(currency="USD", is_active=True)
            return str(fee_usd.amount)
        except DeliveryFee.DoesNotExist:
            return "0"
    
    def get_shipment_amount_uzs(self, obj):
        """Get delivery fee in UZS."""
        from acham.orders.models import DeliveryFee
        from decimal import Decimal
        try:
            fee_uzs = DeliveryFee.objects.get(currency="UZS", is_active=True)
            # Если есть amount_uzs, используем его, иначе amount
            if fee_uzs.amount_uzs is not None:
                return str(fee_uzs.amount_uzs)
            return str(fee_uzs.amount)
        except DeliveryFee.DoesNotExist:
            return "0"


class ProductCompleteDetailsSerializer(serializers.Serializer):
    """Serializer describing the complete product details response."""
    product = ProductSerializer()
    shots = ProductShotSerializer(many=True)
    metadata = serializers.DictField()
