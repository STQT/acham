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
    """Serializer for AboutPageSection model."""
    hero_image_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    image_2_url = serializers.SerializerMethodField()
    image_3_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AboutPageSection
        fields = [
            'id',
            'section_type',
            'founder_name',
            'founder_title',
            'hero_image',
            'hero_image_url',
            'title',
            'content',
            'image',
            'image_url',
            'image_2',
            'image_2_url',
            'image_3',
            'image_3_url',
            'process_description',
            'process_items',
            'is_active',
            'order',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'hero_image_url',
            'image_url',
            'image_2_url',
            'image_3_url'
        ]
    
    def get_hero_image_url(self, obj):
        """Get the full URL for the hero image."""
        if obj.hero_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.hero_image.url)
            return obj.hero_image.url
        return None
    
    def get_image_url(self, obj):
        """Get the full URL for the image."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_image_2_url(self, obj):
        """Get the full URL for image_2."""
        if obj.image_2:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_2.url)
            return obj.image_2.url
        return None
    
    def get_image_3_url(self, obj):
        """Get the full URL for image_3."""
        if obj.image_3:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_3.url)
            return obj.image_3.url
        return None

