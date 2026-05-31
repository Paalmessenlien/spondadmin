"""
PDF rendering for a TrainingPlan. Single function: render_plan_pdf(plan,
shifts) → bytes. Uses reportlab (pure Python, no system deps) so the
existing python:3.13-slim image needs no Dockerfile changes.

The layout is intentionally compact and printable: a header with the
plan name + period + description + summary, then a chronological table
of shifts. The table flows across pages as needed.
"""
from __future__ import annotations

from datetime import date as date_type, datetime
from io import BytesIO
from typing import Iterable, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.training_plan import TrainingPlan
from app.models.training_shift import TrainingShift


# Norwegian 3-letter weekday abbreviations — matches the form used in the
# UI (calendar header). Index by Python weekday() (0 = Monday).
_NB_WEEKDAYS = ("man", "tir", "ons", "tor", "fre", "lør", "søn")

# Status colors, mirrored from the calendar legend in the frontend.
_STATUS_COLOR = {
    "draft": colors.HexColor("#3b82f6"),      # blue-500
    "published": colors.HexColor("#16a34a"),  # green-600
    "cancelled": colors.HexColor("#6b7280"),  # gray-500
}


def _fmt_date(d: date_type) -> str:
    return d.strftime("%d.%m.%y")


def _weekday(d: date_type) -> str:
    return _NB_WEEKDAYS[d.weekday()]


def _fmt_time(t) -> str:
    if t is None:
        return ""
    return t.strftime("%H:%M")


def _leader_label(shift: TrainingShift) -> str:
    if shift.leader is not None:
        # "Pål M." — first name + last initial. Avoids exposing full
        # surnames in print while still being identifiable.
        last_initial = (
            f"{shift.leader.last_name[0]}." if shift.leader.last_name else ""
        )
        return f"{shift.leader.first_name} {last_initial}".strip()
    if shift.raw_initials:
        return shift.raw_initials
    return "—"


def _leader_summary(shift_list: list[TrainingShift]) -> list[tuple[str, int]]:
    """Count how many shifts each person leads in the plan.

    Grouping key is the leader's identity, not their display label: a linked
    Member is keyed by id, an unlinked entry by its raw initials, so two
    different people who happen to render to the same "Pål M." label are still
    counted separately. Returns (label, count) sorted by count descending then
    label ascending, with any unassigned shifts collapsed into a single
    trailing "(unassigned)" row.
    """
    counts: dict[tuple, int] = {}
    labels: dict[tuple, str] = {}
    for s in shift_list:
        if s.leader is not None:
            key: tuple = ("member", s.leader.id)
        elif s.raw_initials:
            key = ("initials", s.raw_initials)
        else:
            key = ("unassigned",)
        counts[key] = counts.get(key, 0) + 1
        labels[key] = _leader_label(s)

    unassigned = counts.pop(("unassigned",), 0)
    summary = [(labels[k], c) for k, c in counts.items()]
    summary.sort(key=lambda lc: (-lc[1], lc[0].lower()))
    if unassigned:
        summary.append(("(unassigned)", unassigned))
    return summary


def render_plan_pdf(
    plan: TrainingPlan,
    shifts: Iterable[TrainingShift],
    *,
    generated_at: Optional[datetime] = None,
) -> bytes:
    """Build the PDF and return its bytes."""
    generated_at = generated_at or datetime.utcnow()
    shift_list = sorted(
        shifts,
        key=lambda s: (s.date, (s.session_type.name if s.session_type else "")),
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        title=plan.name,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "PlanH1",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=2,
    )
    h2 = ParagraphStyle(
        "PlanH2",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#374151"),
        spaceAfter=2,
    )
    body = ParagraphStyle(
        "PlanBody",
        parent=styles["BodyText"],
        fontSize=9,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=6,
    )
    footer = ParagraphStyle(
        "PlanFooter",
        parent=styles["BodyText"],
        fontSize=8,
        textColor=colors.HexColor("#9ca3af"),
        alignment=TA_LEFT,
    )

    # Distinct session types in this plan — useful for the summary line.
    session_type_names: list[str] = []
    seen: set[str] = set()
    for s in shift_list:
        if s.session_type is None:
            continue
        if s.session_type.name not in seen:
            seen.add(s.session_type.name)
            session_type_names.append(s.session_type.name)

    story = []
    story.append(Paragraph("TRAINING PLAN", h2))
    story.append(Paragraph(plan.name, h1))
    story.append(
        Paragraph(
            f"{_fmt_date(plan.period_start)} – {_fmt_date(plan.period_end)}",
            h2,
        )
    )
    if plan.description:
        story.append(Paragraph(plan.description.replace("\n", "<br/>"), body))
    story.append(
        Paragraph(
            f"{len(shift_list)} shift(s) across {len(session_type_names)} session type(s).",
            body,
        )
    )
    story.append(Spacer(1, 4 * mm))

    # Per-leader summary: how many trainings each person leads in this plan.
    # Sits at the top so a coordinator sees the workload distribution at a
    # glance before the detailed chronological table further down.
    leader_counts = _leader_summary(shift_list)
    if leader_counts:
        story.append(Paragraph("Trainings per leader", h2))
        summary_rows: list[list[str]] = [["Leader", "Trainings"]]
        summary_rows += [[label, str(count)] for label, count in leader_counts]
        summary_table = Table(
            summary_rows,
            colWidths=[60 * mm, 30 * mm],
            repeatRows=1,
        )
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("TOPPADDING", (0, 0), (-1, 0), 6),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                    ("TOPPADDING", (0, 1), (-1, -1), 4),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.HexColor("#d1d5db")),
                    ("LINEBELOW", (0, -1), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#fafafa")],
                    ),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 6 * mm))

    # Table.
    header = ["Date", "Day", "Session type", "Time", "Leader", "Status"]
    rows: list[list[str]] = [header]
    for s in shift_list:
        st = s.session_type
        start = (
            s.start_time_override
            or (st.default_start_time if st else None)
        )
        end = (
            s.end_time_override
            or (st.default_end_time if st else None)
        )
        time_str = f"{_fmt_time(start)}–{_fmt_time(end)}" if start and end else ""
        rows.append(
            [
                _fmt_date(s.date),
                _weekday(s.date),
                st.name if st else "—",
                time_str,
                _leader_label(s),
                s.status,
            ]
        )

    # Column widths sum to ~180mm (A4 portrait minus margins).
    col_widths = [
        20 * mm,  # date
        12 * mm,  # day
        58 * mm,  # session type
        24 * mm,  # time
        38 * mm,  # leader
        28 * mm,  # status
    ]
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("ALIGN", (0, 0), (1, -1), "LEFT"),
            ("ALIGN", (3, 0), (3, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.HexColor("#d1d5db")),
            ("LINEBELOW", (0, -1), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
        ]
    )
    # Color-code the status column per row.
    for i, s in enumerate(shift_list, start=1):
        color = _STATUS_COLOR.get(s.status, colors.HexColor("#6b7280"))
        table_style.add("TEXTCOLOR", (5, i), (5, i), color)
        table_style.add("FONTNAME", (5, i), (5, i), "Helvetica-Bold")
    table.setStyle(table_style)
    story.append(table)

    story.append(Spacer(1, 6 * mm))
    story.append(
        Paragraph(
            f"Generated {generated_at.strftime('%d.%m.%Y %H:%M')} UTC · spondadmin",
            footer,
        )
    )

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
