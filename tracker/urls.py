from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from .views import reports, chart_data, bill_list, add_bill, mark_bill_paid, notifications, mark_notification_read, clear_notifications, notification_settings

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('transactions/', views.transaction_list, name='transactions'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/edit/<int:pk>/', views.edit_transaction, name='edit_transaction'),
    path('transactions/delete/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    
    path('incomes/', views.income_list, name='incomes'),
    path('expenses/', views.expense_list, name='expenses'),

    path('categories/', views.category_list, name='categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:pk>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),

    path('budgets/', views.budget_list, name='budgets'),
    path('budgets/add/', views.add_budget, name='add_budget'),
    path('budgets/edit/<int:pk>/', views.edit_budget, name='edit_budget'),
    path('budgets/delete/<int:pk>/', views.delete_budget, name='delete_budget'),

    path('goals/', views.goal_list, name='goals'),
    path('goals/add/', views.add_goal, name='add_goal'),
    path('goals/edit/<int:pk>/', views.edit_goal, name='edit_goal'),
    path('goals/delete/<int:pk>/', views.delete_goal, name='delete_goal'),

    path('reports/', views.reports, name='reports'),
    path('api/chart-data/', chart_data, name='chart_data'),

    path('bills/', bill_list, name='bill_list'),
    path('bills/add/', add_bill, name='add_bill'),
    path('bills/<int:bill_id>/paid/', mark_bill_paid, name='mark_bill_paid'),
    path('notifications/', notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('notifications/clear/', clear_notifications, name='clear_notifications'),
    path('notifications/settings/', notification_settings, name='notification_settings')
]