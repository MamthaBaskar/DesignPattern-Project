"""
PDF Report Generator using ReportLab.
Produces a professional, comprehensive audit report of document comparison results.
"""

from datetime import datetime, timezone
import io
import logging
from typing import List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..models.schemas import ChangeResult, ChangeType, ComparisonResponse, ImportanceLevel

logger = logging.getLogger(__name__)


def generate_comparison_pdf_report(comparison_data: ComparisonResponse) -> bytes:
    """
    Generates a formatted PDF report bytes from ComparisonResponse data.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15,
    )

    h2_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=8,
    )

    meta_label = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#334155"),
    )

    meta_val = ParagraphStyle(
        "MetaValue",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )

    body_style = ParagraphStyle(
        "CardBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
    )

    diff_old_style = ParagraphStyle(
        "DiffOld",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#991b1b"),
        backColor=colors.HexColor("#fef2f2"),
    )

    diff_new_style = ParagraphStyle(
        "DiffNew",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#166534"),
        backColor=colors.HexColor("#f0fdf4"),
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("AI Document Comparison & Change Analysis Report", title_style))
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    story.append(Paragraph(f"Generated on {now_str} • Powered by AI & Software Design Patterns", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=14))

    # Executive Summary Table
    summary = comparison_data.summary
    summary_data = [
        [
            Paragraph("<b>Old Document:</b>", meta_label),
            Paragraph(summary.old_filename, meta_val),
            Paragraph("<b>Total Changes:</b>", meta_label),
            Paragraph(str(summary.total_changes), meta_val),
        ],
        [
            Paragraph("<b>New Document:</b>", meta_label),
            Paragraph(summary.new_filename, meta_val),
            Paragraph("<b>Added / Deleted / Modified:</b>", meta_label),
            Paragraph(f"{summary.added_count} / {summary.deleted_count} / {summary.modified_count}", meta_val),
        ],
        [
            Paragraph("<b>Comparison Strategy:</b>", meta_label),
            Paragraph(summary.strategy_used, meta_val),
            Paragraph("<b>High / Med / Low Importance:</b>", meta_label),
            Paragraph(f"{summary.high_importance_count} / {summary.medium_importance_count} / {summary.low_importance_count}", meta_val),
        ],
        [
            Paragraph("<b>AI Status:</b>", meta_label),
            Paragraph(summary.ai_status, meta_val),
            Paragraph("<b>Analysis Time:</b>", meta_label),
            Paragraph(f"{summary.processing_time_seconds}s", meta_val),
        ],
    ]

    sum_table = Table(summary_data, colWidths=[110, 160, 140, 120])
    sum_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(sum_table)
    story.append(Spacer(1, 14))

    # Individual Changes
    story.append(Paragraph(f"Detailed Change Findings ({len(comparison_data.changes)} items)", h2_style))

    if not comparison_data.changes:
        story.append(Paragraph("No significant changes were detected between the two documents.", body_style))
    else:
        for idx, change in enumerate(comparison_data.changes, 1):
            card_elements = []

            # Color coding by change type
            type_bg = "#dbeafe"
            if change.change_type == ChangeType.ADDED:
                type_bg = "#dcfce7"
            elif change.change_type == ChangeType.DELETED:
                type_bg = "#fee2e2"

            imp_color = "#dc2626" if change.importance == ImportanceLevel.HIGH else ("#d97706" if change.importance == ImportanceLevel.MEDIUM else "#2563eb")

            header_text = (
                f"<b>#{idx} &nbsp; [{change.change_type.value}]</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"<b>Category:</b> {change.category.value} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"<b>Importance:</b> <font color='{imp_color}'><b>{change.importance.value}</b></font> &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"<b>Confidence:</b> {change.confidence.value}"
            )
            card_elements.append(Paragraph(header_text, meta_label))

            loc_str = f"<b>Section:</b> {change.section or 'General'}"
            if change.location:
                loc_str += f" &nbsp; ({change.location})"
            card_elements.append(Paragraph(loc_str, meta_val))
            card_elements.append(Spacer(1, 4))

            # Old and New Text Comparison
            if change.old_text:
                clean_old = change.old_text.replace("<", "&lt;").replace(">", "&gt;")
                card_elements.append(Paragraph(f"<b>Previous Text:</b><br/>{clean_old}", diff_old_style))
                card_elements.append(Spacer(1, 3))

            if change.new_text:
                clean_new = change.new_text.replace("<", "&lt;").replace(">", "&gt;")
                card_elements.append(Paragraph(f"<b>Current Text:</b><br/>{clean_new}", diff_new_style))
                card_elements.append(Spacer(1, 3))

            # Explanation & Practical Impact
            if change.explanation:
                clean_exp = change.explanation.replace("<", "&lt;").replace(">", "&gt;")
                card_elements.append(Paragraph(f"<b>AI Explanation:</b> {clean_exp}", body_style))
            if change.impact:
                clean_imp = change.impact.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
                card_elements.append(Paragraph(f"<b>Practical Impact:</b><br/>{clean_imp}", body_style))

            # Put in single cell box table
            card_table = Table([[card_elements]], colWidths=[530])
            card_table.setStyle(
                TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )

            story.append(KeepTogether([card_table, Spacer(1, 8)]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

