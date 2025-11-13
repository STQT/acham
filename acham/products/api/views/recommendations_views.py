from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.db.models import Q

from ...models import Product, ProductRelation
from ..serializers import ProductListSerializer


@extend_schema(
    operation_id='complete_the_look',
    tags=['Recommendations'],
    summary='Get complete the look products',
    description='Get products that complete the look for a specific product',
    responses={
        200: {'description': 'Complete the look products'},
        404: {'description': 'Product not found'}
    }
)
@api_view(['GET'])
def complete_the_look(request, product_id):
    """
    Get products that complete the look for a specific product.
    """
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get curated "Complete the Look" products
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


@extend_schema(
    operation_id='product_recommendations',
    tags=['Recommendations'],
    summary='Get product recommendations',
    description='Get all types of recommendations for a product (complete the look + you may also like)',
    responses={
        200: {'description': 'Product recommendations'},
        404: {'description': 'Product not found'}
    }
)
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


def get_smart_complete_the_look_recommendations(source_product):
    """
    Generate smart "Complete the Look" recommendations based on product type and collection.
    """
    recommendations = []
    
    collection = source_product.collection

    # Get products from same collection first (if any)
    if collection is not None:
        same_collection = Product.objects.filter(
            collection=collection,
            is_available=True
        ).exclude(id=source_product.id)
    else:
        same_collection = Product.objects.none()
    
    if source_product.type == 'shoes':
        recommendations.extend(
            same_collection.filter(
                Q(type__in=['bags', 'accessories', 'clothing']) |
                Q(material__icontains=source_product.material)
            )[:3]
        )
    elif source_product.type == 'clothing':
        recommendations.extend(
            same_collection.filter(
                Q(type__in=['shoes', 'bags', 'accessories']) |
                Q(color__icontains=source_product.color)
            )[:3]
        )
    elif source_product.type == 'bags':
        recommendations.extend(
            same_collection.filter(
                Q(type__in=['shoes', 'accessories', 'clothing']) |
                Q(color__icontains=source_product.color)
            )[:3]
        )
    else:
        recommendations.extend(same_collection[:3])
    
    # If not enough from same collection, add similar products from other collections
    if len(recommendations) < 3:
        additional_filters = Q(type__in=['shoes', 'bags', 'accessories'])
        if collection is not None:
            additional_filters |= Q(collection__is_new_arrival=collection.is_new_arrival)

        similar_products = Product.objects.filter(
            additional_filters,
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
