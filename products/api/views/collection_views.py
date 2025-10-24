from rest_framework import generics, filters, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.db.models import Q

from ...models import Product, Collection
from ..serializers import (
    ProductListSerializer,
    CollectionSerializer
)


@extend_schema(
    operation_id='products_collection_list',
    tags=['Collections'],
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
    tags=['Collections'],
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


class CollectionProductsView(generics.ListAPIView):
    """
    List products within a specific collection with search and filtering.
    """
    serializer_class = ProductListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'material', 'color', 'short_description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get products for a specific collection."""
        collection_id = self.kwargs['collection_id']
        return Product.objects.filter(
            collection_id=collection_id,
            is_available=True
        ).select_related('collection').prefetch_related('shots')
    
    def get_serializer_context(self):
        """Add collection context to serializer."""
        context = super().get_serializer_context()
        try:
            collection = Collection.objects.get(id=self.kwargs['collection_id'])
            context['collection'] = collection
        except Collection.DoesNotExist:
            pass
        return context


@extend_schema(
    tags=["New Arrivals"],
    summary="List new arrival products",
    description="Get products from collections marked as new arrivals"
)
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


@extend_schema(
    tags=["Collections"],
    summary="Get collection page data",
    description="Get complete collection page with products and search options"
)
@api_view(['GET'])
def collection_page(request, collection_id):
    """
    Get complete collection page data (collection + products with search/filter).
    """
    try:
        collection = Collection.objects.get(id=collection_id)
    except Collection.DoesNotExist:
        return Response({'error': 'Collection not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get products in collection
    products = Product.objects.filter(
        collection=collection,
        is_available=True
    ).select_related('collection').prefetch_related('shots')
    
    # Apply search filter if provided
    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(material__icontains=search_query) |
            Q(color__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    # Apply ordering
    ordering = request.GET.get('ordering', '-created_at')
    products = products.order_by(ordering)
    
    # Serialize data
    collection_serializer = CollectionSerializer(collection, context={'request': request})
    products_serializer = ProductListSerializer(products, many=True, context={'request': request})
    
    return Response({
        'collection': collection_serializer.data,
        'products': products_serializer.data,
        'search_query': search_query,
        'total_products': products.count()
    })


@extend_schema(
    tags=["Collections"],
    summary="Search collections",
    description="Search collections by name"
)
@api_view(['GET'])
def search_collections(request):
    """
    Search collections by name.
    """
    search_query = request.GET.get('q', '')
    
    if not search_query:
        return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    collections = Collection.objects.filter(
        name__icontains=search_query,
        is_active=True
    ).order_by('-created_at')
    
    serializer = CollectionSerializer(collections, many=True, context={'request': request})
    
    return Response({
        'collections': serializer.data,
        'search_query': search_query,
        'total_collections': collections.count()
    })


@extend_schema(
    tags=["New Arrivals"],
    summary="Get new arrival collections",
    description="Get collections marked as new arrivals"
)
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
    
    return Response({
        'collections': serializer.data,
        'total_collections': collections.count()
    })


@extend_schema(
    tags=["New Arrivals"],
    summary="Get new arrivals page data",
    description="Get complete new arrivals page with collections and products"
)
@api_view(['GET'])
def new_arrivals_page(request):
    """
    Get complete new arrivals page data (collections + products).
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
    
    # Apply search filter if provided
    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(material__icontains=search_query) |
            Q(color__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    # Serialize data
    collections_serializer = CollectionSerializer(collections, many=True, context={'request': request})
    products_serializer = ProductListSerializer(products, many=True, context={'request': request})
    
    return Response({
        'collections': collections_serializer.data,
        'products': products_serializer.data,
        'search_query': search_query,
        'total_collections': collections.count(),
        'total_products': products.count()
    })
