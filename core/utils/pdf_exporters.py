# ==================================================
# FILE: Mbayar/core/utils/pdf_exporters.py
# PATH: D:/Project Pyton/Mbayar/core/utils/pdf_exporters.py
# FUNGSI: Class untuk export ke PDF
# ==================================================

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.http import HttpResponse
import io
from datetime import datetime

class PDFExporter:
    """Base class untuk export PDF"""
    
    def __init__(self, title="Laporan", pagesize=A4):
        self.buffer = io.BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer, 
            pagesize=pagesize,
            rightMargin=30, 
            leftMargin=30, 
            topMargin=30, 
            bottomMargin=30
        )
        self.styles = getSampleStyleSheet()
        self.elements = []
        self.title = title
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom styles"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.maroon,
            alignment=1,  # Center
            spaceAfter=20
        )
        
        self.normal_style = self.styles['Normal']
        self.normal_style.fontSize = 9
        
        self.header_style = ParagraphStyle(
            'Header',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.whitesmoke,
            alignment=1,
            backColor=colors.maroon
        )
    
    def add_title(self, text):
        """Tambah judul"""
        self.elements.append(Paragraph(text, self.title_style))
        self.elements.append(Spacer(1, 10))
    
    def add_paragraph(self, text, style='Normal'):
        """Tambah paragraph"""
        self.elements.append(Paragraph(text, self.styles[style]))
        self.elements.append(Spacer(1, 6))
    
    def add_period_info(self, start_date, end_date):
        """Tambah info periode"""
        text = f"Periode: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        self.elements.append(Paragraph(text, self.styles['Heading2']))
        self.elements.append(Spacer(1, 20))
    
    def add_table(self, data, col_widths=None):
        """Tambah table"""
        if col_widths is None:
            # Auto calculate
            col_widths = [self._get_col_width(data, i) for i in range(len(data[0]))]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.maroon),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        self.elements.append(table)
        self.elements.append(Spacer(1, 15))
    
    def _get_col_width(self, data, col_idx):
        """Hitung lebar kolom berdasarkan konten"""
        max_len = 0
        for row in data:
            cell = str(row[col_idx])
            max_len = max(max_len, len(cell))
        # Convert to points (approximate)
        return min(max_len * 6 + 10, 150)
    
    def add_summary_table(self, data):
        """Tambah table summary"""
        table = Table(data, colWidths=[150, 150])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        self.elements.append(table)
        self.elements.append(Spacer(1, 20))
    
    def add_footer(self):
        """Tambah footer"""
        self.elements.append(Spacer(1, 20))
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.elements.append(Paragraph(f"Diekspor pada: {timestamp}", self.styles['Italic']))
    
    def get_response(self, filename):
        """Return HttpResponse dengan file PDF"""
        self.doc.build(self.elements)
        self.buffer.seek(0)
        
        response = HttpResponse(self.buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class SalesPDFExporter(PDFExporter):
    """Export laporan penjualan ke PDF"""
    
    def export(self, orders, start_date, end_date):
        self.add_title("LAPORAN PENJUALAN")
        self.add_period_info(start_date, end_date)
        
        # Summary
        total_penjualan = sum(float(o.total) for o in orders)
        total_transaksi = orders.count()
        rata_rata = total_penjualan / total_transaksi if total_transaksi > 0 else 0
        
        summary_data = [
            ['Total Penjualan', f"Rp {total_penjualan:,.0f}"],
            ['Jumlah Transaksi', str(total_transaksi)],
            ['Rata-rata per Transaksi', f"Rp {rata_rata:,.0f}"]
        ]
        self.add_summary_table(summary_data)
        
        # Table data
        table_data = [['No', 'Tanggal', 'No. Order', 'Pelanggan', 'Total']]
        
        for i, order in enumerate(orders[:50], 1):  # Batasi 50
            customer = order.customer_name
            if len(customer) > 20:
                customer = customer[:20] + '...'
            
            table_data.append([
                str(i),
                order.order_date.strftime('%d/%m/%Y'),
                order.order_no,
                customer,
                f"Rp {order.total:,.0f}"
            ])
        
        if len(orders) > 50:
            table_data.append(['...', '', '', '', f"Dan {len(orders)-50} transaksi lainnya"])
        
        self.add_table(table_data, [30, 70, 100, 100, 100])
        self.add_footer()
        
        return self