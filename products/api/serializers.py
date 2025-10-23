from rest_framework import serializers
from ..models import Product, ProductShot, UserFavorite, ProductShare


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection model."""
    
    class Meta:
        model = Collection
        fields = [
            'id',
            'name',
            'image',
            'slug',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChoiceItemSerializer(serializers.Serializer):
    """Serializer for simple value/label pairs."""
    value = serializers.CharField()
    label = serializers.CharField()


class ProductShotSerializer(serializers.ModelSerializer):
    """Serializer for ProductShot model."""
    
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


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model with nested shots and collection."""
    
    shots = ProductShotSerializer(many=True, read_only=True)
    collection = CollectionSerializer(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    size_display = serializers.CharField(source='get_size_display', read_only=True)
    is_favorited = serializers.SerializerMethodField()
    favorite_count = serializers.SerializerMethodField()
    share_count = serializers.SerializerMethodField()
    
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
    
    def validate_price(self, value):
        """Validate that price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class ProductListSerializer(serializers.ModelSerializer):
    """Simplified serializer for product lists."""
    
    primary_image = serializers.SerializerMethodField()
    collection = CollectionSerializer(read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    size_display = serializers.CharField(source='get_size_display', read_only=True)
    
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
            'is_available',
            'primary_image',
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
            'is_available'
        ]
    
    def validate_price(self, value):
        """Validate that price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
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


class ProductCompleteDetailsSerializer(serializers.Serializer):
    """Serializer describing the complete product details response."""
    product = ProductSerializer()
    shots = ProductShotSerializer(many=True)
    metadata = serializers.DictField()
