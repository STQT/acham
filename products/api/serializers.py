from rest_framework import serializers
from ..models import Product, ProductShot, Collection, Banner


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection model."""
    
    class Meta:
        model = Collection
        fields = [
            'id',
            'name',
            'image',
            'description',
            'slug',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BannerSerializer(serializers.ModelSerializer):
    """Serializer for Banner model."""
    
    video_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Banner
        fields = [
            'id',
            'title',
            'video',
            'video_url',
            'image',
            'image_url',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_video_url(self, obj) -> str | None:
        """Get the video URL for the banner."""
        if obj.video:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video.url)
            return obj.video.url
        return None


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
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
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


class ProductCompleteDetailsSerializer(serializers.Serializer):
    """Serializer describing the complete product details response."""
    product = ProductSerializer()
    shots = ProductShotSerializer(many=True)
    metadata = serializers.DictField()
