# views.py
import pandas as pd
import numpy as np
import json
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProgramaProduccionSerializer
import io
from django.http import HttpResponse
from django.db import transaction
from django.utils.dateparse import parse_datetime

from .models import ProgramaProduccion, ExcelExtra, Producto, DetalleProducto, Matrix, InventarioPaila, PailaAsignacion


def clean_value(val):
    """Convierte valores de pandas/numpy a tipos JSON-compatibles."""
    if pd.isna(val):
        return None
    if isinstance(val, pd.Timestamp):
        return val.strftime("%Y-%m-%d")  # o .isoformat() si quieres fecha+hora
    if isinstance(val, (np.generic,)):  # numpy int64, float64, etc.
        return val.item()
    return val


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def importar_excel(request):
    file = request.FILES.get("file")
    if not file:
        return Response({"error": "No file uploaded"}, status=400)

    try:
        df = pd.read_excel(file)
        mapping = request.data.get("mapping")
        if not mapping:
            return Response({"error": "Mapping not provided"}, status=400)
        mapping = json.loads(mapping) if isinstance(mapping, str) else mapping

        fert_cache = {}  # cache de productos

        for _, row in df.iterrows():
            orden = row.get(mapping["orden"])
            codigo_fert = row.get(mapping["fert"])
            lote = row.get(mapping["lote"])

            if pd.isna(orden) or pd.isna(codigo_fert):
                continue

            codigo_fert = str(int(codigo_fert)) if isinstance(codigo_fert, float) else str(codigo_fert).strip()

            # obtener o crear Producto
            if codigo_fert in fert_cache:
                fert = fert_cache[codigo_fert]
            else:
                fert, _ = Producto.objects.get_or_create(codigo=codigo_fert, defaults={"descripcion": codigo_fert})
                fert_cache[codigo_fert] = fert

            # guardar ProgramaProduccion fila por fila
            programa = ProgramaProduccion.objects.create(
                orden=str(orden).strip(),
                fert=fert,
                lote_f=float(lote) if pd.notna(lote) else None
            )

            # guardar ExcelExtra asociado
            extras = {
                str(col): clean_value(row[col])
                for col in df.columns
                if col not in mapping.values()
            }
            if extras:
                ExcelExtra.objects.create(programa=programa, data=extras)

        return Response({"message": "Excel importado correctamente"}, status=201)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
def listar_programa(request):
    # 🔹 traer todos
    programas = ProgramaProduccion.objects.all().order_by("id")  # mantiene el orden de inserción

    # 🔹 separar padres de hijos
    padres = programas.filter(parent__isnull=True)

    # serializar solo padres (los hijos se anidan en el serializer)
    serializer = ProgramaProduccionSerializer(padres, many=True)
    return Response(serializer.data)

@api_view(["DELETE"])
def borrar_programa_y_extras(request):
    try:
        ExcelExtra.objects.all().delete()
        ProgramaProduccion.objects.all().delete()
        return Response({"message": "Datos borrados correctamente"}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(["GET"])
def hay_datos(request):
    return Response({
        "programa": ProgramaProduccion.objects.exists(),
        "extras": ExcelExtra.objects.exists()
    })

@api_view(["GET"])
def exportar_excel(request):
    try:
        programas = ProgramaProduccion.objects.all().prefetch_related("extras")
        if not programas.exists():
            return Response({"error": "No hay datos para exportar"}, status=400)

        # Serializar a DataFrame
        base_data = []
        extras_data = []

        for programa in programas:
            base_row = {
                "orden": programa.orden,
                "fert": programa.fert.codigo if programa.fert else None,
                "lote_f": programa.lote_f,
                "paila": programa.paila.paila if programa.paila else None,
                "estacion": programa.estacion,
                "hora_inicial": programa.hora_inicial,
                "hora_final": programa.hora_final,
                "duracion_total": programa.duracion_total,
                "empastado": programa.empastado,
                "molino": programa.molino,
                "matizado": programa.matizado,
                "emulsion": programa.emulsion,
                "completado": programa.completado,
                "envasado": programa.envasado,
            }
            base_data.append(base_row)

            # Combinar extras
            extra = programa.extras.first()
            extras_data.append(extra.data if extra else {})

        df_base = pd.DataFrame(base_data)
        df_extras = pd.DataFrame(extras_data)

        # Concatenar lado a lado
        df_final = pd.concat([df_base, df_extras], axis=1)

        # Guardar en memoria como Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_final.to_excel(writer, index=False, sheet_name="Produccion+Extras")

        output.seek(0)

        response = HttpResponse(
            output,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="produccion_extras.xlsx"'
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)
    
@api_view(["GET"])
def get_pailas_validas(request, programa_id):
    try:
        programa = ProgramaProduccion.objects.get(pk=programa_id)
        print(f"🔹 Programa ID: {programa.id}, lote_f: {programa.lote_f}")
        print(f"🔹 Fert desde TanStack: {programa.fert.codigo}")

        # Obtener el detalle del producto y su color
        detalle = DetalleProducto.objects.filter(fert=programa.fert).first()
        if not detalle:
            print("❌ No se encontró DetalleProducto para este fert")
            return Response([], status=200)

        color = detalle.color
        if not color:
            print("❌ DetalleProducto no tiene color asignado")
            return Response([], status=200)

        print(f"🔹 Color obtenido: {color.codigo} - {color.descripcion}")

        # Filtrar matrices según color, diamsi='SI' y base_dispersion_minimo < lote_f
        matrices = Matrix.objects.filter(
            color=color,
            diamsi__iexact="SI",
            base_dispersion_minimo__lt=programa.lote_f
        ).select_related("paila")

        print(f"🔹 Matrices encontradas: {matrices.count()}")

        # Tomar pailas únicas y quedarnos con la mayor capacidad_planificable
        paila_dict = {}
        for m in matrices:
            if not m.paila or not m.capacidad_planificable:
                continue
            if m.paila.paila not in paila_dict:
                paila_dict[m.paila.paila] = {
                    "paila": m.paila.paila,
                    "numero": m.paila.numero,
                    "capacidad_planificable": m.capacidad_planificable,
                }
            else:
                # Si ya existe, me quedo con el máximo capacidad_planificable
                if m.capacidad_planificable > paila_dict[m.paila.paila]["capacidad_planificable"]:
                    paila_dict[m.paila.paila]["capacidad_planificable"] = m.capacidad_planificable

        # Ordenar por capacidad_planificable descendente
        pailas_ordenadas = sorted(
            paila_dict.values(),
            key=lambda x: x["capacidad_planificable"],
            reverse=True
        )

        print(f"🔹 Pailas válidas ordenadas: {[p['paila'] for p in pailas_ordenadas]}")

        return Response(pailas_ordenadas, status=200)

    except ProgramaProduccion.DoesNotExist:
        return Response({"error": "Programa no encontrado"}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)


    
@api_view(["PATCH"])
def asignar_paila(request, programa_id):
    try:
        programa = ProgramaProduccion.objects.get(pk=programa_id)
        paila_id = request.data.get("paila")

        if not paila_id:
            return Response({"error": "No se proporcionó paila"}, status=400)

        try:
            paila = InventarioPaila.objects.get(pk=paila_id)
        except InventarioPaila.DoesNotExist:
            return Response({"error": "Paila no encontrada"}, status=404)

        # 🔹 1. Eliminar hijos previos
        programa.children.all().delete()

        # 🔹 2. Asignar paila al padre
        programa.paila = paila

        # 🔹 3. Obtener color del producto
        detalle = DetalleProducto.objects.filter(fert=programa.fert).first()
        color = detalle.color if detalle else None

        # 🔹 4. Buscar estación válida para la paila seleccionada
        matrix = Matrix.objects.filter(paila=paila, color=color, diamsi="SI").first()
        programa.estacion = matrix.estacion if matrix else None

        # 🔹 5. Fragmentación
        if matrix and programa.lote_f and matrix.capacidad_planificable:
            cap = matrix.capacidad_planificable

            if programa.lote_f <= cap:
                programa.produccion = programa.lote_f
                programa.save()

            else:
                original_lote = programa.lote_f
                programa.produccion = cap
                programa.save()

                sobrante = original_lote - cap

                # Hijo → sin paila y sin estación
                ProgramaProduccion.objects.create(
                    orden=programa.orden,
                    fert=programa.fert,
                    lote_f=sobrante,
                    produccion=min(sobrante, cap),
                    estacion=None,   # 👈 vacío
                    paila=None,      # 👈 vacío
                    parent=programa,
                )
        else:
            programa.produccion = programa.lote_f
            programa.save()

        return Response({
            "message": "Paila asignada y fragmentación actualizada",
            "paila": programa.paila.paila if programa.paila else None,
            "estacion": programa.estacion,
        })

    except ProgramaProduccion.DoesNotExist:
        return Response({"error": "Programa no encontrado"}, status=404)
    except Exception as e:
        import traceback; traceback.print_exc()
        return Response({"error": str(e)}, status=500)
    
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def importar_excel_paila_asignacion(request):
    file = request.FILES.get("file")
    if not file:
        return Response({"error": "No file uploaded"}, status=400)

    try:
        df = pd.read_excel(file)
        mapping = request.data.get("mapping")
        inicio = request.data.get("inicio")  # 👈 fecha/hora inicial común
        if not mapping or not inicio:
            return Response({"error": "Mapping or inicio not provided"}, status=400)

        mapping = json.loads(mapping) if isinstance(mapping, str) else mapping
        inicio_dt = parse_datetime(inicio)
        if not inicio_dt:
            return Response({"error": "Inicio inválido, debe ser formato ISO (YYYY-MM-DD HH:MM:SS)"}, status=400)

        # 👇 BORRAR asignaciones sin programa antes de importar nuevas
        PailaAsignacion.objects.filter(programa__isnull=True).delete()

        for _, row in df.iterrows():
            paila_id = row.get(mapping["paila"])
            fin_val = row.get(mapping["fin"])
            estado_val = row.get(mapping["estado"])

            if pd.isna(paila_id):
                continue

            try:
                paila = InventarioPaila.objects.get(pk=str(paila_id).strip())
            except InventarioPaila.DoesNotExist:
                continue

            fin_dt = None
            if pd.notna(fin_val):
                # soporta string de fecha o datetime
                if isinstance(fin_val, pd.Timestamp):
                    fin_dt = fin_val.to_pydatetime()
                else:
                    fin_dt = parse_datetime(str(fin_val))

            PailaAsignacion.objects.create(
                paila=paila,
                inicio=inicio_dt,   # 👈 mismo valor para todas
                fin=fin_dt,
                estado=str(estado_val).strip().lower() if pd.notna(estado_val) else "disponible",
            )

        return Response({"message": "Excel de PailaAsignacion importado correctamente"}, status=201)

    except Exception as e:
        import traceback; traceback.print_exc()
        return Response({"error": str(e)}, status=500)