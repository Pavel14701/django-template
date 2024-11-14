from rest_framework import serializers
from products.models import Product
from cart.models import Cart, Order


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = "__all__"
        read_only = ['created']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"
        read_only = ['created']
