from rest_framework import serializers
from .models import MQS, MES, YieldTurno  # Mantener solo esta importación

class MQSSerializer(serializers.ModelSerializer):
    class Meta:
        model = MQS
        fields = '__all__'

class MESSerializer(serializers.ModelSerializer):
    class Meta:
        model = MES
        fields = '__all__'

class YieldTurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = YieldTurno
        fields = '__all__'
