from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from ...models import Product, UserFavorite, ProductShare
from ..serializers import (
    UserFavoriteSerializer,
    ProductShareSerializer,
    ProductShareCreateSerializer
)


@extend_schema(
    tags=["Favorites"],
    summary="Manage user favorites",
    description="List user's favorite products or add a product to favorites"
)
class UserFavoriteListCreateView(generics.ListCreateAPIView):
    """
    List user's favorites or add a product to favorites.
    """
    serializer_class = UserFavoriteSerializer
    
    def get_queryset(self):
        return UserFavorite.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(
    tags=["Favorites"],
    summary="Remove from favorites",
    description="Remove a product from user's favorites"
)
class UserFavoriteDestroyView(generics.DestroyAPIView):
    """
    Remove a product from user's favorites.
    """
    serializer_class = UserFavoriteSerializer
    
    def get_queryset(self):
        return UserFavorite.objects.filter(user=self.request.user).order_by('-created_at')


@extend_schema(
    operation_id='toggle_favorite',
    tags=['Favorites'],
    summary='Toggle product favorite status',
    description='Add or remove a product from user favorites',
    responses={
        200: {'description': 'Product favorite status updated'},
        201: {'description': 'Product added to favorites'},
        404: {'description': 'Product not found'}
    }
)
@api_view(['POST', 'DELETE'])
def toggle_favorite(request, product_id):
    """
    Toggle favorite status for a product.
    POST: Add to favorites
    DELETE: Remove from favorites
    """
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'POST':
        favorite, created = UserFavorite.objects.get_or_create(
            user=request.user,
            product=product
        )
        if created:
            return Response({'message': 'Product added to favorites'}, status=status.HTTP_201_CREATED)
        else:
            # Обновляем created_at, чтобы товар переместился в начало списка
            from django.utils import timezone
            favorite.created_at = timezone.now()
            favorite.save(update_fields=['created_at'])
            return Response({'message': 'Product already in favorites'}, status=status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        try:
            favorite = UserFavorite.objects.get(user=request.user, product=product)
            favorite.delete()
            return Response({'message': 'Product removed from favorites'}, status=status.HTTP_200_OK)
        except UserFavorite.DoesNotExist:
            return Response({'message': 'Product not in favorites'}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Sharing"],
    summary="Create product share",
    description="Record a product share action"
)
class ProductShareCreateView(generics.CreateAPIView):
    """
    Create a product share record.
    """
    serializer_class = ProductShareCreateSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)


@extend_schema(
    tags=["Sharing"],
    summary="Get share statistics",
    description="Get sharing statistics for a product"
)
@api_view(['GET'])
def product_share_stats(request, product_id):
    """
    Get sharing statistics for a product.
    """
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get share statistics by platform
    share_stats = {}
    for platform, _ in ProductShare.SharePlatform.choices:
        count = ProductShare.objects.filter(product=product, platform=platform).count()
        if count > 0:
            share_stats[platform] = count
    
    total_shares = ProductShare.objects.filter(product=product).count()
    
    return Response({
        'product_id': product.id,
        'total_shares': total_shares,
        'platform_stats': share_stats
    })


@extend_schema(
    tags=["Favorites"],
    summary="Get user favorites",
    description="Get current user's favorite products"
)
@api_view(['GET'])
def user_favorites(request):
    """
    Get current user's favorite products.
    """
    favorites = UserFavorite.objects.filter(user=request.user).order_by('-created_at')
    serializer = UserFavoriteSerializer(favorites, many=True, context={'request': request})
    return Response(serializer.data)
