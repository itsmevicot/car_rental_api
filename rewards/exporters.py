"""Export formatters for reward transaction history."""

import csv
import io

from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def csv_response(transactions, email: str) -> HttpResponse:
    """Return a CSV download response for a reward transaction queryset.

    Args:
        transactions: Iterable of reward transactions to export.
        email: Customer email used in the filename.

    Returns:
        HttpResponse: CSV attachment response.
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="rewards_{email}.csv"'
    writer = csv.writer(response)
    writer.writerow(["id", "type", "points", "reason", "rental_id", "created_at"])
    for txn in transactions:
        writer.writerow([txn.id, txn.type, txn.points, txn.reason, txn.rental_id, txn.created_at])
    return response


def pdf_response(transactions, email: str) -> HttpResponse:
    """Return a PDF download response for a reward transaction list.

    Args:
        transactions: Iterable of reward transactions to export.
        email: Customer email used in the filename and header.

    Returns:
        HttpResponse: PDF attachment response.
    """
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, 800, f"Reward History - {email}")
    pdf.setFont("Helvetica", 10)
    y = 770
    for txn in transactions:
        pdf.drawString(50, y, f"{txn.created_at.date()}  {txn.type:8}  {txn.points:+5}pts  {txn.reason}")
        y -= 18
        if y < 50:
            pdf.showPage()
            y = 800
    pdf.save()
    buf.seek(0)
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="rewards_{email}.pdf"'
    return response
