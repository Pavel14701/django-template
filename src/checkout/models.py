from django.db.models import Model, ForeignKey, CharField, CASCADE
from django.forms import ModelForm
from django.contrib.auth import get_user_model

User = get_user_model()

class BillingAddress(Model):
	user = ForeignKey(User, on_delete=CASCADE)
	address = CharField(max_length=100)
	zipcode = CharField(max_length=50)
	city = CharField(max_length=30)
	landmark = CharField(max_length=20)

	def __str__(self):
		return f'{self.user.username} billing address'

	class Meta:
		verbose_name_plural = "Billing Addresses"


class BillingForm(ModelForm):
	class Meta:
		model = BillingAddress
		fields = ['address', 'zipcode', 'city', 'landmark']