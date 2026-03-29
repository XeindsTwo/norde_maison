from io import BytesIO
from django.db.models import Sum, Avg, Min, Max
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

from .models import Order, OrderItem


def apply_excel_style(ws):
    thin = Side(border_style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    header_fill = PatternFill("solid", fgColor="D9EAF7")
    header_font = Font(bold=True, color="000000")
    center = Alignment(horizontal="center", vertical="center")
    left = Alignment(horizontal="left", vertical="center")

    for row_idx, row in enumerate(ws.iter_rows(), start=1):
        for cell in row:
            cell.border = border
            cell.alignment = center if row_idx == 1 else left
            if row_idx == 1:
                cell.fill = header_fill
                cell.font = header_font

    for column_cells in ws.columns:
        max_length = 0
        col_letter = column_cells[0].column_letter
        for cell in column_cells:
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(max_length + 4, 12)

    ws.freeze_panes = "A2"


def generate_report_content(report_type, date_from, date_to, file_format):
    buffer = BytesIO()

    if file_format == "xlsx":
        wb = Workbook()
        ws = wb.active

        if report_type == "sales_by_month":
            ws.title = "Продажи по месяцам"
            ws.append(["Год", "Месяц", "Сумма продаж"])
            data = (
                Order.objects.filter(created_at__date__range=[date_from, date_to])
                .values("created_at__year", "created_at__month")
                .annotate(total=Sum("total_price"))
                .order_by("created_at__year", "created_at__month")
            )
            for row in data:
                ws.append([row["created_at__year"], row["created_at__month"], float(row["total"] or 0)])

        elif report_type == "average_check":
            ws.title = "Средний чек"
            orders = Order.objects.filter(created_at__date__range=[date_from, date_to])
            agg = orders.aggregate(avg=Avg("total_price"), min=Min("total_price"), max=Max("total_price"))
            total_orders = orders.count()

            ws.append(["Показатель", "Значение", "Примечание"])
            ws.append(["Средний чек", float(agg["avg"] or 0), ""])
            ws.append(["Минимальный заказ", float(agg["min"] or 0), ""])
            ws.append(["Максимальный заказ", float(agg["max"] or 0), ""])
            ws.append(["Всего заказов", total_orders, ""])

        elif report_type == "top_products":
            ws.title = "Популярные товары"
            ws.append(["Товар", "Цвет", "Размер", "Количество"])
            data = (
                OrderItem.objects.filter(order__created_at__date__range=[date_from, date_to])
                .values("product_name", "color", "size")
                .annotate(total_qty=Sum("quantity"))
                .order_by("-total_qty")
            )
            for row in data:
                ws.append([row["product_name"], row["color"], row["size"], row["total_qty"]])

        apply_excel_style(ws)
        wb.save(buffer)

    elif file_format == "pdf":
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )
        story = []
        story.append(Paragraph("Отчёт", styles["Title"]))
        story.append(Spacer(1, 8))

        if report_type == "sales_by_month":
            story.append(Paragraph("Продажи по месяцам", styles["Heading2"]))
            data = [["Год", "Месяц", "Сумма продаж"]]
            rows = (
                Order.objects.filter(created_at__date__range=[date_from, date_to])
                .values("created_at__year", "created_at__month")
                .annotate(total=Sum("total_price"))
                .order_by("created_at__year", "created_at__month")
            )
            for row in rows:
                data.append([str(row["created_at__year"]), str(row["created_at__month"]), f'{float(row["total"] or 0):.2f}'])
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]))
            story.append(table)

        elif report_type == "average_check":
            orders = Order.objects.filter(created_at__date__range=[date_from, date_to])
            agg = orders.aggregate(avg=Avg("total_price"), min=Min("total_price"), max=Max("total_price"))
            total_orders = orders.count()

            data = [
                ["Показатель", "Значение"],
                ["Средний чек", f"{float(agg['avg'] or 0):.2f}"],
                ["Минимальный заказ", f"{float(agg['min'] or 0):.2f}"],
                ["Максимальный заказ", f"{float(agg['max'] or 0):.2f}"],
                ["Всего заказов", str(total_orders)],
            ]
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]))
            story.append(table)

        elif report_type == "top_products":
            data = [["Товар", "Цвет", "Размер", "Количество"]]
            rows = (
                OrderItem.objects.filter(order__created_at__date__range=[date_from, date_to])
                .values("product_name", "color", "size")
                .annotate(total_qty=Sum("quantity"))
                .order_by("-total_qty")
            )
            for row in rows:
                data.append([row["product_name"], row["color"], row["size"], str(row["total_qty"])])

            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]))
            story.append(table)

        doc.build(story)

    else:
        raise ValueError("Unsupported format")

    buffer.seek(0)
    filename = f"report_{report_type}_{date_from}_to_{date_to}.{file_format}"
    return buffer, filename