import django_filters
from .models import Transaction
from .models import Category
from django import forms
from django.utils import timezone

class TransactionFilter(django_filters.FilterSet):
    date_range = django_filters.DateRangeFilter(field_name='date')
    start_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='gte',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='lte',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    category = django_filters.ModelChoiceFilter(
        queryset=None,
        field_name='category',
        label='Category'
    )
    
    class Meta:
        model = Transaction
        fields = ['category']
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.filters['category'].queryset = Category.objects.filter(user=user)