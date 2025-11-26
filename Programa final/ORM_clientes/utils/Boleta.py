# Boleta.py
# -------------------------------------------------------------------------
#   Generador de Boleta PDF (compatible con BD y Pedido nuevo)
# -------------------------------------------------------------------------

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle


class Boleta:
    def __init__(self, detalle, subtotal, iva, total, fecha=None):
        """
        detalle: lista de tuplas (descripcion, cantidad, precio_unitario, subtotal_linea)
        subtotal, iva, total: montos numéricos
        fecha: datetime personalizado (opcional)
        """
        self.detalle = detalle
        self.subtotal = subtotal
        self.iva = iva
        self.total = total
        self.fecha = fecha if fecha is not None else datetime.now()

        # Datos del restaurante (puedes editarlos)
        self.razon_social = "Restaurante Crunch"
        self.rut = "00.000.000-0"
        self.direccion = "Avenida Principal 123"
        self.telefono = "+56 9 0000 0000"
        self.titulo = "Boleta Restaurante"

    # ---------------------------------------------------------------------
    #   Formateo monetario
    # ---------------------------------------------------------------------
    def _dinero(self, n):
        """Formato chileno $X.XXX,00"""
        s = f"{float(n):,.2f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"${s}"

    # ---------------------------------------------------------------------
    #   Generación del PDF
    # ---------------------------------------------------------------------
    def generar_pdf(self, ruta_salida):
        c = canvas.Canvas(ruta_salida, pagesize=A4)
        w, h = A4

        # ------------------------------------------------------------
        #   Encabezado
        # ------------------------------------------------------------
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, h - 2 * cm, self.titulo)

        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, h - 2.8 * cm, self.razon_social)
        c.drawString(2 * cm, h - 3.2 * cm, f"RUT: {self.rut}")
        c.drawString(2 * cm, h - 3.6 * cm, f"Dirección: {self.direccion}")
        c.drawString(2 * cm, h - 4.0 * cm, f"Teléfono: {self.telefono}")

        c.drawRightString(
            w - 2 * cm, h - 2.8 * cm,
            self.fecha.strftime("Fecha: %d/%m/%Y %H:%M:%S")
        )

        # ------------------------------------------------------------
        #   Tabla de productos
        # ------------------------------------------------------------
        data = [["Descripción", "Cant.", "P. Unitario", "Subtotal"]]

        for desc, cant, punit, subt in self.detalle:
            data.append([
                str(desc),
                str(cant),
                self._dinero(punit),
                self._dinero(subt)
            ])

        col_widths = [7 * cm, 2.3 * cm, 3.5 * cm, 3.5 * cm]

        table = Table(data, colWidths=col_widths)

        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))

        # Posición de la tabla
        table_x = 2 * cm
        table_y = h - 6 * cm - (len(data) * 0.6 * cm)

        table.wrapOn(c, w, h)
        table.drawOn(c, table_x, table_y)

        # ------------------------------------------------------------
        #   Totales
        # ------------------------------------------------------------
        y = table_y - 1 * cm

        c.setFont("Helvetica-Bold", 11)

        c.drawRightString(15 * cm, y, "Subtotal:")
        c.drawRightString(19 * cm, y, self._dinero(self.subtotal))

        y -= 0.6 * cm
        c.drawRightString(15 * cm, y, "IVA (19%):")
        c.drawRightString(19 * cm, y, self._dinero(self.iva))

        y -= 0.6 * cm
        c.drawRightString(15 * cm, y, "Total:")
        c.drawRightString(19 * cm, y, self._dinero(self.total))

        # ------------------------------------------------------------
        #   Mensaje final
        # ------------------------------------------------------------
        c.setFont("Helvetica", 9)
        y -= 1 * cm
        c.drawCentredString(w / 2, y, "Gracias por su compra. Los productos no tienen garantía.")

        # Finalizar
        c.showPage()
        c.save()
