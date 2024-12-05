import django_filters as filters
from django.db.models import Q
from .models import Product

class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = filters.CharFilter(method='filter_category')
    search = filters.CharFilter(method='filter_search')
    in_stock = filters.BooleanFilter(method='filter_stock')

    class Meta:
        model = Product
        fields = ['category', 'is_active', 'min_price', 'max_price', 'in_stock']

    def filter_category(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(category__slug=value) |
                Q(category__parent__slug=value)
            )
        return queryset

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(description__icontains=value) |
                Q(category__name__icontains=value)
            )
        return queryset

    def filter_stock(self, queryset, name, value):
        if value is True:
            return queryset.filter(inventory__quantity__gt=0)
        elif value is False:
            return queryset.filter(inventory__quantity=0)
        return queryset 