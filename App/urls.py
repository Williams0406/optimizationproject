# urls.py
from django.urls import path
from .views import (
    importar_excel, listar_programa, borrar_programa_y_extras, hay_datos,
    exportar_excel, get_pailas_validas, asignar_paila,
    importar_excel_paila_asignacion, calcular_operaciones, set_hora_inicial,
    sincronizar_asignaciones   # 👈 importar
)

urlpatterns = [
    path("importar-excel/", importar_excel, name="importar_excel"),
    path("programa-produccion/", listar_programa, name="listar_programa"),
    path("borrar-programa-extras/", borrar_programa_y_extras, name="borrar_programa_y_extras"),
    path("hay-datos/", hay_datos, name="hay_datos"),
    path("exportar-excel/", exportar_excel, name="exportar_excel"),
    path("pailas-validas/<int:programa_id>/", get_pailas_validas, name="pailas_validas"),
    path("asignar-paila/<int:programa_id>/", asignar_paila, name="asignar_paila"),
    path("importar-excel-paila-asignacion/", importar_excel_paila_asignacion, name="importar_excel_paila_asignacion"),
    path("calcular-operaciones/", calcular_operaciones, name="calcular_operaciones"),
    path("set-hora-inicial/<int:programa_id>/", set_hora_inicial, name="set_hora_inicial"),
    path("sincronizar-asignaciones/", sincronizar_asignaciones, name="sincronizar_asignaciones"),  # 👈 nuevo
]