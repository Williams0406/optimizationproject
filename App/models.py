from django.db import models

# Create your models here.
class Producto(models.Model):
    codigo = models.CharField(max_length=50, primary_key=True)
    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"
    
# Tabla: Color
class Color(models.Model):
    codigo = models.CharField(max_length=50, primary_key=True)
    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

class DetalleProducto(models.Model):
    primario = models.IntegerField(primary_key=True)
    fert = models.ForeignKey(Producto, on_delete=models.CASCADE)
    halb = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.CharField(max_length=255)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.fert} - {self.descripcion}"
    
# Tabla: Rutas
class Ruta(models.Model):
    Tipo = models.CharField(max_length=50)
    proceso = models.CharField(max_length=50, primary_key=True)
    empastado = models.BooleanField(default=False)
    molino = models.BooleanField(default=False)
    emulsion = models.BooleanField(default=False)
    completado = models.BooleanField(default=False)
    matizado = models.BooleanField(default=False)
    calidad = models.BooleanField(default=False)
    envasado = models.BooleanField(default=False)

    def __str__(self):
        return self.proceso

# Tabla: Inventario_paila
class InventarioPaila(models.Model):
    paila = models.CharField(max_length=50, primary_key=True)   # PAILA como clave única
    numero = models.IntegerField()
    tipo = models.CharField(max_length=100, blank=True, null=True)
    altura = models.FloatField(blank=True, null=True)
    diametro = models.FloatField(blank=True, null=True)
    base = models.FloatField(blank=True, null=True)
    capacidad_planificable = models.FloatField(blank=True, null=True)
    capacidad_total = models.FloatField(blank=True, null=True)
    tara = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"Paila {self.paila}"

# Tabla: Equipo
class Equipo(models.Model):
    equipo = models.CharField(max_length=50, primary_key=True)
    estacion = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.equipo} ({self.estacion})"
    
# Tabla: Matrix
class Matrix(models.Model):
    primario = models.IntegerField(primary_key=True)
    paila = models.ForeignKey(InventarioPaila, on_delete=models.CASCADE)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    numero = models.IntegerField()
    capacidad_total = models.FloatField(blank=True, null=True)
    relacion = models.FloatField(blank=True, null=True)
    diamsi = models.CharField(max_length=10, blank=True, null=True)
    base_dispersion_minimo = models.FloatField(blank=True, null=True)
    capacidad_planificable = models.FloatField(blank=True, null=True)
    estacion = models.CharField(max_length=100, blank=True, null=True)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    validacion = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"Matrix {self.primario}"
    
# Tabla: PailaAsignacion
class PailaAsignacion(models.Model):
    paila = models.ForeignKey("InventarioPaila", on_delete=models.CASCADE)
    inicio = models.DateTimeField(null=True, blank=True)
    fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=50,
        choices=[
            ('disponible', 'Disponible'),
            ('ocupada', 'Ocupada'),
            ('lavado', 'Pendiente de lavado'),
        ]
    )
    programa = models.OneToOneField(
        "ProgramaProduccion",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="asignacion"
    )

    def __str__(self):
        return f"{self.paila} ({self.estado})"


# Tabla: ProgramaProduccion
class ProgramaProduccion(models.Model):
    orden = models.CharField(max_length=100)
    fert = models.ForeignKey(Producto, on_delete=models.CASCADE)
    lote_f = models.FloatField(blank=True, null=True)
    paila = models.ForeignKey("InventarioPaila", on_delete=models.SET_NULL, null=True, blank=True)
    estacion = models.CharField(max_length=100, blank=True, null=True)

        # Nuevos campos ⬇️
    hora_inicial = models.DateTimeField(null=True, blank=True)
    hora_final = models.DateTimeField(null=True, blank=True)
    duracion_total = models.FloatField(null=True, blank=True)  # en horas

    empastado = models.FloatField(null=True, blank=True)
    molino = models.FloatField(null=True, blank=True)
    emulsion = models.FloatField(null=True, blank=True)
    completado = models.FloatField(null=True, blank=True)
    matizado = models.FloatField(null=True, blank=True)
    envasado = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Orden {self.orden} - {self.fert_id}"


# Tabla: Throughput
class Throughput(models.Model):
    primario = models.IntegerField(primary_key=True)
    linea = models.CharField(max_length=50)
    fert = models.ForeignKey(Producto, on_delete=models.CASCADE)
    halb = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.CharField(max_length=255)
    ruta = models.ForeignKey(Ruta, on_delete=models.SET_NULL, null=True, blank=True)
    pdp = models.FloatField(blank=True, null=True)

    # Etapas de proceso (numéricas en lugar de booleanas)
    empastado = models.FloatField(blank=True, null=True)
    molino = models.FloatField(blank=True, null=True)
    matizado = models.FloatField(blank=True, null=True)
    emulsion = models.FloatField(blank=True, null=True)
    completado = models.FloatField(blank=True, null=True)
    envasado = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"Throughput {self.primario} - {self.fert_id}"

class ExcelExtra(models.Model):
    programa = models.ForeignKey(ProgramaProduccion, on_delete=models.CASCADE, related_name="extras")
    data = models.JSONField()  # guarda pares clave-valor de columnas adicionales