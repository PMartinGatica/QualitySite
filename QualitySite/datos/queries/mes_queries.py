from django.db import models
from ..models import MES, MQS

def get_repair_history_by_trackid(track_id):
    """
    Obtiene el historial completo de un equipo por su TrackId
    """
    # Obtener todas las fallas MQS
    mqs_records = MQS.objects.filter(TrackId=track_id).order_by('date', 'Time')
    
    # Obtener todas las reparaciones MES
    mes_records = MES.objects.filter(NS=track_id).order_by('FECHA_REPARACION', 'HORA_REPARACION')
    
    # Crear historial combinado
    full_history = []
    
    for mqs in mqs_records:
        event = {
            'fecha': mqs.date,
            'hora': mqs.Time,
            'tipo': 'Falla MQS',
            'testcode': mqs.Testcode,
            'descripcion': mqs.Testcode_Desc,
            'station': mqs.Station,
            'line': mqs.Line
        }
        full_history.append(event)
    
    for mes in mes_records:
        event = {
            'fecha': mes.FECHA_REPARACION,
            'hora': mes.HORA_REPARACION,
            'tipo': 'Reparación MES',
            'codigo': mes.CODIGO_FALLA,
            'accion': mes.ACCION,
            'causa': mes.CAUSA,
            'reparador': mes.REPARADOR
        }
        full_history.append(event)
    
    # Ordenar por fecha y hora
    full_history.sort(key=lambda x: (x['fecha'], x['hora']))
    
    return {
        'track_id': track_id,
        'total_fallas': mqs_records.count(),
        'total_reparaciones': mes_records.count(),
        'historial': full_history
    }

def get_top_repairs_by_model(date_from, date_to, limit=10):
    """
    Obtiene los modelos con más reparaciones
    """
    return MES.objects.filter(
        FECHA_REPARACION__range=[date_from, date_to]
    ).values('MODELO').annotate(
        repairs_count=models.Count('id')
    ).order_by('-repairs_count')[:limit]