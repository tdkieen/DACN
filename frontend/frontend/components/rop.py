"""Khối giao diện dùng chung cho Tuần 7: kế hoạch bổ sung theo ROP."""

import reflex as rx

from frontend import theme as t
from frontend.components import ui
from frontend.state import State


def source_pill() -> rx.Component:
    return rx.cond(
        State.rop_source != "",
        ui.pill(State.rop_source_label, tone=State.rop_source_tone, border_radius="4px", font_size="11px"),
        rx.fragment(),
    )


def create_proposal_button(r: rx.Var, compact: bool = False) -> rx.Component:
    """Nút "Tạo đề xuất" cho dòng thiếu hàng; tự khóa khi đang gửi."""
    busy = State.creating_proposal_id == r["id"]
    return rx.button(
        rx.cond(busy, rx.spinner(size="1"), rx.icon("file-plus-2", size=14)),
        rx.text(rx.cond(busy, "Đang tạo...", "Tạo đề xuất")),
        on_click=State.create_proposal_for(r["id"]),
        disabled=State.creating_proposal_id > 0,
        background=t.PRIMARY,
        color="#FFFFFF",
        height="32px" if compact else "36px",
        padding="0 12px",
        border_radius=t.RADIUS_SM,
        font_size="13px",
        font_weight="600",
        cursor="pointer",
        white_space="nowrap",
        _hover={"background": t.PRIMARY_HOVER},
    )


def stock_bar(r: rx.Var) -> rx.Component:
    """Vạch tồn kho so với ROP (vạch đứng ở giữa = ROP)."""
    return rx.box(
        rx.box(height="100%", width=r["bar_pct"], background=ui._tone_style(r["tone"])[1], border_radius="999px"),
        rx.box(position="absolute", left=r["rop_pct"], top="-3px", height="12px", width="2px", background=t.INK, opacity="0.5"),
        position="relative",
        height="6px",
        width="100%",
        max_width="120px",
        background=t.NEUTRAL_SOFT,
        border_radius="999px",
        margin_top="6px",
    )


def plan_state(content: rx.Component, empty: rx.Component, has_rows: rx.Var) -> rx.Component:
    """Bọc nội dung theo 4 trạng thái: đang tải, lỗi, rỗng, có dữ liệu."""
    return rx.match(
        State.rop_status,
        ("loading", ui.loading_state("Đang tính ROP và nhà cung cấp tối ưu...")),
        ("idle", ui.loading_state("Đang tính ROP và nhà cung cấp tối ưu...")),
        (
            "error",
            ui.error_state(
                "Chưa tải được kế hoạch bổ sung",
                State.rop_error,
                State.load_rop_plan,
                ui.secondary_button("Xem dữ liệu mẫu", icon="eye", on_click=State.use_rop_mock),
            ),
        ),
        rx.cond(has_rows, content, empty),
    )
