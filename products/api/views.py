from rest_framework import generics, filters, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q

from ..models import Product, ProductShot, Collection, UserFavorite, ProductShare, Cart, CartItem, ProductRelation
from .serializers import (
    ProductSerializer,
    ProductListSerializer,
    ProductShotSerializer,
    CollectionSerializer,
    ChoiceItemSerializer,
    ProductCompleteDetailsSerializer,
    UserFavoriteSerializer,
    ProductShareSerializer,
    ProductShareCreateSerializer,
    CartSerializer,
    CartItemSerializer,
    CartItemCreateUpdateSerializer,
    CartSummarySerializer
)


class ProductListView(generics.ListAPIView):
    """
    List all products.
    """
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'material', 'color', 'short_description']
    ordering_fields = ['name', 'price', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = Product.objects.all()
        
        # Filter by type
        product_type = self.request.query_params.get('type')
        if product_type:
            queryset = queryset.filter(type=product_type)
        
        # Filter by size
        size = self.request.query_params.get('size')
        if size:
            queryset = queryset.filter(size=size)
        
        # Filter by color
        color = self.request.query_params.get('color')
        if color:
            queryset = queryset.filter(color__icontains=color)
        
        # Filter by material
        material = self.request.query_params.get('material')
        if material:
            queryset = queryset.filter(material__icontains=material)
        
        # Filter by availability
        is_available = self.request.query_params.get('is_available')
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() == 'true')
        
        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    """
    Retrieve a product.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductShotListView(generics.ListAPIView):
    """
    List all shots for a product.
    """
    serializer_class = ProductShotSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'created_at']
    ordering = ['order', 'created_at']
    
    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return ProductShot.objects.filter(product_id=product_id)


class ProductShotDetailView(generics.RetrieveAPIView):
    """
    Retrieve a product shot.
    """
    serializer_class = ProductShotSerializer
    
    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return ProductShot.objects.filter(product_id=product_id)


@extend_schema(
    operation_id='products_product_search',
    tags=['products'],
    summary='Advanced product search',
    description='Search products with multiple filters including text, type, size, color, and price range.',
    responses={200: ProductListSerializer(many=True)},
    parameters=[
        OpenApiParameter(name='q', description='Search query', required=False, type=str),
        OpenApiParameter(name='type', description='Product type', required=False, type=str),
        OpenApiParameter(name='size', description='Product size', required=False, type=str),
        OpenApiParameter(name='color', description='Product color', required=False, type=str),
        OpenApiParameter(name='min_price', description='Minimum price', required=False, type=float),
        OpenApiParameter(name='max_price', description='Maximum price', required=False, type=float),
        OpenApiParameter(name='available_only', description='Show only available products', required=False, type=bool),
    ]
)
@api_view(['GET'])
def product_search(request):
    """
    Advanced search endpoint for products.
    """
    query = request.GET.get('q', '')
    product_type = request.GET.get('type', '')
    size = request.GET.get('size', '')
    color = request.GET.get('color', '')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    available_only = request.GET.get('available_only', 'true').lower() == 'true'
    
    queryset = Product.objects.all()
    
    # Text search
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(material__icontains=query) |
            Q(color__icontains=query) |
            Q(short_description__icontains=query) |
            Q(detailed_description__icontains=query)
        )
    
    # Filter by type
    if product_type:
        queryset = queryset.filter(type=product_type)
    
    # Filter by size
    if size:
        queryset = queryset.filter(size=size)
    
    # Filter by color
    if color:
        queryset = queryset.filter(color__icontains=color)
    
    # Price range filter
    if min_price:
        try:
            queryset = queryset.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            queryset = queryset.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Availability filter
    if available_only:
        queryset = queryset.filter(is_available=True)
    
    # Order by creation date
    queryset = queryset.order_by('-created_at')
    
    serializer = ProductListSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


@extend_schema(
    operation_id='products_product_types',
    tags=['products'],
    summary='Get product types',
    description='Get available product types and their choices.',
    responses={200: ChoiceItemSerializer(many=True)}
)
@api_view(['GET'])
def product_types(request):
    """
    Get available product types and their choices.
    """
    types = [{'value': choice[0], 'label': choice[1]} for choice in Product.ProductType.choices]
    return Response(types)


@extend_schema(
    operation_id='products_product_sizes',
    tags=['products'],
    summary='Get product sizes',
    description='Get available product sizes and their choices.',
    responses={200: ChoiceItemSerializer(many=True)}
)
@api_view(['GET'])
def product_sizes(request):
    """
    Get available product sizes and their choices.
    """
    sizes = [{'value': choice[0], 'label': choice[1]} for choice in Product.ProductSize.choices]
    return Response(sizes)


@extend_schema(
    operation_id='products_product_complete_details',
    tags=['products'],
    summary='Get complete product details',
    description='Get comprehensive product information including all shots, available types, sizes, and search options.',
    responses={200: ProductCompleteDetailsSerializer}
)
@api_view(['GET'])
def product_complete_details(request, pk):
    """
    Get complete product details including all related information.
    """
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get product details
    product_serializer = ProductSerializer(product, context={'request': request})
    
    # Get all shots for this product
    shots = ProductShot.objects.filter(product=product).order_by('order', 'created_at')
    shots_serializer = ProductShotSerializer(shots, many=True, context={'request': request})
    
    # Get available types and sizes
    types = [{'value': choice[0], 'label': choice[1]} for choice in Product.ProductType.choices]
    sizes = [{'value': choice[0], 'label': choice[1]} for choice in Product.ProductSize.choices]
    
    # Get all active collections
    collections = Collection.objects.filter(is_active=True)
    collections_serializer = CollectionSerializer(collections, many=True)
    
    # Build complete response
    response_data = {
        'product': product_serializer.data,
        'shots': shots_serializer.data,
        'metadata': {
            'available_types': types,
            'available_sizes': sizes,
            'collections': collections_serializer.data,
            'search_fields': ['name', 'material', 'color', 'short_description'],
            'filter_options': {
                'type': [choice[0] for choice in Product.ProductType.choices],
                'size': [choice[0] for choice in Product.ProductSize.choices],
                'availability': [True, False]
            }
        }
    }
    
    return Response(response_data)


@extend_schema(
    operation_id='products_collection_list',
    tags=['collections'],
    summary='List collections',
    description='Get all active collections.',
    responses={200: CollectionSerializer(many=True)}
)
class CollectionListView(generics.ListAPIView):
    """
    List all active collections.
    """
    queryset = Collection.objects.filter(is_active=True)
    serializer_class = CollectionSerializer
    ordering = ['-created_at']


@extend_schema(
    operation_id='products_collection_detail',
    tags=['collections'],
    summary='Get collection details',
    description='Retrieve details of a specific collection.',
    responses={200: CollectionSerializer}
)
class CollectionDetailView(generics.RetrieveAPIView):
    """
    Retrieve a collection with its products.
    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        collection = self.get_object()
        context['collection'] = collection
        return context


class CollectionProductsView(generics.ListAPIView):
    """
    List products in a specific collection with search and filtering.
    """
    serializer_class = ProductListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'material', 'color', 'short_description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get products from the specified collection."""
        collection_id = self.kwargs['collection_id']
        return Product.objects.filter(
            collection_id=collection_id,
            is_available=True
        ).select_related('collection').prefetch_related('shots')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        try:
            collection = Collection.objects.get(id=self.kwargs['collection_id'])
            context['collection'] = collection
        except Collection.DoesNotExist:
            pass
        return context


class NewArrivalsListView(generics.ListAPIView):
    """
    List products from new arrival collections.
    """
    serializer_class = ProductListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'material', 'color', 'short_description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get products from collections marked as new arrivals."""
        return Product.objects.filter(
            collection__is_new_arrival=True,
            collection__is_active=True,
            is_available=True
        ).select_related('collection').prefetch_related('shots')


@api_view(['GET'])
def new_arrivals_collections(request):
    """
    Get collections marked as new arrivals.
    """
    collections = Collection.objects.filter(
        is_new_arrival=True,
        is_active=True
    ).order_by('-created_at')
    
    serializer = CollectionSerializer(collections, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def new_arrivals_page(request):
    """
    Get complete new arrivals page data including collections and products.
    """
    # Get new arrival collections
    collections = Collection.objects.filter(
        is_new_arrival=True,
        is_active=True
    ).order_by('-created_at')
    
    # Get products from new arrival collections
    products = Product.objects.filter(
        collection__is_new_arrival=True,
        collection__is_active=True,
        is_available=True
    ).select_related('collection').prefetch_related('shots').order_by('-created_at')
    
    # Serialize data
    collections_data = CollectionSerializer(collections, many=True, context={'request': request}).data
    products_data = ProductListSerializer(products, many=True, context={'request': request}).data
    
    return Response({
        'collections': collections_data,
        'products': products_data,
        'total_collections': len(collections_data),
        'total_products': len(products_data)
    })


@api_view(['GET'])
def collection_page(request, collection_id):
    """
    Get complete collection page data including collection details and products.
    """
    try:
        collection = Collection.objects.get(id=collection_id)
    except Collection.DoesNotExist:
        return Response({'error': 'Collection not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get products from the collection
    products = Product.objects.filter(
        collection=collection,
        is_available=True
    ).select_related('collection').prefetch_related('shots').order_by('-created_at')
    
    # Apply search if provided
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(material__icontains=search_query) |
            Q(color__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    # Apply filtering
    product_type = request.GET.get('type')
    if product_type:
        products = products.filter(type=product_type)
    
    size = request.GET.get('size')
    if size:
        products = products.filter(size=size)
    
    color = request.GET.get('color')
    if color:
        products = products.filter(color__icontains=color)
    
    # Apply price range filtering
    min_price = request.GET.get('min_price')
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    max_price = request.GET.get('max_price')
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Serialize data
    collection_data = CollectionSerializer(collection, context={'request': request}).data
    products_data = ProductListSerializer(products, many=True, context={'request': request}).data
    
    return Response({
        'collection': collection_data,
        'products': products_data,
        'total_products': products.count(),
        'search_query': search_query,
        'filters': {
            'type': product_type,
            'size': size,
            'color': color,
            'min_price': min_price,
            'max_price': max_price
        }
    })


@api_view(['GET'])
def search_collections(request):
    """
    Search collections by name.
    """
    search_query = request.GET.get('q', '')
    
    if not search_query:
        return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    collections = Collection.objects.filter(
        Q(name__icontains=search_query) |
        Q(slug__icontains=search_query),
        is_active=True
    ).order_by('-created_at')
    
    serializer = CollectionSerializer(collections, many=True, context={'request': request})
    return Response({
        'collections': serializer.data,
        'total_collections': collections.count(),
        'search_query': search_query
    })


# Favorites and Shares Views

class UserFavoriteListCreateView(generics.ListCreateAPIView):
    """
    List user's favorites or add a product to favorites.
    """
    serializer_class = UserFavoriteSerializer
    
    def get_queryset(self):
        return UserFavorite.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserFavoriteDestroyView(generics.DestroyAPIView):
    """
    Remove a product from user's favorites.
    """
    serializer_class = UserFavoriteSerializer
    
    def get_queryset(self):
        return UserFavorite.objects.filter(user=self.request.user)


@extend_schema(
    operation_id='toggle_favorite',
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
            return Response({'message': 'Product already in favorites'}, status=status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        try:
            favorite = UserFavorite.objects.get(user=request.user, product=product)
            favorite.delete()
            return Response({'message': 'Product removed from favorites'}, status=status.HTTP_200_OK)
        except UserFavorite.DoesNotExist:
            return Response({'message': 'Product not in favorites'}, status=status.HTTP_200_OK)


class ProductShareCreateView(generics.CreateAPIView):
    """
    Create a product share record.
    """
    serializer_class = ProductShareCreateSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)


@api_view(['GET'])
def product_share_stats(request, product_id):
    """
    Get sharing statistics for a product.
    """
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get share counts by platform
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


@api_view(['GET'])
def user_favorites(request):
    """
    Get current user's favorite products.
    """
    favorites = UserFavorite.objects.filter(user=request.user)
    serializer = UserFavoriteSerializer(favorites, many=True, context={'request': request})
    return Response(serializer.data)


# Cart Views

class CartDetailView(generics.RetrieveAPIView):
    """
    Get user's cart with all items.
    """
    serializer_class = CartSerializer
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartSummaryView(generics.RetrieveAPIView):
    """
    Get cart summary (total items, price, etc.).
    """
    serializer_class = CartSummarySerializer
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartItemListCreateView(generics.ListCreateAPIView):
    """
    List cart items or add item to cart.
    """
    serializer_class = CartItemSerializer
    
    def get_queryset(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)
    
    def perform_create(self, serializer):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=cart)


class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or remove cart item.
    """
    serializer_class = CartItemSerializer
    
    def get_queryset(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)


@extend_schema(
    operation_id='add_to_cart',
    summary='Add product to cart',
    description='Add a product to user cart or update quantity if already exists',
    responses={
        201: {'description': 'Product added to cart'},
        200: {'description': 'Product quantity updated in cart'},
        404: {'description': 'Product not found'},
        400: {'description': 'Invalid request data'}
    }
)
@api_view(['POST'])
def add_to_cart(request, product_id):
    """
    Add product to cart or update quantity if already exists.
    """
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if not product.is_available:
        return Response({'error': 'Product is not available'}, status=status.HTTP_400_BAD_REQUEST)
    
    quantity = request.data.get('quantity', 1)
    if quantity <= 0:
        return Response({'error': 'Quantity must be greater than zero'}, status=status.HTTP_400_BAD_REQUEST)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    serializer = CartItemSerializer(cart_item, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@extend_schema(
    operation_id='remove_from_cart',
    summary='Remove product from cart',
    description='Remove a product from user cart',
    responses={
        200: {'description': 'Product removed from cart'},
        404: {'description': 'Product or cart not found'}
    }
)
@api_view(['DELETE'])
def remove_from_cart(request, product_id):
    """
    Remove product from cart.
    """
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.delete()
        return Response({'message': 'Product removed from cart'}, status=status.HTTP_200_OK)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
    except CartItem.DoesNotExist:
        return Response({'error': 'Product not in cart'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    operation_id='update_cart_item_quantity',
    summary='Update cart item quantity',
    description='Update the quantity of a product in user cart',
    responses={
        200: {'description': 'Cart item quantity updated'},
        404: {'description': 'Product or cart not found'},
        400: {'description': 'Invalid quantity'}
    }
)
@api_view(['PUT'])
def update_cart_item_quantity(request, product_id):
    """
    Update quantity of a product in cart.
    """
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    quantity = request.data.get('quantity')
    if quantity is None or quantity <= 0:
        return Response({'error': 'Valid quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = CartItemSerializer(cart_item, context={'request': request})
        return Response(serializer.data)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
    except CartItem.DoesNotExist:
        return Response({'error': 'Product not in cart'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    operation_id='clear_cart',
    summary='Clear user cart',
    description='Remove all items from user cart',
    responses={
        200: {'description': 'Cart cleared successfully'},
        404: {'description': 'Cart not found'}
    }
)
@api_view(['DELETE'])
def clear_cart(request):
    """
    Remove all items from cart.
    """
    try:
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
        return Response({'message': 'Cart cleared'}, status=status.HTTP_200_OK)
    except Cart.DoesNotExist:
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)


# Product Relations and Recommendations

@api_view(['GET'])
def complete_the_look(request, product_id):
    """
    Get products that complete the look for a specific product.
    """
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get manually curated "Complete the Look" products
    curated_products = Product.objects.filter(
        related_from_products__source_product=product,
        related_from_products__relation_type=ProductRelation.RelationType.COMPLETE_THE_LOOK,
        related_from_products__is_active=True,
        is_available=True
    ).order_by('-related_from_products__priority', '-related_from_products__created_at').distinct()
    
    # If no curated products, use smart recommendations
    if not curated_products.exists():
        curated_products = get_smart_complete_the_look_recommendations(product)
    
    serializer = ProductListSerializer(curated_products[:6], many=True, context={'request': request})
    
    return Response({
        'source_product': ProductListSerializer(product, context={'request': request}).data,
        'complete_the_look': serializer.data,
        'total_products': len(serializer.data)
    })


def get_smart_complete_the_look_recommendations(source_product):
    """
    Generate smart "Complete the Look" recommendations based on product type and collection.
    """
    recommendations = []
    
    # Get products from the same collection (different types)
    same_collection = Product.objects.filter(
        collection=source_product.collection,
        is_available=True
    ).exclude(id=source_product.id)
    
    # Smart type matching logic
    if source_product.type == 'shoes':
        # For shoes, recommend: bags, accessories, clothing
        recommendations.extend(
            same_collection.filter(
                Q(type__in=['bags', 'accessories', 'clothing']) |
                Q(material__icontains=source_product.material)
            )[:3]
        )
    elif source_product.type == 'clothing':
        # For clothing, recommend: shoes, bags, accessories
        recommendations.extend(
            same_collection.filter(
                Q(type__in=['shoes', 'bags', 'accessories']) |
                Q(color__icontains=source_product.color)
            )[:3]
        )
    elif source_product.type == 'bags':
        # For bags, recommend: shoes, accessories, clothing
        recommendations.extend(
            same_collection.filter(
                Q(type__in=['shoes', 'accessories', 'clothing']) |
                Q(color__icontains=source_product.color)
            )[:3]
        )
    else:
        # For other types, recommend complementary items
        recommendations.extend(same_collection[:3])
    
    # If not enough from same collection, get from similar collections
    if len(recommendations) < 3:
        similar_products = Product.objects.filter(
            Q(collection__is_new_arrival=source_product.collection.is_new_arrival) |
            Q(type__in=['shoes', 'bags', 'accessories']),
            is_available=True
        ).exclude(id=source_product.id).exclude(id__in=[p.id for p in recommendations])[:3-len(recommendations)]
        
        recommendations.extend(similar_products)
    
    return recommendations


def get_smart_recommendations_same_collection(source_product):
    """
    Generate smart "You May Also Like" recommendations prioritizing same collection.
    """
    # First priority: Same collection products
    same_collection_products = Product.objects.filter(
        collection=source_product.collection,
        is_available=True
    ).exclude(id=source_product.id).order_by('-created_at')[:8]
    
    if same_collection_products.count() >= 6:
        return same_collection_products[:6]
    
    # If not enough from same collection, add similar products from other collections
    similar_products = Product.objects.filter(
        Q(type=source_product.type) |
        Q(color__icontains=source_product.color) |
        Q(material__icontains=source_product.material),
        is_available=True
    ).exclude(id=source_product.id).exclude(collection=source_product.collection).distinct()[:8-same_collection_products.count()]
    
    # Combine same collection + similar products
    recommendations = list(same_collection_products) + list(similar_products)
    return recommendations[:8]


def get_smart_recommendations(source_product):
    """
    Generate smart "You May Also Like" recommendations (legacy function for complete-the-look).
    """
    # Get products with similar characteristics
    similar_products = Product.objects.filter(
        Q(collection=source_product.collection) |
        Q(type=source_product.type) |
        Q(color__icontains=source_product.color) |
        Q(material__icontains=source_product.material),
        is_available=True
    ).exclude(id=source_product.id).distinct()[:8]
    
    return similar_products


@api_view(['GET'])
def product_recommendations(request, product_id):
    """
    Get all types of recommendations for a product, prioritizing same collection.
    """
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get complete the look products (prioritize same collection)
    complete_look = Product.objects.filter(
        related_from_products__source_product=product,
        related_from_products__relation_type=ProductRelation.RelationType.COMPLETE_THE_LOOK,
        related_from_products__is_active=True,
        is_available=True
    ).order_by('-related_from_products__priority')[:6]
    
    if not complete_look.exists():
        complete_look = get_smart_complete_the_look_recommendations(product)
    
    # Get you may also like products (prioritize same collection)
    also_like = Product.objects.filter(
        related_from_products__source_product=product,
        related_from_products__relation_type=ProductRelation.RelationType.YOU_MAY_ALSO_LIKE,
        related_from_products__is_active=True,
        is_available=True
    ).order_by('-related_from_products__priority')[:8]
    
    if not also_like.exists():
        also_like = get_smart_recommendations_same_collection(product)
    
    return Response({
        'source_product': ProductListSerializer(product, context={'request': request}).data,
        'complete_the_look': ProductListSerializer(complete_look, many=True, context={'request': request}).data,
        'you_may_also_like': ProductListSerializer(also_like, many=True, context={'request': request}).data
    })
