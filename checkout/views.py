import stripe
from stripe import Charge
from django.utils.crypto import get_random_string
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from cart.models import Order, Cart
from . models import BillingForm, BillingAddress
from django.views.generic.base import TemplateView
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect


stripe.api_key = settings.STRIPE_SECRET_KEY 


def checkout(request:HttpRequest) -> HttpResponse:
    form = BillingForm()
    order = _get_user_order(request.user)
    context = _get_context_data(form, order)
    saved_address = _get_saved_address(request.user)
    if saved_address:
        context["savedAddress"] = saved_address
    if request.method == "POST":
        form = BillingForm(request.POST, instance=saved_address)
        if form.is_valid():
            _save_billing_address(form, request.user)
            context["form"] = form
    return render(request, 'checkout/index.html', context)

def _get_user_order(user:str) -> Order|None:
    return Order.objects.filter(user=user, ordered=False).first()

def _get_context_data(form:BillingForm, order:Order) -> dict:
    return {
        "form": form,
        "order_items": order.orderitems.all(),
        "order_total": order.get_totals()
    }

def _get_saved_address(user:str) -> BillingAddress|None:
    return BillingAddress.objects.filter(user=user).first()

def _save_billing_address(form:BillingForm, user:str) -> None:
    billingaddress = form.save(commit=False)
    billingaddress.user = user
    billingaddress.save()


def payment(request: HttpRequest) -> HttpResponse:
    key = settings.STRIPE_PUBLISHABLE_KEY
    order = _get_user_order(request.user)
    total = _calculate_total(order)
    if request.method == 'POST':
        process_payment(request.POST['stripeToken'], total, order)
    return render(request, 'checkout/payment.html', {"key": key, "total": total})

def _calculate_total(order:Order) -> float:
    order_total = order.get_totals()
    total_cents = float(order_total * 100)
    return round(total_cents, 2)

def process_payment(token:str, total:float, order:Order) -> None:
    charge = stripe.Charge.create(
        amount=total,
        currency='usd',
        description=str(order),
        source=token
    )
    print(charge)


def charge(request: HttpRequest) -> HttpResponse:
    order = _get_unordered_user_order(request.user)
    order_items = order.orderitems.all()
    order_total = order.get_totals()
    if request.method == 'POST':
        total_cents = int(float(order_total * 100))
        charge = _process_charge(total_cents, order, request.POST['stripeToken'])
        if charge.status == "succeeded":
            _handle_successful_charge(charge, order, request.user)
        return render(request, 'checkout/charge.html', {"items": order_items, "order": order})
    return render(request, 'checkout/charge.html', {"items": order_items, "order": order})

def _get_unordered_user_order(user:str) -> Order|None:
    return Order.objects.get(user=user, ordered=False)

def _process_charge(amount:int, order:Order, token:str) -> Charge:
    return stripe.Charge.create(
        amount=amount,
        currency='inr',
        description=str(order),
        source=token
    )

def _handle_successful_charge(charge: Charge, order:Order, user:str) -> None:
    order_id = _generate_order_id(user)
    print(charge.id)
    order.ordered = True
    order.paymentId = charge.id
    order.orderId = order_id
    order.save()
    _mark_items_as_purchased(user)

def _generate_order_id(user:str) -> str:
    return f'#{user}{
        get_random_string(
            length=16, allowed_chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )
    }'

def _mark_items_as_purchased(user:str) -> None:
    cart_items = Cart.objects.filter(user=user)
    for item in cart_items:
        item.purchased = True
        item.save()


def order_view(request:HttpRequest) -> HttpResponseRedirect|HttpResponse:
	try:
		orders = Order.objects.filter(user=request.user, ordered=True)
		context = {"orders": orders}
	except Exception:
		messages.warning(request, "You do not have an active order")
		return redirect('/')
	return render(request, 'checkout/order.html', context)