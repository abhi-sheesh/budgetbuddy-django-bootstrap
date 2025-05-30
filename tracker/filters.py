import django_filters
from .models import Transaction, Bill
from .models import Category
from django import forms
from django.utils import timezone

class TransactionFilter(django_filters.FilterSet):
    date_range = django_filters.DateRangeFilter(field_name='date')
    start_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='gte',
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='From ',
    )
    end_date = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='lte',
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='To ',
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

class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['name', 'amount', 'due_date', 'recurring', 'recurring_frequency']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }