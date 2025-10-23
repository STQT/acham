from rest_framework import serializers
from ..models import Banner

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