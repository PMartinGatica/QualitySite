from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import MQS, MES, YieldTurno
from .serializers import MQSSerializer, MESSerializer, YieldTurnoSerializer

# Importar las funciones de consulta
# Si todavía no tienes estos módulos, deberás crearlos primero
from .queries.mqs_queries import get_top_failures_by_family, get_station_performance
from .queries.mes_queries import get_repair_history_by_trackid
from .queries.yield_queries import get_yield_complete_stats
from .queries.dashboard_queries import get_dashboard_summary

# Create your views here.

class MQSListView(ListAPIView):
    queryset = MQS.objects.all()
    serializer_class = MQSSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['date', 'Family', 'Line', 'Station', 'Testcode', 'NTF', 'Prime']
    ordering_fields = ['date', 'Time', 'TrackId']
    search_fields = ['TrackId', 'Testcode', 'Testcode_Desc', 'Fail_Desc']

class MESListView(ListAPIView):
    queryset = MES.objects.all()
    serializer_class = MESSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['MODELO', 'NS', 'FECHA_REPARACION', 'POSICION', 'CODIGO_FALLA', 'CAUSA', 'ORIGEN', 'REPARADOR']
    ordering_fields = ['FECHA_REPARACION', 'HORA_REPARACION', 'NS']
    search_fields = ['NS', 'COMENTARIO', 'CODIGO_FALLA']

class YieldTurnoListView(ListAPIView):
    queryset = YieldTurno.objects.all()
    serializer_class = YieldTurnoSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date', 'Jornada', 'Turno', 'Line', 'Family', 'Process']
    ordering_fields = ['date', 'FTY', 'DPHU', 'NTF', 'Prime_Handle']

class DashboardView(APIView):
    """
    Vista para el dashboard principal con resumen de estadísticas
    """
    def get(self, request):
        try:
            days = request.query_params.get('days', 7)
            data = get_dashboard_summary(days_back=int(days))
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class YieldStatsView(APIView):
    """
    Vista para estadísticas completas de Yield
    """
    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        family = request.query_params.get('family')
        line = request.query_params.get('line')
        
        if not date_from or not date_to:
            return Response({"error": "Se requieren parámetros date_from y date_to"}, 
                          status=status.HTTP_400_BAD_REQUEST)
            
        try:
            stats = get_yield_complete_stats(date_from, date_to, family, line)
            return Response(stats)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TopFailuresView(APIView):
    """
    Vista para obtener el top de fallas por familia
    """
    def get(self, request):
        family = request.query_params.get('family')
        limit = int(request.query_params.get('limit', 10))
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        try:
            failures = get_top_failures_by_family(family, limit, date_from, date_to)
            return Response(failures)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RepairHistoryView(APIView):
    """
    Vista para obtener el historial de reparaciones de un equipo
    """
    def get(self, request, track_id):
        try:
            history = get_repair_history_by_trackid(track_id)
            return Response(history)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StationPerformanceView(APIView):
    """
    Vista para analizar el rendimiento de estaciones
    """
    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        line = request.query_params.get('line')
        family = request.query_params.get('family')
        
        if not date_from or not date_to:
            return Response({"error": "Se requieren parámetros date_from y date_to"}, 
                          status=status.HTTP_400_BAD_REQUEST)
            
        try:
            stats = get_station_performance(date_from, date_to, line, family)
            return Response(stats)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
