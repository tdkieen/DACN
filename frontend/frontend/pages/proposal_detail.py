"""Trang Chi tiết đề xuất — Figma frame "07 · Chi tiết đề xuất"."""

import reflex as rx

from frontend import theme as t
from frontend.components import ui
from frontend.components.header import layout
from frontend.state import State

LINE_COLS = [("Nguyên liệu / Nhà cung cấp", "47%"), ("Số lượng", "16%"), ("Đơn giá", "18%"), ("Thành tiền", "19%")]

P = State.current_proposal


def workflow_status() -> rx.Component:
    done = P["status"] != "CHO_DUYET"
    approved = P["status"] == "DA_DUYET"
    return ui.card(
        rx.hstack(
            rx.text("✓  AI đã phân tích", font_size="13px", font_weight="600", color=t.PRIMARY, white_space="pre"),
            rx.text("→", color=t.SUBTLE),
            rx.text(
                rx.cond(done, "✓  Quản lý thẩm định", "02  Quản lý thẩm định"),
                font_size="13px",
                font_weight="600",
                color=rx.cond(done, t.PRIMARY, t.INK),
                white_space="pre",
            ),
            rx.text("→", color=t.SUBTLE),
            rx.text(
                rx.cond(approved, "✓  Đã tạo đơn sau khi duyệt", "03  Tạo đơn sau khi duyệt"),
                font_size="13px",
                font_weight="500",
                color=rx.cond(approved, t.PRIMARY, t.MUTED),
                white_space="pre",
            ),
            width="100%",
            justify="between",
            align="center",
            wrap="wrap",
            gap="12px",
        ),
        padding="15px 20px",
        margin_bottom="20px",
    )


def ai_explanation() -> rx.Component:
    return ui.card(
        ui.eyebrow_pill("GIẢI TRÌNH CỦA AI"),
        rx.text("Bổ sung " + P["summary"].to(str) + " cho 7 ngày tới", font_size="18px", font_weight="600", color=t.INK, margin_top="14px"),
        rx.text(P["reason"], font_size="13px", color=t.TEXT, margin_top="10px", line_height="17px"),
        rx.vstack(
            rx.foreach(State.current_reasons, lambda r: rx.text("• " + r, font_size="13px", color=t.TEXT, line_height="17px")),
            spacing="0",
            gap="6px",
            align_items="start",
            margin_top="14px",
        ),
        background=t.PRIMARY_TINT,
        padding="17px 20px 20px 20px",
        min_height="207px",
    )


def line_row(l: rx.Var) -> rx.Component:
    return ui.table_row(
        ui.cell(
            rx.vstack(
                rx.text(l["ten"], font_size="14px", font_weight="600", color=t.INK),
                rx.text(l["ncc"], font_size="12px", color=t.MUTED),
                spacing="0",
                gap="6px",
                align_items="start",
            ),
            LINE_COLS[0][1],
            padding_right="12px",
        ),
        ui.cell(l["so_luong"], LINE_COLS[1][1]),
        ui.cell(l["don_gia"], LINE_COLS[2][1]),
        ui.cell(l["thanh_tien"], LINE_COLS[3][1], font_weight="600"),
        height="71px",
        padding_x="0",
        _hover={},
    )


def line_items() -> rx.Component:
    return ui.card(
        rx.hstack(
            rx.text("Chi tiết nguyên liệu", font_size="16px", font_weight="600", color=t.INK),
            rx.spacer(),
            rx.cond(
                State.current_is_pending & State.can_approve,
                ui.text_link("Chỉnh sửa số lượng", on_click=rx.set_focus("manager-comment"), font_size="12px"),
                rx.fragment(),
            ),
            width="100%",
            align="center",
        ),
        rx.box(
            rx.box(
                rx.hstack(
                    *[rx.text(n, width=w, font_size="12px", font_weight="500", color=t.MUTED) for n, w in LINE_COLS],
                    width="100%",
                    padding_bottom="12px",
                    border_bottom=f"1px solid {t.BORDER}",
                    spacing="0",
                ),
                rx.foreach(State.current_lines, line_row),
                min_width="560px",
            ),
            overflow_x="auto",
            width="100%",
            margin_top="19px",
        ),
        padding="17px 20px 10px 20px",
        min_height="235px",
    )


def manager_feedback() -> rx.Component:
    return ui.card(
        rx.text("Ý kiến của quản lý", font_size="14px", font_weight="600", color=t.INK),
        rx.cond(
            State.current_is_pending & State.can_approve,
            rx.text_area(
                id="manager-comment",
                placeholder="Nhập ghi chú hoặc lý do điều chỉnh / từ chối...",
                value=State.proposal_comment,
                on_change=State.set_proposal_comment,
                width="100%",
                min_height="61px",
                margin_top="12px",
            ),
            rx.vstack(
                rx.cond(
                    State.current_history.length() > 0,
                    rx.foreach(
                        State.current_history,
                        lambda h: rx.hstack(
                            ui.pill(h["label"], tone=h["tone"], border_radius="4px", font_size="11px"),
                            rx.vstack(
                                rx.text(h["comment"], font_size="13px", color=t.INK),
                                rx.text(h["who"].to(str) + " · " + h["time"].to(str), font_size="11px", color=t.MUTED),
                                spacing="0",
                                gap="2px",
                                align_items="start",
                            ),
                            align="start",
                            gap="10px",
                        ),
                    ),
                    rx.text(
                        rx.cond(State.can_approve, "Chưa có ý kiến.", "Phiếu đang chờ Quản lý cửa hàng phê duyệt. Tài khoản của bạn chỉ có quyền xem."),
                        font_size="13px",
                        color=t.MUTED,
                    ),
                ),
                spacing="3",
                width="100%",
                margin_top="12px",
            ),
        ),
        padding="14px 20px 18px 20px",
        min_height="124px",
    )


def order_summary() -> rx.Component:
    return ui.card(
        rx.text("Tổng quan đề xuất", font_size="16px", font_weight="600", color=t.INK),
        rx.box(ui.info_row("Tạm tính · " + P["n_items"].to_string() + " nguyên liệu", P["total_fmt"]), width="100%", margin_top="25px"),
        ui.divider(margin="20px 0 22px 0"),
        ui.eyebrow("TỔNG TIỀN DỰ KIẾN"),
        rx.text(P["total_fmt"], font_size="34px", font_weight="600", color=t.INK, line_height="45px", margin_top="10px"),
        rx.text("Giá theo báo giá mới nhất của nhà cung cấp.", font_size="12px", color=t.MUTED, margin_top="10px"),
        rx.text("Chưa bao gồm phí phát sinh (nếu có).", font_size="12px", color=t.MUTED, margin_top="6px"),
        padding="19px 22px",
        min_height="278px",
    )


def checks() -> rx.Component:
    return ui.card(
        rx.text("Kiểm tra trước phê duyệt", font_size="16px", font_weight="600", color=t.INK),
        rx.vstack(
            rx.text("✓  Đáp ứng MOQ nhà cung cấp", font_size="13px", color=t.PRIMARY, white_space="pre"),
            rx.text("✓  Đã tính hàng đang về", font_size="13px", color=t.PRIMARY, white_space="pre"),
            rx.text("✓  Duy trì mức tồn an toàn", font_size="13px", color=t.PRIMARY, white_space="pre"),
            spacing="0",
            gap="12px",
            align_items="start",
            margin_top="18px",
        ),
        padding="18px 22px",
        min_height="158px",
    )


def hitl_notice() -> rx.Component:
    return rx.box(
        rx.text(
            rx.match(
                P["status"],
                ("CHO_DUYET", "Đang chờ quyết định của bạn"),
                ("DA_DUYET", "Đề xuất đã được phê duyệt"),
                ("TU_CHOI", "Đề xuất đã bị từ chối"),
                ("DA_SUA", "Đề xuất cần điều chỉnh"),
                "Trạng thái đề xuất",
            ),
            font_size="15px",
            font_weight="600",
            color=t.INK,
        ),
        rx.text(
            "AI không tự gửi đơn hàng. Duyệt sẽ tạo đơn mua hàng và lưu lịch sử phê duyệt. Tồn kho cập nhật khi ghi nhận nhập hàng.",
            font_size="12px",
            color=t.TEXT,
            line_height="16px",
            margin_top="14px",
        ),
        background="#FFF8E6",
        border="1px solid #F6E3B5",
        border_radius=t.RADIUS,
        padding="17px 20px",
        min_height="130px",
        width="100%",
    )


def approval_actions() -> rx.Component:
    return ui.card(
        rx.hstack(
            rx.vstack(
                rx.text("Quyết định thuộc về quản lý", font_size="15px", font_weight="600", color=t.INK),
                rx.text("Mọi thao tác đều được lưu vết.", font_size="12px", color=t.MUTED),
                spacing="0",
                gap="9px",
                align_items="start",
            ),
            rx.spacer(),
            rx.cond(
                State.current_is_pending & State.can_approve,
                rx.hstack(
                    ui.secondary_button("Từ chối", color=t.DANGER, width="120px", justify_content="flex-start", on_click=State.handle_proposal_action("REJECT"), disabled=State.acting),
                    ui.secondary_button("Chỉnh sửa số lượng", width="190px", justify_content="flex-start", on_click=State.handle_proposal_action("MODIFY"), disabled=State.acting),
                    ui.primary_button("Duyệt đề xuất  →", width="192px", justify_content="flex-start", white_space="pre", on_click=State.handle_proposal_action("APPROVE"), disabled=State.acting),
                    gap="12px",
                    wrap="wrap",
                ),
                ui.pill(P["status_label"].to(str), tone=P["tone"], border_radius="4px"),
            ),
            width="100%",
            align="center",
            wrap="wrap",
            gap="12px",
        ),
        padding="15px 20px",
    )


def proposal_detail_page() -> rx.Component:
    return layout(
        rx.cond(
            P.contains("id"),
            rx.vstack(
                ui.text_link("←  Đề xuất mua hàng", href="/proposals", color=t.MUTED, font_size="12px", font_weight="500", white_space="pre"),
                rx.hstack(
                    rx.hstack(
                        rx.text("Phiếu " + P["code"].to(str), font_size="30px", font_weight="600", color=t.INK, line_height="39px"),
                        ui.pill(P["status_label"].to(str), tone=P["tone"], border_radius="4px", font_size="11px"),
                        align="center",
                        gap="16px",
                        spacing="0",
                    ),
                    rx.spacer(),
                    ui.secondary_button("Xuất phiếu", on_click=State.export_current_proposal, width="130px", justify_content="flex-start"),
                    width="100%",
                    align="center",
                    margin_top="14px",
                    wrap="wrap",
                ),
                rx.text(State.current_meta, font_size="12px", color=t.MUTED, margin_top="6px", margin_bottom="19px", white_space="pre-wrap"),
                workflow_status(),
                rx.grid(
                    rx.vstack(ai_explanation(), line_items(), manager_feedback(), spacing="0", gap="20px", width="100%"),
                    rx.vstack(order_summary(), checks(), hitl_notice(), spacing="0", gap="20px", width="100%"),
                    grid_template_columns=rx.breakpoints(initial="1fr", lg="744fr 384fr"),
                    gap="20px",
                    width="100%",
                    margin_bottom="20px",
                ),
                approval_actions(),
                spacing="0",
                width="100%",
                align_items="start",
            ),
            rx.center(rx.spinner(size="3"), width="100%", padding="80px"),
        ),
        active_page="proposals",
    )
