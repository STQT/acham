from rest_framework import serializers
from ..models import Product, ProductShot


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
    """Serializer for Product model with nested shots."""
    
    shots = ProductShotSerializer(many=True, read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    size_display = serializers.CharField(source='get_size_display', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id',
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
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    size_display = serializers.CharField(source='get_size_display', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id',
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
    
    def get_primary_image(self, obj):
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
