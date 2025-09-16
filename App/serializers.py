# serializers.py
from rest_framework import serializers
from .models import ProgramaProduccion, ExcelExtra, Producto

class ProgramaProduccionSerializer(serializers.ModelSerializer):
    paila_id = serializers.CharField(source="paila.paila", default=None)
    paila_nombre = serializers.CharField(source="paila.paila", default=None)
    fert = serializers.CharField(source="fert.codigo")  # fuerza que fert sea string
    
    class Meta:
        model = ProgramaProduccion
        fields = "__all__"
class ExcelExtraSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExcelExtra
        fields = "__all__"
