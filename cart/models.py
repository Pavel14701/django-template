from django.db.models import Model, ForeignKey, IntegerField, BooleanField, DateTimeField,\
    ManyToManyField, CharField, CASCADE
from django.contrib.auth import get_user_model
from products.models import Product


User = get_user_model()


class Cart(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    item = ForeignKey(Product, on_delete=CASCADE)
    quantity = IntegerField(default=1)
    purchased = BooleanField(default=False)
    created = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.quantity} of {self.item.name}'

    def get_total(self):
        return float("{0:.2f}".format(self.item.price * self.quantity))


class Order(Model):
    orderitems = ManyToManyField(Cart)
    user = ForeignKey(User, on_delete=CASCADE)
    ordered = BooleanField(default=False)
    created = DateTimeField(auto_now_add=True)
    paymentId = CharField(max_length=200, blank=True, null=True)
    orderId = CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.user.username

    def get_totals(self):
        return sum(order_item.get_total() for order_item in self.orderitems.all())
