# serializers.py
from rest_framework import serializers
from .models import ProgramaProduccion, ExcelExtra, Producto

class ProgramaProduccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramaProduccion
        fields = "__all__"

class ExcelExtraSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExcelExtra
        fields = "__all__"
