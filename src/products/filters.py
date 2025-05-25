from . models import Product
from django_filters import FilterSet
from django_filters.filters import RangeFilter, CharFilter


class ProductFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')
    price = RangeFilter()


    class Meta:
        model = Product
        fields = ['name', 'price']