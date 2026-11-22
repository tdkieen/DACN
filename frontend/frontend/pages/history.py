"""Trang Lịch sử duyệt — Figma frame "08 · Lịch sử duyệt"."""

import reflex as rx

from frontend import theme as t
from frontend.components import ui
from frontend.components.header import layout
from frontend.state import State

COLS = [("Thời gian duyệt", "16.2%"), ("Người duyệt", "19%"), ("Mã phiếu", "16.7%"), ("Hành động", "15.9%"), ("Ý kiến", "32.2%")]

ACTIONS = [("ALL", "Tất cả hành động"), ("APPROVE", "Phê duyệt"), ("MODIFY", "Điều chỉnh"), ("REJECT", "Từ chối")]


def history_row(r: rx.Var) -> rx.Component:
    return ui.table_row(
        ui.cell(r["time"], COLS[0][1], font_size="12px", color=t.TEXT),
        ui.cell(r["who"], COLS[1][1], font_size="13px", font_weight="600"),
        ui.cell(
            rx.link(r["code"], href="/proposals/" + r["pid"].to_string(), font_size="13px", font_weight="600", color=t.PRIMARY, underline="none"),
            COLS[2][1],
        ),
        ui.cell(ui.pill(r["label"], tone=r["tone"], border_radius="4px", font_size="11px"), COLS[3][1]),
        ui.cell(r["comment"], COLS[4][1], font_size="12px", color=t.TEXT),
        height="52px",
    )


def explain(title: str, body: str) -> rx.Component:
    return rx.vstack(
        rx.text(title, font_size="15px", font_weight="600", color=t.PRIMARY),
        rx.text(body, font_size="13px", color=t.TEXT, line_height="17px"),
        spacing="0",
        gap="12px",
        align_items="start",
    )


def history_page() -> rx.Component:
    return layout(
        rx.vstack(
            ui.page_title(
                "Lịch sử duyệt",
                "Theo dõi người thực hiện, quyết định và lý do của từng lần phê duyệt.",
                ui.primary_button("Xuất lịch sử", on_click=State.export_history, width="180px", justify_content="flex-start"),
            ),
            rx.grid(
                ui.kpi_card("Đã phê duyệt", ui.pad2(State.history_counts["APPROVE"].to(int)), "Tổng số lần duyệt", inline_hint=True),
                ui.kpi_card("Đã điều chỉnh", ui.pad2(State.history_counts["MODIFY"].to(int)), "Số lượng / nhà cung cấp", inline_hint=True),
                ui.kpi_card("Đã từ chối", ui.pad2(State.history_counts["REJECT"].to(int)), "Đã ghi nhận lý do", inline_hint=True),
                columns=rx.breakpoints(initial="1", md="3"),
                gap="22px",
                width="100%",
                margin_bottom="20px",
            ),
            ui.card(
                rx.text("Nhật ký hoạt động", font_size="16px", font_weight="600", color=t.INK),
                rx.hstack(
                    rx.input(
                        rx.input.slot(rx.icon("search", size=15, color=t.SUBTLE)),
                        placeholder="Tìm mã phiếu hoặc người duyệt...",
                        value=State.history_search,
                        on_change=State.set_history_search,
                        width=["100%", "366px"],
                        height="42px",
                    ),
                    rx.select.root(
                        rx.select.trigger(width="206px", height="42px"),
                        rx.select.content(*[rx.select.item(label, value=v) for v, label in ACTIONS]),
                        value=State.history_action_filter,
                        on_change=State.set_history_action_filter,
                    ),
                    rx.spacer(),
                    rx.box(
                        rx.text(State.history_period, font_size="14px", color=t.INK),
                        height="42px",
                        min_width="238px",
                        padding="0 14px",
                        display="flex",
                        align_items="center",
                        border=f"1px solid {t.BORDER_STRONG}",
                        border_radius=t.RADIUS_SM,
                    ),
                    width="100%",
                    align="center",
                    gap="16px",
                    wrap="wrap",
                    margin_top="17px",
                    margin_bottom="19px",
                ),
                rx.box(
                    rx.box(
                        ui.table_header(COLS),
                        rx.cond(
                            State.history_page_rows.length() > 0,
                            rx.foreach(State.history_page_rows, history_row),
                            ui.empty_state("Chưa có hoạt động phê duyệt phù hợp."),
                        ),
                        min_width="820px",
                    ),
                    overflow_x="auto",
                    width="100%",
                ),
                ui.pagination(State.history_page_label, State.history_page, State.history_total_pages, State.prev_history_page, State.next_history_page),
                padding="18px 20px 14px 20px",
                margin_bottom="20px",
            ),
            ui.card(
                rx.text("Minh bạch ở từng quyết định", font_size="18px", font_weight="600", color=t.INK),
                rx.grid(
                    explain("Ai thực hiện?", "Ghi nhận người duyệt và vai trò được cấp quyền trong hệ thống."),
                    explain("Điều gì thay đổi?", "Lưu hành động, ý kiến và thời điểm duyệt / từ chối / điều chỉnh."),
                    explain("Theo dõi sau phê duyệt", "Đối chiếu với đơn mua hàng và giao dịch nhập kho liên quan."),
                    columns=rx.breakpoints(initial="1", md="3"),
                    gap="37px",
                    width="100%",
                    margin_top="24px",
                ),
                background=t.PRIMARY_TINT,
                padding="18px 22px 28px 22px",
            ),
            spacing="0",
            width="100%",
        ),
        active_page="history",
    )
