from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transactions/', views.transaction_list, name='transactions'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('incomes/', views.income_list, name='incomes'),
    path('expenses/', views.expense_list, name='expenses'),
    path('categories/', views.category_list, name='categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('budgets/', views.budget_list, name='budgets'),
    path('budgets/add/', views.add_budget, name='add_budget'),
    path('goals/', views.goal_list, name='goals'),
    path('goals/add/', views.add_goal, name='add_goal'),
    path('reports/', views.reports, name='reports'),
    path('transactions/edit/<int:pk>/', views.edit_transaction, name='edit_transaction'),
    path('transactions/delete/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    
    # Category URLs
    path('categories/edit/<int:pk>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
    
    # Budget URLs
    path('budgets/edit/<int:pk>/', views.edit_budget, name='edit_budget'),
    path('budgets/delete/<int:pk>/', views.delete_budget, name='delete_budget'),
    
    # Goal URLs
    path('goals/edit/<int:pk>/', views.edit_goal, name='edit_goal'),
    path('goals/delete/<int:pk>/', views.delete_goal, name='delete_goal'),
]