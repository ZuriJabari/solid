from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Product

class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="price", lookup_expr='lte')
    min_rating = filters.NumberFilter(method='filter_min_rating')
    max_rating = filters.NumberFilter(method='filter_max_rating')
    in_stock = filters.BooleanFilter(method='filter_in_stock')
    category = filters.CharFilter(method='filter_category')
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Product
        fields = ['potency', 'is_featured', 'category']

    def filter_min_rating(self, queryset, name, value):
        return queryset.filter(average_rating__gte=value)

    def filter_max_rating(self, queryset, name, value):
        return queryset.filter(average_rating__lte=value)

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)

    def filter_category(self, queryset, name, value):
        try:
            from .models import Category
            category = Category.objects.get(slug=value)
            descendant_categories = category.get_descendants(include_self=True)
            return queryset.filter(category__in=descendant_categories)
        except Category.DoesNotExist:
            return queryset

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(short_description__icontains=value) |
            Q(category__name__icontains=value)
        ) 