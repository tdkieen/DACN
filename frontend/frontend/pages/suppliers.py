"""Trang Nhà cung cấp và báo giá — Figma frame "05 · Nhà cung cấp"."""

import reflex as rx

from frontend import theme as t
from frontend.components import rop, ui
from frontend.components.header import layout
from frontend.state import State

DIR_COLS = [("Nhà cung cấp", "30%"), ("Người liên hệ", "17%"), ("Điện thoại", "14%"), ("Giao hàng", "11%"), ("Uy tín", "10%"), ("Chất lượng", "10%"), ("Báo giá", "8%")]


def quote_filters() -> rx.Component:
    return ui.card(
        rx.hstack(
            rx.vstack(
                ui.field_label("NGUYÊN LIỆU"),
                rx.select.root(
                    rx.select.trigger(placeholder="Chọn nguyên liệu", width="294px", height="40px"),
                    rx.select.content(rx.foreach(State.compare_ingredient_options, lambda o: rx.select.item(o["label"], value=o["value"]))),
                    value=State.compare_ingredient_id,
                    on_change=State.set_compare_ingredient,
                    size="2",
                ),
                spacing="0",
                gap="4px",
                align_items="start",
            ),
            rx.vstack(
                ui.field_label("SỐ LƯỢNG CẦN MUA"),
                rx.input(
                    rx.input.slot(rx.text(State.compare_unit, font_size="13px", color=t.MUTED), side="right"),
                    value=State.compare_qty,
                    on_change=State.set_compare_qty,
                    width="165px",
                    height="40px",
                    size="2",
                ),
                spacing="0",
                gap="4px",
                align_items="start",
            ),
            rx.spacer(),
            rx.text(State.quote_updated, font_size="12px", color=t.MUTED, align_self="center"),
            width="100%",
            align="end",
            gap="28px",
            wrap="wrap",
        ),
        padding="12px 20px",
        margin_bottom="22px",
    )


def supplier_card(c: rx.Var) -> rx.Component:
    return rx.box(
        ui.pill(c["badge"], tone=rx.cond(c["best"], "primary", "yellow"), border_radius="4px", font_size="11px"),
        rx.text(c["name"], font_size="22px", font_weight="600", color=t.INK, line_height="29px", margin_top="20px"),
        rx.text(c["sub"], font_size="12px", color=t.MUTED, margin_top="4px"),
        rx.text(c["price"], font_size="32px", font_weight="600", color=t.INK, line_height="44px", margin_top="15px"),
        ui.divider(margin="9px 0 18px 0"),
        rx.vstack(
            ui.info_row("Thời gian giao hàng", c["lead"]),
            ui.info_row("Số lượng tối thiểu", c["moq"]),
            ui.info_row("Điểm uy tín", c["rating"]),
            ui.info_row("Điểm MCDM", c["score"].to(str) + " / 100"),
            ui.info_row("Tổng tiền dự kiến", c["total"], color=t.PRIMARY),
            spacing="0",
            gap="19px",
            width="100%",
        ),
        rx.cond(c["moq_note"] != "", rx.text(c["moq_note"], font_size="11px", color=t.WARNING, margin_top="10px"), rx.fragment()),
        background=t.SURFACE,
        border=rx.cond(c["best"], f"2px solid {t.PRIMARY}", f"1px solid {t.BORDER}"),
        border_radius=t.RADIUS,
        padding="19px 20px 24px 20px",
        min_height="369px",
        width="100%",
    )


def comparison_tab() -> rx.Component:
    r = State.compare_rationale
    return rx.vstack(
        quote_filters(),
        rx.cond(
            State.compare_cards.length() > 0,
            rx.grid(
                rx.foreach(State.compare_cards, supplier_card),
                columns=rx.breakpoints(initial="1", md="2", lg="3"),
                gap="22px",
                width="100%",
                margin_bottom="22px",
            ),
            ui.card(ui.empty_state("Chưa có báo giá cho nguyên liệu này."), margin_bottom="22px"),
        ),
        ui.card(
            rx.text(r["title"], font_size="16px", font_weight="600", color=t.INK),
            rx.text(r["line1"], font_size="13px", color=t.TEXT, margin_top="13px"),
            rx.text(r["line2"], font_size="13px", font_weight="600", color=t.PRIMARY, margin_top="11px"),
            background=t.PRIMARY_TINT,
            padding="18px 22px",
            margin_bottom="20px",
        ),
        ui.guardrail(
            "Lựa chọn nhà cung cấp chưa tạo đơn mua hàng.",
            "Nhà cung cấp chỉ nhận đơn sau khi quản lý phê duyệt đề xuất.",
            rx.link(ui.primary_button("Xem đề xuất  →", width="180px", justify_content="flex-start", white_space="pre"), href="/proposals"),
            background=t.SURFACE,
            border=f"1px solid {t.BORDER}",
        ),
        spacing="0",
        width="100%",
    )


def _chip(icon: str, text) -> rx.Component:
    return rx.hstack(
        rx.icon(icon, size=13, color=t.MUTED),
        rx.text(text, font_size="12px", color=t.TEXT, white_space="nowrap"),
        align="center",
        gap="5px",
        spacing="0",
        padding="3px 8px",
        border=f"1px solid {t.BORDER}",
        border_radius="6px",
        background=t.SURFACE_MUTED,
    )


def selected_row(r: rx.Var) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.vstack(
                rx.hstack(
                    rx.text(r["ten"], font_size="15px", font_weight="600", color=t.INK),
                    ui.pill(r["status"], tone=r["tone"], border_radius="4px", font_size="11px", height="22px"),
                    align="center",
                    gap="8px",
                    spacing="0",
                    wrap="wrap",
                ),
                rx.text(r["stock_line"], font_size="12px", color=t.MUTED, white_space="pre-wrap"),
                spacing="0",
                gap="6px",
                align_items="start",
                flex="1 1 260px",
                min_width="0",
            ),
            rx.vstack(
                ui.eyebrow("NHÀ CUNG CẤP ĐƯỢC CHỌN", font_size="10px"),
                rx.text(r["ncc"], font_size="14px", font_weight="600", color=rx.cond(r["has_ncc"], t.INK, t.WARNING)),
                rx.cond(
                    r["has_ncc"],
                    rx.flex(
                        _chip("award", r["ncc_score_label"]),
                        _chip("tag", r["ncc_price"]),
                        _chip("truck", r["ncc_lead"]),
                        _chip("package", r["ncc_moq_label"]),
                        wrap="wrap",
                        gap="6px",
                    ),
                    rx.fragment(),
                ),
                spacing="0",
                gap="6px",
                align_items="start",
                flex="1 1 320px",
                min_width="0",
            ),
            rx.vstack(
                ui.eyebrow("TỔNG DỰ KIẾN", font_size="10px"),
                rx.text(r["total"], font_size="18px", font_weight="700", color=t.PRIMARY),
                rop.create_proposal_button(r),
                spacing="0",
                gap="8px",
                align_items=rx.breakpoints(initial="start", md="end"),
                flex="0 0 auto",
            ),
            width="100%",
            gap="20px",
            wrap="wrap",
            align="start",
        ),
        rx.hstack(
            rx.icon("sparkles", size=14, color=t.PRIMARY, flex_shrink="0", margin_top="2px"),
            rx.vstack(
                rx.text(rx.text.strong("Lý do chọn: "), r["reason"], font_size="13px", color=t.TEXT),
                rx.cond(
                    r["has_ncc"],
                    ui.text_link(
                        "So sánh chi tiết các nhà cung cấp  →",
                        on_click=State.open_compare_for(r["id"]),
                        font_size="12px",
                        white_space="pre",
                    ),
                    rx.fragment(),
                ),
                spacing="0",
                gap="6px",
                align_items="start",
            ),
            align="start",
            gap="8px",
            spacing="0",
            margin_top="14px",
            padding="10px 12px",
            border_radius=t.RADIUS_SM,
            background=t.PRIMARY_TINT,
            width="100%",
        ),
        background=t.SURFACE,
        border=f"1px solid {t.BORDER}",
        border_left=rx.cond(r["tone"] == "danger", f"3px solid {t.DANGER}", f"1px solid {t.BORDER}"),
        border_radius=t.RADIUS,
        padding="16px 20px",
        width="100%",
    )


def selected_tab() -> rx.Component:
    content = rx.vstack(rx.foreach(State.rop_selected_rows, selected_row), width="100%", spacing="0", gap="14px")
    return rx.vstack(
        ui.card(
            rx.hstack(
                rx.vstack(
                    rx.text("Nhà cung cấp được chọn cho từng nguyên liệu cần đặt", font_size="16px", font_weight="600", color=t.INK),
                    rx.text(
                        State.rop_need_count.to_string() + " nguyên liệu dưới ROP  ·  "
                        + State.rop_supplier_count.to_string() + " nhà cung cấp  ·  Tổng dự kiến " + State.rop_total_fmt,
                        font_size="13px",
                        color=t.MUTED,
                        white_space="pre",
                    ),
                    spacing="0",
                    gap="6px",
                    align_items="start",
                ),
                rx.spacer(),
                rop.source_pill(),
                width="100%",
                align="center",
                gap="12px",
                wrap="wrap",
            ),
            padding="14px 20px",
            margin_bottom="16px",
        ),
        rop.plan_state(
            content,
            ui.card(ui.empty_state("Không có nguyên liệu nào dưới ROP nên chưa cần chọn nhà cung cấp.", "circle-check")),
            State.rop_selected_rows.length() > 0,
        ),
        ui.guardrail(
            "Tạo đề xuất chưa phải là đặt hàng.",
            "AI chọn nhà cung cấp theo điểm MCDM (giá 40%, thời gian giao 30%, chất lượng 15%, uy tín 15%). Quản lý có thể đổi khi duyệt phiếu.",
            background=t.SURFACE,
            border=f"1px solid {t.BORDER}",
            margin_top="20px",
        ),
        spacing="0",
        width="100%",
    )


def directory_row(s: rx.Var) -> rx.Component:
    return ui.table_row(
        ui.cell(
            rx.vstack(
                rx.text(s["name"], font_size="14px", font_weight="600", color=t.INK),
                rx.text(s["address"], font_size="11px", color=t.MUTED),
                spacing="0",
                gap="2px",
                align_items="start",
            ),
            DIR_COLS[0][1],
            padding_right="12px",
        ),
        ui.cell(s["contact"], DIR_COLS[1][1], font_size="13px", color=t.TEXT),
        ui.cell(s["phone"], DIR_COLS[2][1], font_size="13px", color=t.TEXT),
        ui.cell(s["lead"], DIR_COLS[3][1], font_size="13px", color=t.TEXT),
        ui.cell(s["rating"], DIR_COLS[4][1], font_size="13px", color=t.TEXT),
        ui.cell(s["quality"], DIR_COLS[5][1], font_size="13px", color=t.TEXT),
        ui.cell(s["n_quotes"], DIR_COLS[6][1], font_size="13px", color=t.PRIMARY),
        height="60px",
    )


def directory_tab() -> rx.Component:
    return ui.card(
        rx.box(
            rx.box(
                ui.table_header(DIR_COLS),
                rx.cond(State.supplier_rows.length() > 0, rx.foreach(State.supplier_rows, directory_row), ui.empty_state("Chưa có nhà cung cấp.")),
                min_width="860px",
            ),
            overflow_x="auto",
            width="100%",
        ),
    )


def field(label: str, key: str, placeholder: str = "") -> rx.Component:
    return rx.vstack(
        rx.text(label, font_size="13px", font_weight="500", color=t.INK),
        rx.input(value=State.supplier_form[key], on_change=lambda v: State.set_supplier_field(key, v), placeholder=placeholder, width="100%"),
        spacing="1",
        width="100%",
    )


def supplier_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Thêm nhà cung cấp"),
            rx.vstack(
                field("Tên nhà cung cấp", "ten_nha_cung_cap"),
                rx.grid(field("Người liên hệ", "nguoi_lien_he"), field("Số điện thoại", "sdt"), columns="2", gap="12px", width="100%"),
                field("Email", "email"),
                field("Địa chỉ", "dia_chi"),
                rx.grid(field("Thời gian giao (ngày)", "thoi_gian_giao_du_kien"), field("Điểm uy tín (1–5)", "diem_uy_tin"), columns="2", gap="12px", width="100%"),
                spacing="3",
                width="100%",
                margin_top="12px",
            ),
            rx.hstack(
                rx.dialog.close(ui.secondary_button("Hủy")),
                ui.primary_button("Lưu nhà cung cấp", on_click=State.save_supplier),
                justify="end",
                width="100%",
                margin_top="20px",
                gap="10px",
            ),
            max_width="520px",
        ),
        open=State.supplier_dialog_open,
        on_open_change=State.set_supplier_dialog_open,
    )


def suppliers_page() -> rx.Component:
    return layout(
        rx.vstack(
            ui.page_title(
                "Nhà cung cấp và báo giá",
                "So sánh giá, MOQ và thời gian giao hàng trước khi chọn nhà cung cấp.",
                ui.primary_button("+  Thêm nhà cung cấp", on_click=State.open_supplier_dialog, width="180px", justify_content="flex-start", white_space="pre"),
            ),
            ui.underline_tabs(
                [("lua-chon", "NCC được chọn"), ("so-sanh", "So sánh báo giá"), ("danh-ba", "Danh bạ nhà cung cấp")],
                State.active_tab_suppliers,
                State.set_suppliers_tab,
                margin_bottom="22px",
            ),
            rx.match(
                State.active_tab_suppliers,
                ("danh-ba", directory_tab()),
                ("lua-chon", selected_tab()),
                comparison_tab(),
            ),
            supplier_dialog(),
            spacing="0",
            width="100%",
        ),
        active_page="suppliers",
    )
