import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from django.db.models import Sum, FloatField
from .models import Transaction
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from datetime import timedelta
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db.models.functions import TruncDay, Cast
from django.db import models

def detect_spending_patterns(user):
    transactions = Transaction.objects.filter(
        user=user,
        category__category_type='EX'
    ).values('category__name', 'amount', 'date')
    
    if len(transactions) < 5:  
        return None
    
    df = pd.DataFrame(list(transactions))
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.dayofweek
    df['day_of_month'] = df['date'].dt.day
    df['month'] = df['date'].dt.month
    
    features = df.groupby('category__name').agg({
        'amount': ['mean', 'count'],
        'day_of_week': 'mean',
        'day_of_month': 'mean'
    }).fillna(0)
    features.columns = ['amount_mean', 'transaction_count', 'day_of_week_mean', 'day_of_month_mean']
    
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    kmeans = KMeans(n_clusters=3, random_state=42)
    clusters = kmeans.fit_predict(scaled_features)
    
    features['cluster'] = clusters
    features['category'] = features.index
    
    results = []
    for cluster in sorted(features['cluster'].unique()):
        cluster_data = features[features['cluster'] == cluster]
        avg_amount = cluster_data['amount_mean'].mean()
        avg_day = cluster_data['day_of_month_mean'].mean()
        
        results.append({
            'cluster': cluster,
            'categories': list(cluster_data['category']),
            'average_amount': avg_amount,
            'average_day': round(avg_day),
            'size': len(cluster_data)
        })
    
    return sorted(results, key=lambda x: x['average_amount'], reverse=True)

def predict_future_expenses(user, months=3):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=365)
    
    daily_expenses = Transaction.objects.filter(
        user=user,
        category__category_type='EX',
        date__range=[start_date, end_date]
    ).annotate(
        day=models.functions.TruncDay('date')).annotate(
        amount_float=Cast(models.F('amount'), FloatField())
    ).values('day').annotate(
        total=Sum('amount_float')
    ).order_by('day')
    
    if len(daily_expenses) < 60:
        return None
    
    df = pd.DataFrame(list(daily_expenses))
    df['day'] = pd.to_datetime(df['day'])
    df['total'] = pd.to_numeric(df['total'], errors='coerce')
    df.set_index('day', inplace=True)
    
    monthly = df.resample('M').sum()
    monthly = monthly[monthly['total'] > 0] 
    
    if len(monthly) < 6:  
        return None
    
    ts_data = monthly['total'].values.astype('float64')
    
    try:
        model = ARIMA(ts_data, order=(1,1,1))
        model_fit = model.fit()
        
        forecast = model_fit.forecast(steps=months)
        forecast = np.maximum(forecast, 0) 
        
        results = []
        current_date = end_date.replace(day=1)
        
        for i, amount in enumerate(forecast, 1):
            month_date = current_date + pd.DateOffset(months=i)
            results.append({
                'month': month_date.strftime('%B %Y'),
                'predicted_amount': float(amount)
            })
        
        return results
    
    except Exception as e:
        print(f"ARIMA modeling failed: {str(e)}")
        return None