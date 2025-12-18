# arquitecura limpia
"""
Según lo que he visto:
    1. Domain (Entities - logica de negocio)
    2. Application (use cases - logica de la aplicación)
    3. Infrastructure ( adapters )
    4. Presentation (Recursos externos)
"""
# solitud / requerimientos
"""
    Desarrollar un microservicio en Python que reciba datos en formato JSON
    mediante una API REST y genere un reporte en PDF basado en esa información.
    El servicio debe validar el contenido recibido, construir tablas y/o
    gráficos simples dentro del PDF y devolverlo como archivo descargable en la
    respuesta.
    Crees que puedas tener el contenedor listo para el otro jueves?
"""
# psudocodigo
"""
# partes
1. API: enpoints, pasos: request -> autentication-> process-> response
2. Microservicio: puede funcionar independiente
3. Python: tecnología
4. REST: siguiendo los principios de rest, cliente-servidor, request independientes,
con cache para optimizar request, sistema de capas, codigo en demanda, interface uniforme
5. Generar pdf
6. graficos
7. respuesta: archivo descargable
8. contenedor: microservicio montado en docker

# pasos
1. montar endpoint que reciba información (put/post) de la venta de un producto en formato json;
los valores seran nombre del producto, valor, y cantidad vendida
2. exponer endpoint
3. recibir request
4. autenticar usuario (after)
5. validar autorización de usuario (after)
6. validar información
7. manejar errores
8. procesar información:
    a. crear graficas
9. Crear pdf
    a. dar formato al pdf
    b. incluir graficas
10. regresar pdf como respuesta y que sea descargable
    a. regresar pdf
    b. pdf descargable
"""
# we use fastapi:
# to create a API with FastAPI
# handle error responses with HTTPException
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
# we use pydantic:
# BaseModel to ask for request body
# Field to validate with Annotate more constrictions over the fields
from pydantic import BaseModel, Field
# we use decimal to get more precition with money data
from decimal import Decimal
# we use reportlab and io to respon with a pdf:
# to create pdf file
# to crear graphs
import io
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib import colors
from reportlab.graphics import renderPDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


app = FastAPI()

# -- domain --
class ItemSale(BaseModel):
    name: str
    price: float = Field(gt=0, description="The price must be greater than zero")
    quantity: int = Field(gt=0, description="The price must be greater than zero")

# -- application / use_cases --
def create_graph(items):
    # Extraer nombres para las etiquetas y cantidades para las barras
    names = [p.name for p in items]
    prices = [p.price for p in items]

    # Crear un contenedor para el dibujo (Ancho, Alto)
    draw = Drawing(400, 200)

    # Configurar el gráfico de barras
    bar_chart = VerticalBarChart()
    bar_chart.x = 50
    bar_chart.y = 50
    bar_chart.height = 125
    bar_chart.width = 300
    bar_chart.data = [prices] # Debe ser una lista de listas
    bar_chart.strokeColor = colors.black

    # Configurar ejes
    bar_chart.valueAxis.valueMin = 0
    bar_chart.valueAxis.valueMax = max(prices) + 5.0
    bar_chart.categoryAxis.categoryNames = names
    bar_chart.categoryAxis.labels.boxAnchor = 'ne'
    bar_chart.categoryAxis.labels.dx = 0
    bar_chart.categoryAxis.labels.dy = -10
    bar_chart.categoryAxis.labels.angle = 30 # Rotar nombres para que quepan

    # Color de las barras
    bar_chart.bars[0].fillColor = colors.skyblue

    draw.add(bar_chart)
    return draw

# this is here for reference, and as a remainder of a first try
# def create_pdf(items):
#     3. Construir el PDF
#     doc = SimpleDocTemplate("reporte_productos.pdf")
#     elementos = []
#     estilos = getSampleStyleSheet()

#     elementos.append(Paragraph("Reporte de Inventario", estilos['Title']))
#     elementos.append(Spacer(1, 12))
#     elementos.append(Paragraph("Cantidad de productos en existencia:", estilos['Normal']))
#     elementos.append(Spacer(1, 20))

#     Añadir la gráfica al PDF
#     elementos.append(create_graph(items))

#     doc.build(elementos)
#     print("PDF generado con éxito: reporte_productos.pdf")

def create_pdf_in_memory(items):
    # 1. Crear el buffer de memoria
    buffer = io.BytesIO()

    # 2. Construir el PDF usando el buffer en lugar de un nombre de archivo
    doc = SimpleDocTemplate(buffer)
    elementos = []
    estilos = getSampleStyleSheet()

    elementos.append(Paragraph("Reporte de Inventario", estilos['Title']))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph("Cantidad de productos en existencia:", estilos['Normal']))
    elementos.append(Spacer(1, 20))

    # Añadir la gráfica al PDF
    elementos.append(create_graph(items))

    doc.build(elementos)
    print("PDF generado con éxito: reporte_productos.pdf")

    # 3. Mover el "puntero" al inicio del buffer para poder leerlo
    buffer.seek(0)

    return buffer

# -- infrastructure / adapter --
def process_data(list_of_items_sales: list):
    return create_pdf_in_memory(list_of_items_sales)
# -- External / presentation --

# this is here for reference, and as a remainder of a first try
# @app.post("/pdf-report")
# async def PDFReport(items: list[ItemSale]):
#     # read data and get graphics
#     return process_data(items)

@app.post("/pdf-report")
async def pdf_report_endpoint(items: list[ItemSale]):
    try:
        # Generamos el buffer con el contenido del PDF
        pdf_buffer = process_data(items)

        # Retornamos una respuesta de streaming
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=reporte_ventas.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
