import csv
from datetime import datetime
from django.db import models

class MQS(models.Model):
    TrackId = models.CharField(max_length=100)  # Remove unique=True if it exists
    date = models.DateField()  # Nota: "date" con "d" minúscula
    Time = models.TimeField()
    Line = models.CharField(max_length=255)
    Family = models.CharField(max_length=255)
    Model = models.CharField(max_length=255)
    Process = models.CharField(max_length=255)
    Station = models.CharField(max_length=255)
    Fixture = models.CharField(max_length=255)
    NTF = models.BooleanField()
    Prime = models.BooleanField()
    Testcode = models.CharField(max_length=255)
    Testcode_Desc = models.TextField()
    Fail_Desc = models.TextField()
    TestTime = models.FloatField(null=True, blank=True)
    Test_Val = models.FloatField(null=True, blank=True)
    LL = models.FloatField(null=True, blank=True)
    UL = models.FloatField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['TrackId', 'date', 'Time'],
                name='unique_mqs_trackid_datetime'
            )
        ]
        indexes = [
            models.Index(fields=['date', 'Time']),
            models.Index(fields=['TrackId']),
        ]
        db_table = 'quality_mqs'

class MES(models.Model):
    MODELO = models.CharField(max_length=255)  # New field
    NS = models.CharField(max_length=100)      # New field
    FECHA_REPARACION = models.DateField()
    HORA_REPARACION = models.TimeField()
    FECHA_RECHAZO = models.DateField()
    HORA_RECHAZO = models.TimeField()
    POSICION = models.CharField(max_length=100)
    FUNCION = models.CharField(max_length=100)
    CODIGO_FALLA = models.CharField(max_length=200)
    CAUSA = models.CharField(max_length=200)
    ACCION = models.CharField(max_length=200)
    ORIGEN = models.CharField(max_length=50)
    IMAGEN = models.TextField(default='0')  # Default to '0' if empty
    REPARADOR = models.CharField(max_length=100)
    COMENTARIO = models.TextField(blank=True, default='')  # Allow empty comments

    # Relación con MQS sin especificar db_column
           # Sin db_column para evitar conflictos
    

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['NS', 'FECHA_REPARACION', 'HORA_REPARACION', 'CODIGO_FALLA'],
                name='uq_mes_reparacion_codigo'
            )
        ]

class YieldTurno(models.Model):
    JORNADA_CHOICES = [
        ('Day', 'Día'),
        ('Night', 'Noche'),
    ]
    
    TURNO_CHOICES = [
        ('1', 'Turno 1'),
        ('2', 'Turno 2'),
        ('3', 'Turno 3'),
    ]
    
    Name = models.CharField(max_length=255)
    date = models.DateField()
    Jornada = models.CharField(max_length=10, choices=JORNADA_CHOICES)
    Turno = models.CharField(max_length=10, choices=TURNO_CHOICES)  # Cambiado de max_length=1 a 10
    Line = models.CharField(max_length=50)
    Family = models.CharField(max_length=50)
    Process = models.CharField(max_length=100)
    Prime_Pass = models.IntegerField(default=0)
    Prime_Fail = models.IntegerField(default=0)
    Prime_Handle = models.IntegerField(default=0)
    Prime_NTF_Count = models.IntegerField(default=0)
    Prime_Defect_Count = models.IntegerField(default=0)
    FTY = models.FloatField(default=0.0)
    DPHU = models.FloatField(default=0.0)
    NTF = models.FloatField(default=0.0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['Name', 'date', 'Turno', 'Line'],
                name='unique_yield_turno'
            )
        ]

    # Relación inversa con MQS (opcional)
    @property
    def mqs_records(self):
        """Retorna todos los registros MQS relacionados con este turno"""
        return MQS.objects.filter(
            date=self.date,
            Line=self.Line,
            Family=self.Family,
            Process=self.Process
        )
    
    @property
    def calculate_fty(self):
        """Calcula FTY (First Time Yield) basado en datos actuales"""
        if self.Prime_Handle == 0:
            return 0
        return (self.Prime_Pass / self.Prime_Handle) * 100
    
    def save(self, *args, **kwargs):
        # Auto-calcular FTY y DPHU al guardar
        if self.Prime_Handle > 0:
            self.FTY = (self.Prime_Pass / self.Prime_Handle) * 100
            self.DPHU = (self.Prime_Defect_Count / self.Prime_Handle) * 100
        super().save(*args, **kwargs)

class QualityAnalytics(models.Model):
    """Modelo para almacenar análisis de calidad y tendencias"""
    date = models.DateField()
    line = models.CharField(max_length=255)
    family = models.CharField(max_length=255)
    top_failure = models.CharField(max_length=255)
    failure_count = models.IntegerField(default=0)
    ntf_rate = models.FloatField(default=0)
    average_fty = models.FloatField(default=0)
    
    class Meta:
        unique_together = ['date', 'line', 'family']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['line', 'family']),
        ]

