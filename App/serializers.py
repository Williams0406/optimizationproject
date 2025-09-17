# serializers.py
from rest_framework import serializers
from .models import ProgramaProduccion, ExcelExtra, Producto
from datetime import timedelta

class ProgramaProduccionSerializer(serializers.ModelSerializer):
    paila_id = serializers.CharField(source="paila.paila", default=None)
    paila_nombre = serializers.CharField(source="paila.paila", default=None)
    fert = serializers.CharField(source="fert.codigo")  
    children = serializers.SerializerMethodField()
    produccion = serializers.SerializerMethodField()  # 👈 sobrescribir produccion

    class Meta:
        model = ProgramaProduccion
        fields = "__all__"

    def get_children(self, obj):
        return ProgramaProduccionSerializer(
            obj.children.all().order_by("id"), many=True
        ).data

    def get_produccion(self, obj):
        # Solo devolver producción si hay paila asignada
        if obj.paila:
            return obj.produccion
        return None
    
class ExcelExtraSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExcelExtra
        fields = "__all__"
