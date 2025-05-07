from django.db import models
from ..models import YieldTurno, MQS, MES

def get_yield_stats(date_from, date_to, family=None, line=None):
    """
    Obtiene estadísticas de Yield para un rango de fechas con filtros opcionales
    """
    # Query base para YieldTurno
    query = YieldTurno.objects.filter(date__range=[date_from, date_to])
    
    # Filtros opcionales
    if family:
        query = query.filter(Family=family)
    if line:
        query = query.filter(Line=line)
    
    return query

def get_yield_complete_stats(date_from, date_to, family=None, line=None):
    """
    Obtiene estadísticas completas de Yield incluyendo reparaciones MES
    """
    # Obtener datos básicos
    yields = get_yield_stats(date_from, date_to, family, line)
    results = []
    
    for yield_data in yields:
        # Datos básicos del yield
        yield_stats = {
            'date': yield_data.date,
            'line': yield_data.Line,
            'family': yield_data.Family,
            'turno': yield_data.Turno,
            'jornada': yield_data.Jornada,
            'equipos_procesados': yield_data.Prime_Handle,
            'equipos_ok': yield_data.Prime_Pass,
            'equipos_fail': yield_data.Prime_Fail,
            'ntf_count': yield_data.Prime_NTF_Count,
            'defect_count': yield_data.Prime_Defect_Count,
            'fty': yield_data.FTY,
            'dphu': yield_data.DPHU,
            'ntf_rate': yield_data.NTF
        }
        
        # Obtener TrackIds relacionados con este yield
        mqs_records = yield_data.mqs_records
        track_ids = mqs_records.values_list('TrackId', flat=True).distinct()
        
        # Contar reparaciones en MES para estos TrackIds
        mes_repairs_count = MES.objects.filter(
            NS__in=track_ids
        ).count()
        
        yield_stats['mes_repairs_count'] = mes_repairs_count
        
        # Añadir al resultado
        results.append(yield_stats)
    
    return results