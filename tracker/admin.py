from django.contrib import admin
from .models import Transaction, Category, Budget, Goal

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'category', 'date')
    list_filter = ('user', 'category', 'date')
    search_fields = ('description',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'category_type')
    list_filter = ('user', 'category_type')
    search_fields = ('name',)

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'start_date', 'end_date')
    list_filter = ('user', 'category')
    search_fields = ('category__name',)

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'current_amount', 'target_amount', 'target_date', 'completed')
    list_filter = ('user', 'completed')
    search_fields = ('name',)
