from django.db import models
from django.db.models import Count, Avg, Sum, F, Q
from django.utils import timezone
from datetime import timedelta
from ..models import MQS, MES, YieldTurno, QualityAnalytics

def get_dashboard_summary(date=None, days_back=7):
    """
    Obtiene un resumen para el dashboard principal
    """
    if not date:
        date = timezone.now().date()
        
    start_date = date - timedelta(days=days_back)
    
    # Resumen de Yield
    yield_summary = YieldTurno.objects.filter(
        date__range=[start_date, date]
    ).aggregate(
        avg_fty=Avg('FTY'),
        avg_dphu=Avg('DPHU'),
        avg_ntf=Avg('NTF'),
        total_units=Sum('Prime_Handle'),
        pass_units=Sum('Prime_Pass'),
        fail_units=Sum('Prime_Fail')
    )
    
    # Top fallas MQS
    top_failures = MQS.objects.filter(
        date__range=[start_date, date],
        Prime=True
    ).values('Testcode', 'Testcode_Desc').annotate(
        failure_count=Count('id')
    ).order_by('-failure_count')[:5]
    
    # Conteo de reparaciones MES
    mes_repairs = MES.objects.filter(
        FECHA_REPARACION__range=[start_date, date]
    ).count()
    
    # Datos por familia
    family_data = YieldTurno.objects.filter(
        date__range=[start_date, date]
    ).values('Family').annotate(
        avg_fty=Avg('FTY'),
        total_units=Sum('Prime_Handle')
    ).order_by('-total_units')
    
    return {
        'period': {
            'start': start_date,
            'end': date,
            'days': days_back
        },
        'yield': yield_summary,
        'top_failures': list(top_failures),
        'mes_repairs': mes_repairs,
        'families': list(family_data)
    }