import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from django.db.models import Sum
from .models import Transaction

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