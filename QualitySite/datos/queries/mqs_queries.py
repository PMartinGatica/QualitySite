from django.db import models
from ..models import MQS, MES

def get_top_failures_by_family(family=None, limit=10, date_from=None, date_to=None):
    """
    Obtiene los testcodes con más fallas por familia
    """
    query = MQS.objects.filter(Prime=True)  # Solo equipos en Prime
    
    if family:
        query = query.filter(Family=family)
        
    if date_from and date_to:
        query = query.filter(date__range=[date_from, date_to])
    
    # Agrupar por Testcode y contar
    top_failures = query.values('Family', 'Testcode', 'Testcode_Desc') \
                       .annotate(failure_count=models.Count('id')) \
                       .order_by('Family', '-failure_count')[:limit]
                       
    return top_failures

def get_station_performance(date_from, date_to, line=None, family=None):
    """
    Analiza el rendimiento de cada estación
    """
    query = MQS.objects.filter(date__range=[date_from, date_to])
    
    if line:
        query = query.filter(Line=line)
    if family:
        query = query.filter(Family=family)
        
    # Agrupar por estación
    stations = query.values('Station', 'Line', 'Family') \
                .annotate(
                    total_tests=models.Count('id'),
                    failures=models.Count('id', filter=models.Q(Prime=True)),
                    ntf_count=models.Count('id', filter=models.Q(NTF=True)),
                )
                
    # Calcular porcentajes
    for station in stations:
        if station['total_tests'] > 0:
            station['failure_rate'] = (station['failures'] / station['total_tests']) * 100
            station['ntf_rate'] = (station['ntf_count'] / station['total_tests']) * 100 if station['failures'] > 0 else 0
            
    return stations