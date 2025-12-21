from rest_framework import serializers
from ..models import Banner, FAQ, StaticPage, ContactMessage

class BannerSerializer(serializers.ModelSerializer):
    """Serializer for Banner model."""
    
    class Meta:
        model = Banner
        fields = [
            'id',
            'title',
            'video',
            'image',
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
    
    class Meta:
        model = StaticPage
        fields = [
            'id',
            'page_type',
            'title',
            'content',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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
            'subscribe_to_newsletter',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

