# Menupdf.py
from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor

AZUL    = HexColor("#1e88e5")
GRIS_HD = HexColor("#eef2f7")
GRIS_F1 = HexColor("#f7f9fc")

def _fmt(n: int) -> str:
    return f"${n:,}".replace(",", ".")

def generar_carta_pdf(ruta_salida: str, menus_disponibles: List[str], db,
                      titulo="Restaurante", subtitulo="Carta 2025"):

    c = canvas.Canvas(ruta_salida, pagesize=A4)
    w, h = A4

    # --------------------------------------------------------
    #    Franja superior
    # --------------------------------------------------------
    c.setFillColor(AZUL)
    c.rect(2*cm, h-4*cm, w-4*cm, 2*cm, fill=1, stroke=0)

    # Título y subtítulo
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2.4*cm, h-2.7*cm, titulo)

    c.setFont("Helvetica", 10)
    c.drawString(2.4*cm, h-3.35*cm, subtitulo)

    # --------------------------------------------------------
    #     Cabecera
    # --------------------------------------------------------
    top_y = h - 5.2*cm
    c.setFillColor(GRIS_HD)
    c.rect(2*cm, top_y-0.15*cm, w-4*cm, 0.9*cm, fill=1, stroke=0)

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2.4*cm, top_y+0.35*cm, "Menú")
    c.drawRightString(w-2.4*cm, top_y+0.35*cm, "Precio")

    c.line(2*cm, top_y+0.1*cm, w-2*cm, top_y+0.1*cm)

    # --------------------------------------------------------
    #      Filas
    # --------------------------------------------------------
    y = top_y - 1.1*cm
    alt = True

    from models import Menu as MenuDB
    for nombre_menu in menus_disponibles:
        menu_obj = db.query(MenuDB).filter_by(nombre=nombre_menu).first()
        if not menu_obj:
            continue
        if y < 4*cm:  # salto de página
            c.showPage()
            w, h = A4
            # repetir cabecera
            c.setFillColor(AZUL)
            c.rect(2*cm, h-4*cm, w-4*cm, 2*cm, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(2.4*cm, h-2.7*cm, titulo)
            c.setFont("Helvetica", 10)
            c.drawString(2.4*cm, h-3.35*cm, subtitulo)
            top_y = h - 5.2*cm
            c.setFillColor(GRIS_HD)
            c.rect(2*cm, top_y-0.15*cm, w-4*cm, 0.9*cm, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(2.4*cm, top_y+0.35*cm, "Menú")
            c.drawRightString(w-2.4*cm, top_y+0.35*cm, "Precio")
            c.line(2*cm, top_y+0.1*cm, w-2*cm, top_y+0.1*cm)
            y = top_y - 1.1*cm
            alt = True
        # Fondo alternado
        if alt:
            c.setFillColor(GRIS_F1)
            c.roundRect(2*cm, y-0.15*cm, w-4*cm, 1.3*cm, 10, fill=1, stroke=0)
        alt = not alt
        # Nombre menú
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2.4*cm, y+0.7*cm, nombre_menu)
        # Descripción
        if menu_obj.descripcion:
            c.setFont("Helvetica", 9)
            c.drawString(2.4*cm, y+0.2*cm, menu_obj.descripcion)
        # Precio desde BD
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(w-2.4*cm, y+0.7*cm, _fmt(menu_obj.precio))
        # Separador de fila
        c.setStrokeColor(AZUL)
        c.setLineWidth(0.5)
        c.line(2.2*cm, y-0.1*cm, w-2.2*cm, y-0.1*cm)
        y -= 1.3*cm

    c.showPage()
    c.save()
