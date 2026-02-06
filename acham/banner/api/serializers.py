from rest_framework import serializers
from ..models import FAQ, StaticPage, ContactMessage, ReturnRequest, EmailSubscription, AboutPageSection

class FAQSerializer(serializers.ModelSerializer):
    """Serializer for FAQ model."""
    
    class Meta:
        model = FAQ
        fields = [
            'id',
            'question',
            'answer',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StaticPageSerializer(serializers.ModelSerializer):
    """Serializer for StaticPage model."""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = StaticPage
        fields = [
            'id',
            'page_type',
            'title',
            'image',
            'image_url',
            'content',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'image_url']
    
    def get_image_url(self, obj):
        """Get the full URL for the image."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for ContactMessage model."""
    
    class Meta:
        model = ContactMessage
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone',
            'subject',
            'message',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReturnRequestSerializer(serializers.ModelSerializer):
    """Serializer for ReturnRequest model."""
    
    class Meta:
        model = ReturnRequest
        fields = [
            'id',
            'order_number',
            'email_or_phone',
            'message',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmailSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for EmailSubscription model."""
    
    class Meta:
        model = EmailSubscription
        fields = [
            'id',
            'email',
            'language',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']


class AboutPageSectionSerializer(serializers.ModelSerializer):
    """Serializer for AboutPageSection singleton model."""
    
    # Hero section image URLs
    hero_image_url = serializers.SerializerMethodField()
    
    # History section image URLs
    history_image_url = serializers.SerializerMethodField()
    
    # Philosophy section image URLs
    philosophy_image_url = serializers.SerializerMethodField()
    
    # Fabrics section image URLs
    fabrics_image_url = serializers.SerializerMethodField()
    fabrics_image_2_url = serializers.SerializerMethodField()
    fabrics_image_3_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AboutPageSection
        fields = [
            'id',
            # Hero section
            'founder_name',
            'founder_title',
            'hero_image',
            'hero_image_url',
            # History section
            'history_title',
            'history_content',
            'history_image',
            'history_image_url',
            # Philosophy section
            'philosophy_title',
            'philosophy_content',
            'philosophy_image',
            'philosophy_image_url',
            # Fabrics section
            'fabrics_title',
            'fabrics_content',
            'fabrics_image',
            'fabrics_image_url',
            'fabrics_image_2',
            'fabrics_image_2_url',
            'fabrics_image_3',
            'fabrics_image_3_url',
            # Process section
            'process_title',
            'process_description',
            'process_items',
            # Common fields
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'hero_image_url',
            'history_image_url',
            'philosophy_image_url',
            'fabrics_image_url',
            'fabrics_image_2_url',
            'fabrics_image_3_url'
        ]
    
    def get_hero_image_url(self, obj):
        """Get the full URL for the hero image."""
        if obj.hero_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.hero_image.url)
            return obj.hero_image.url
        return None
    
    def get_history_image_url(self, obj):
        """Get the full URL for the history image."""
        if obj.history_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.history_image.url)
            return obj.history_image.url
        return None
    
    def get_philosophy_image_url(self, obj):
        """Get the full URL for the philosophy image."""
        if obj.philosophy_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.philosophy_image.url)
            return obj.philosophy_image.url
        return None
    
    def get_fabrics_image_url(self, obj):
        """Get the full URL for fabrics image."""
        if obj.fabrics_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fabrics_image.url)
            return obj.fabrics_image.url
        return None
    
    def get_fabrics_image_2_url(self, obj):
        """Get the full URL for fabrics image_2."""
        if obj.fabrics_image_2:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fabrics_image_2.url)
            return obj.fabrics_image_2.url
        return None
    
    def get_fabrics_image_3_url(self, obj):
        """Get the full URL for fabrics image_3."""
        if obj.fabrics_image_3:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.fabrics_image_3.url)
            return obj.fabrics_image_3.url
        return None

