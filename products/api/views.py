from rest_framework import generics, filters, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q

from ..models import Product, ProductShot
from .serializers import (
    ProductSerializer,
    ProductListSerializer,
    ProductCreateUpdateSerializer,
    ProductShotSerializer
)


class ProductListCreateView(generics.ListCreateAPIView):
    """
    List all products or create a new product.
    """
    queryset = Product.objects.all()
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
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateUpdateSerializer
        return ProductListSerializer


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product.
    """
    queryset = Product.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductSerializer


class ProductShotListCreateView(generics.ListCreateAPIView):
    """
    List all shots for a product or create a new shot.
    """
    serializer_class = ProductShotSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'created_at']
    ordering = ['order', 'created_at']
    
    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return ProductShot.objects.filter(product_id=product_id)
    
    def perform_create(self, serializer):
        product_id = self.kwargs['product_id']
        product = Product.objects.get(id=product_id)
        serializer.save(product=product)


class ProductShotDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product shot.
    """
    serializer_class = ProductShotSerializer
    
    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return ProductShot.objects.filter(product_id=product_id)


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


@api_view(['GET'])
def product_types(request):
    """
    Get available product types and their choices.
    """
    types = [{'value': choice[0], 'label': choice[1]} for choice in Product.ProductType.choices]
    return Response(types)


@api_view(['GET'])
def product_sizes(request):
    """
    Get available product sizes and their choices.
    """
    sizes = [{'value': choice[0], 'label': choice[1]} for choice in Product.ProductSize.choices]
    return Response(sizes)
