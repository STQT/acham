from rest_framework import generics, filters, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q

from ..models import Product, ProductShot, Collection
from .serializers import (
    ProductSerializer,
    ProductListSerializer,
    ProductShotSerializer,
    CollectionSerializer,
    ChoiceItemSerializer,
    ProductCompleteDetailsSerializer
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
    Retrieve a collection.
    """
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
