import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from flask import current_app
from app.models.payment import Payment
from app.models.fine import Fine
from app.models.student import Student


def generate_receipt(payment: Payment, fine: Fine, student: Student) -> str:
    """
    Generates a PDF receipt for a completed payment using ReportLab.

    On Render (production): builds PDF in memory, uploads to Cloudinary,
    and returns the public Cloudinary URL. The URL is stored in
    payment.receipt_path and sent as a Twilio WhatsApp media attachment.

    Locally (development): saves PDF to app/static/receipts/ and returns
    the relative path 'receipts/receipt_<id>.pdf'.

    Args:
        payment: Completed Payment record
        fine:    The Fine that was paid
        student: The Student who paid

    Returns:
        str: Cloudinary URL in production OR relative path locally.
    """
    # ─── Build PDF into a memory buffer ────────────────────────────────────────
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()
    story = []

    # ─── Header ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.grey,
        spaceAfter=12
    )

    story.append(Paragraph("LibraryHub 2.0", title_style))
    story.append(Paragraph("Payment Receipt", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#1a1a2e")))
    story.append(Spacer(1, 0.5 * cm))

    # ─── Receipt Details Table ─────────────────────────────────────────────────
    receipt_data = [
        ["Receipt No.", f"RCP-{payment.id:06d}"],
        ["Date", (payment.completed_at or datetime.utcnow()).strftime("%d %b %Y %H:%M")],
        ["Payment Method", payment.payment_method.capitalize()],
        ["", ""],
        ["Student Name", student.full_name],
        ["Enrollment No.", student.enrollment_number],
        ["Department", student.department],
        ["", ""],
        ["Fine Type", fine.fine_type.replace("_", " ").title()],
        ["Description", fine.description or "—"],
        ["Amount Paid", f"₹ {float(payment.amount):.2f}"],
        ["Status", "PAID ✓"],
    ]

    if payment.razorpay_payment_id:
        receipt_data.append(["Razorpay ID", payment.razorpay_payment_id])

    table = Table(receipt_data, colWidths=[6 * cm, 11 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1a1a2e")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.white, colors.HexColor("#f9f9f9")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(table)
    story.append(Spacer(1, 1 * cm))

    # ─── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 0.3 * cm))
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        alignment=1  # center
    )
    story.append(Paragraph(
        "This is a computer-generated receipt. No signature required.",
        footer_style
    ))
    story.append(Paragraph(
        f"Generated on {datetime.utcnow().strftime('%d %b %Y %H:%M')} UTC | LibraryHub 2.0",
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    # ─── Store PDF: Cloudinary (prod) or local disk (dev) ─────────────────────
    import os as _os
    cloudinary_url = _os.environ.get("CLOUDINARY_URL", "")

    if cloudinary_url and cloudinary_url.startswith("cloudinary://"):
        # Production: upload to Cloudinary and return public URL
        import cloudinary
        import cloudinary.uploader

        # Explicitly configure from env var to avoid auto-parse issues
        cloudinary.config(cloudinary_url=cloudinary_url)

        result = cloudinary.uploader.upload(
            io.BytesIO(pdf_bytes),          # file-like object, not raw bytes
            resource_type="image",
            public_id=f"libraryhub_receipts/receipt_{payment.id}",
            overwrite=True,
            format="pdf"
        )
        return result["secure_url"]
    else:
        # Local dev: save to app/static/receipts/ (served by Flask)
        receipts_dir = current_app.config["RECEIPTS_FOLDER"]
        os.makedirs(receipts_dir, exist_ok=True)
        filename = f"receipt_{payment.id}.pdf"
        filepath = os.path.join(receipts_dir, filename)
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)
        return f"receipts/{filename}"