from django.urls import path
from . import views

urlpatterns = [
    # APIs básicas existentes
    path('mqs/', views.MQSListView.as_view(), name='mqs-list'),
    path('mes/', views.MESListView.as_view(), name='mes-list'),
    path('yield/', views.YieldTurnoListView.as_view(), name='yield-list'),
    
    # Dashboard y analítica
    path('dashboard/', views.DashboardView.as_view(), name='dashboard-summary'),
    
    # Queries específicas
    path('stats/yield/', views.YieldStatsView.as_view(), name='yield-stats'),
    path('stats/top-failures/', views.TopFailuresView.as_view(), name='top-failures'),
    path('stats/repair-history/<str:track_id>/', views.RepairHistoryView.as_view(), name='repair-history'),
    path('stats/station-performance/', views.StationPerformanceView.as_view(), name='station-performance'),
]