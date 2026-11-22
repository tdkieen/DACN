"""Trang Đề xuất mua hàng — Figma frame "06 · Đề xuất mua hàng"."""

import reflex as rx

from frontend import theme as t
from frontend.components import ui
from frontend.components.header import layout
from frontend.state import State

COLS = [("Mã phiếu", "15.5%"), ("Ngày tạo", "15.3%"), ("Nội dung đề xuất", "29%"), ("Tổng tiền dự kiến", "17.3%"), ("Trạng thái", "15.4%"), ("", "7.5%")]

FILTERS = [("ALL", "Tất cả"), ("CHO_DUYET", "Chờ duyệt"), ("DA_DUYET", "Đã duyệt"), ("DA_SUA", "Đã sửa"), ("TU_CHOI", "Từ chối")]


def filter_tab(value: str, label: str) -> rx.Component:
    active = State.proposal_filter == value
    return rx.box(
        rx.text(
            label + " (" + State.proposal_counts[value].to_string() + ")",
            font_size="13px",
            font_weight=rx.cond(active, "600", "500"),
            color=rx.cond(active, t.PRIMARY, t.MUTED),
            white_space="nowrap",
        ),
        padding="0 2px 14px 2px",
        border_bottom="3px solid",
        border_color=rx.cond(active, t.PRIMARY, "transparent"),
        margin_bottom="-1px",
        cursor="pointer",
        on_click=State.set_proposal_filter(value),
    )


def proposal_row(p: rx.Var) -> rx.Component:
    return rx.link(
        ui.table_row(
            ui.cell(p["code"], COLS[0][1], font_size="13px", font_weight="600", color=t.PRIMARY),
            ui.cell(p["created"], COLS[1][1], font_size="12px", color=t.TEXT),
            ui.cell(p["summary"], COLS[2][1], font_size="13px", padding_right="12px"),
            ui.cell(p["total_fmt"], COLS[3][1], font_size="13px", color=t.TEXT),
            ui.cell(ui.pill(p["status_label"], tone=p["tone"], border_radius="4px", font_size="11px"), COLS[4][1]),
            ui.cell(rx.icon("arrow-right", size=16, color=t.MUTED), COLS[5][1], display="flex", justify_content="flex-end"),
            height="50px",
            background=rx.cond(p["status"] == "CHO_DUYET", t.PRIMARY_TINT, "transparent"),
        ),
        href="/proposals/" + p["id"].to_string(),
        underline="none",
        color="inherit",
        display="block",
    )


def workflow_card() -> rx.Component:
    def stepx(num: str, text: str) -> rx.Component:
        return rx.hstack(
            rx.text(num, font_size="24px", font_weight="600", color="#B3CFEB"),
            rx.text(text, font_size="13px", font_weight="500", color="#FFFFFF"),
            align="center",
            gap="20px",
            spacing="0",
        )

    return rx.box(
        rx.text("Một quy trình rõ ràng. Mỗi quyết định đều có người chịu trách nhiệm.", font_size="18px", font_weight="600", color="#FFFFFF"),
        rx.grid(
            stepx("01", "AI phát hiện & đề xuất"),
            stepx("02", "Quản lý xem xét / điều chỉnh"),
            stepx("03", "Duyệt để tạo đơn mua hàng"),
            columns=rx.breakpoints(initial="1", md="3"),
            gap="20px",
            width="100%",
            margin_top="22px",
        ),
        background=t.NAVY,
        border_radius=t.RADIUS,
        padding="18px 22px 26px 22px",
        width="100%",
    )


def proposals_page() -> rx.Component:
    return layout(
        rx.vstack(
            ui.page_title(
                "Đề xuất mua hàng",
                "Xem xét các đề xuất do AI tạo trước khi chuyển thành đơn mua hàng.",
                ui.primary_button(
                    rx.cond(State.generating, "AI đang phân tích…", "+  Tạo đề xuất với AI"),
                    on_click=State.generate_ai_proposal,
                    disabled=State.generating,
                    width="200px",
                    justify_content="flex-start",
                    white_space="pre",
                ),
            ),
            rx.grid(
                ui.kpi_card("Chờ phê duyệt", State.kpi_pending, State.pending_total_fmt + " dự kiến", inline_hint=True),
                ui.kpi_card("Đã duyệt tháng này", ui.pad2(State.approved_this_month), "Đã được quản lý xác nhận", inline_hint=True),
                ui.kpi_card("Cần điều chỉnh", ui.pad2(State.proposal_counts["DA_SUA"].to(int)), "Chờ xem xét lại số lượng", inline_hint=True),
                columns=rx.breakpoints(initial="1", md="3"),
                gap="22px",
                width="100%",
                margin_bottom="20px",
            ),
            ui.card(
                rx.text("Tất cả đề xuất", font_size="16px", font_weight="600", color=t.INK),
                rx.hstack(
                    rx.hstack(*[filter_tab(v, label) for v, label in FILTERS], gap="40px", spacing="0", overflow_x="auto", align="end"),
                    rx.spacer(),
                    rx.input(
                        rx.input.slot(rx.icon("search", size=15, color=t.SUBTLE)),
                        placeholder="Tìm mã phiếu...",
                        value=State.proposal_search,
                        on_change=State.set_proposal_search,
                        width="200px",
                        height="40px",
                        margin_bottom="6px",
                    ),
                    width="100%",
                    align="end",
                    wrap="wrap",
                    gap="12px",
                    border_bottom=f"1px solid {t.BORDER}",
                    margin_top="6px",
                    margin_bottom="18px",
                ),
                rx.box(
                    rx.box(
                        ui.table_header(COLS, height="38px"),
                        rx.cond(
                            State.proposal_page_rows.length() > 0,
                            rx.foreach(State.proposal_page_rows, proposal_row),
                            ui.empty_state("Chưa có phiếu đề xuất phù hợp."),
                        ),
                        min_width="820px",
                    ),
                    overflow_x="auto",
                    width="100%",
                ),
                ui.pagination(State.proposal_page_label, State.proposal_page, State.proposal_total_pages, State.prev_proposal_page, State.next_proposal_page),
                padding="18px 20px 14px 20px",
                margin_bottom="20px",
            ),
            workflow_card(),
            spacing="0",
            width="100%",
        ),
        active_page="proposals",
    )
