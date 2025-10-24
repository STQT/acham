from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from ...models import Product, Cart, CartItem
from ..serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemCreateUpdateSerializer,
    CartSummarySerializer
)


@extend_schema(
    tags=["Cart"],
    summary="Get user cart",
    description="Retrieve user's cart with all items and details"
)
class CartDetailView(generics.RetrieveAPIView):
    """
    Get user's cart with all items.
    """
    serializer_class = CartSerializer
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


@extend_schema(
    tags=["Cart"],
    summary="Get cart summary",
    description="Get cart summary with total items, price, and item count"
)
class CartSummaryView(generics.RetrieveAPIView):
    """
    Get cart summary (total items, price, etc.).
    """
    serializer_class = CartSummarySerializer
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


@extend_schema(
    tags=["Cart"],
    summary="Manage cart items",
    description="List cart items or add item to cart"
)
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


@extend_schema(
    tags=["Cart"],
    summary="Manage cart item",
    description="Retrieve, update, or remove cart item"
)
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
    tags=['Cart'],
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
    tags=['Cart'],
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
    tags=['Cart'],
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
    tags=['Cart'],
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
