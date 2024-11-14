from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from .models import Cart, Order
from products.models import Product
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from common.utils import cache_query
from django.db.models import BaseManager


@cache_query(60*15)
def add_to_cart(request: HttpRequest, slug: str) -> HttpResponseRedirect:
    item = get_object_or_404(Product, slug=slug)
    order_item, created = Cart.objects.get_or_create(
        item=item,
        user=request.user,
        purchased=False
    )
    order = _get_or_create_order(request.user)
    _add_item_to_order(request, order, order_item, item)
    return redirect("mainapp:cart-home")

def _get_or_create_order(user:str) -> BaseManager[Order]:
    order_qs = Order.objects.filter(user=user, ordered=False)
    return order_qs[0] if order_qs.exists() else Order.objects.create(user=user)

def _add_item_to_order(request:HttpRequest, order:Order, order_item:Order, item:Product) -> None:
    if order.orderitems.filter(item__slug=item.slug).exists():
        order_item.quantity += 1
        order_item.save()
        messages.info(request, f"{item.name} quantity has updated.")
    else:
        order.orderitems.add(order_item)
        messages.info(request, f"{item.name} has added to your cart.")


@cache_query(60*15)
def remove_from_cart(request:HttpRequest, slug:str) -> HttpResponseRedirect:
    item = get_object_or_404(Product, slug=slug)
    if cart := _get_cart_item(request.user, item):
        _update_cart_quantity(cart)
    if order := _get_active_order(request.user):
        _remove_item_from_order(order, item)
    else:
        messages.warning(request, "You do not have an active order")
    return redirect("mainapp:home")

def _get_cart_item(user:str, item:Product) -> Cart|None:
    return Cart.objects.filter(user=user, item=item).first()

def _update_cart_quantity(cart:Cart) -> None:
    if cart.quantity > 1:
        cart.quantity -= 1
        cart.save()
    else:
        cart.delete()

def _get_active_order(user:str) -> Order|None:
    return Order.objects.filter(user=user, ordered=False).first()

def _remove_item_from_order(order:Order, item:Product) -> None:
    if order.orderitems.filter(item__slug=item.slug).exists():
        order_item = Cart.objects.filter(item=item, user=order.user).first()
        order.orderitems.remove(order_item)
        messages.warning(order.user, "This item was removed from your cart.")
    else:
        messages.warning(order.user, "This item was not in your cart")


@cache_query(60*15)
def cart_view(request: HttpRequest) -> HttpResponse|HttpResponseRedirect:
    user = request.user
    carts = Cart.objects.filter(user=user, purchased=False)
    if not carts.exists():
        return handle_empty_cart(request)
    orders = Order.objects.filter(user=user, ordered=False)
    if orders.exists():
        order = orders.first()
        return render(request, 'cart/home.html', {"carts": carts, 'order': order})
    else:
        return handle_empty_cart(request)

def handle_empty_cart(request:HttpRequest) -> HttpResponseRedirect:
    messages.warning(request, "You do not have any item in your Cart")
    return redirect("mainapp:home")


@cache_query(60*15)
def decrease_cart(request:HttpRequest, slug:str) -> HttpResponseRedirect:
    item = get_object_or_404(Product, slug=slug)
    if order := _get_active_order(request.user):
        if order_item := _get_cart_item(item, request.user):
            _update_order_item_quantity(order, order_item, item)
        else:
            messages.info(request, f"{item.name} is not in your cart.")
    else:
        messages.info(request, "You do not have an active order")
    return redirect("mainapp:cart-home")


def _update_order_item_quantity(order:Order, order_item:Order, item:Product) -> None:
    if order_item.quantity > 1:
        order_item.quantity -= 1
        order_item.save()
        messages.info(order_item.user, f"{item.name} quantity has updated.")
    else:
        order.orderitems.remove(order_item)
        order_item.delete()
        messages.warning(order_item.user, f"{item.name} has been removed from your cart.")