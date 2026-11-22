"""Trang Quản lý kho — Figma frame "04 · Quản lý kho"."""

import reflex as rx

from frontend import theme as t
from frontend.components import ui
from frontend.components.header import layout
from frontend.state import CATEGORY_PRESETS, UNIT_PRESETS, State

ING_COLS = [("Nguyên liệu", "27%"), ("Đơn vị", "9.5%"), ("Tồn hiện tại", "15%"), ("An toàn", "12.3%"), ("Trạng thái", "20.6%"), ("Thao tác", "15.6%")]
BATCH_COLS = [("Nguyên liệu", "30%"), ("Mã lô NCC", "18%"), ("Nhập / Còn lại", "14%"), ("Ngày nhập", "12%"), ("Hạn sử dụng", "12%"), ("Tình trạng HSD", "14%")]
TX_COLS = [("Tham chiếu", "18%"), ("Nguyên liệu", "28%"), ("Loại", "16%"), ("Số lượng", "14%"), ("Ghi chú", "24%")]
RECENT_COLS = [("Tham chiếu", "23%"), ("Nguyên liệu", "33%"), ("Loại", "25%"), ("Số lượng", "19%")]

STATUS_OPTIONS = [
    ("ALL", "Tất cả trạng thái"),
    ("NGUY_CO_THIEU", "Thiếu hàng"),
    ("CHAM_NGUONG", "Chạm ngưỡng"),
    ("AN_TOAN", "Đủ hàng"),
    ("TON_DU", "Tồn dư"),
]

TX_TYPES = [("NHAP", "Nhập kho"), ("XUAT_BAN", "Xuất bán"), ("HAO_HUT", "Hao hụt"), ("KIEM_KE", "Kiểm kê")]


def ingredient_row(r: rx.Var) -> rx.Component:
    return ui.table_row(
        ui.cell(
            rx.vstack(
                rx.text(r["ten_nguyen_lieu"], font_size="14px", font_weight="600", color=t.INK),
                rx.text("#" + r["ma"].to(str) + " · Dự báo 7 ngày: " + r["du_bao_fmt"].to(str) + " · ROP: " + r["rop_fmt"].to(str), font_size="11px", color=t.MUTED),
                spacing="0",
                gap="2px",
                align_items="start",
            ),
            ING_COLS[0][1],
            padding_right="12px",
        ),
        ui.cell(r["don_vi_tinh"], ING_COLS[1][1], color=t.TEXT),
        ui.cell(r["ton_fmt"], ING_COLS[2][1], font_weight="600"),
        ui.cell(r["an_toan_fmt"], ING_COLS[3][1], color=t.TEXT),
        ui.cell(ui.pill(r["status_label"], tone=r["tone"], border_radius="4px"), ING_COLS[4][1]),
        ui.cell(
            rx.hstack(
                rx.text("Sửa", color=t.PRIMARY, cursor="pointer", on_click=State.open_edit_ingredient(r["ma_nguyen_lieu"])),
                rx.text("·", color=t.SUBTLE),
                rx.text("Xóa", color=t.DANGER, cursor="pointer", on_click=State.ask_delete_ingredient(r["ma_nguyen_lieu"], r["ten_nguyen_lieu"])),
                font_size="14px",
                gap="10px",
                spacing="0",
            ),
            ING_COLS[5][1],
        ),
    )


def ingredient_panel() -> rx.Component:
    return ui.card(
        rx.hstack(
            rx.input(
                rx.input.slot(rx.icon("search", size=16, color=t.SUBTLE)),
                placeholder="Tìm tên hoặc mã nguyên liệu...",
                value=State.ingredient_search,
                on_change=State.set_ingredient_search,
                width=["100%", "394px"],
                height="40px",
                size="2",
            ),
            rx.select.root(
                rx.select.trigger(width="190px", height="40px"),
                rx.select.content(*[rx.select.item(label, value=value) for value, label in STATUS_OPTIONS]),
                value=State.ingredient_status_filter,
                on_change=State.set_status_filter,
                size="2",
            ),
            rx.spacer(),
            ui.secondary_button("Nhập / xuất kho", on_click=State.open_tx_dialog, width="210px", justify_content="flex-start"),
            width="100%",
            align="center",
            gap="16px",
            wrap="wrap",
            margin_bottom="21px",
        ),
        rx.box(
            rx.box(
                ui.table_header(ING_COLS),
                rx.cond(
                    State.ingredient_page_rows.length() > 0,
                    rx.foreach(State.ingredient_page_rows, ingredient_row),
                    ui.empty_state("Không có nguyên liệu phù hợp bộ lọc."),
                ),
                min_width="760px",
            ),
            overflow_x="auto",
            width="100%",
        ),
        ui.pagination(State.ingredient_page_label, State.ingredient_page, State.ingredient_total_pages, State.prev_ingredient_page, State.next_ingredient_page),
        padding="19px 20px 14px 20px",
        margin_bottom="20px",
    )


def batch_row(b: rx.Var) -> rx.Component:
    return ui.table_row(
        ui.cell(b["ten"], BATCH_COLS[0][1], font_weight="600", padding_right="12px"),
        ui.cell(b["ma_lo"], BATCH_COLS[1][1], color=t.TEXT, font_size="13px"),
        ui.cell(b["nhap_con"], BATCH_COLS[2][1], color=t.TEXT),
        ui.cell(b["ngay_nhap"], BATCH_COLS[3][1], color=t.TEXT),
        ui.cell(b["han"], BATCH_COLS[4][1], color=t.TEXT),
        ui.cell(
            rx.vstack(ui.pill(b["label"], tone=b["tone"], border_radius="4px"), rx.text(b["con_han"], font_size="11px", color=t.MUTED), spacing="0", gap="3px"),
            BATCH_COLS[5][1],
        ),
        height="60px",
    )


def batch_panel() -> rx.Component:
    return ui.card(
        rx.hstack(
            rx.checkbox(
                "Chỉ hiển thị lô sắp hết hạn hoặc đã quá hạn",
                checked=State.only_expiring_batches,
                on_change=State.toggle_expiring_batches,
                size="2",
            ),
            rx.spacer(),
            ui.pill(State.batch_rows.length().to_string() + " lô hàng", tone="neutral", border_radius="4px"),
            width="100%",
            align="center",
            margin_bottom="18px",
        ),
        rx.box(
            rx.box(
                ui.table_header(BATCH_COLS),
                rx.cond(State.batch_rows.length() > 0, rx.foreach(State.batch_rows, batch_row), ui.empty_state("Không có lô hàng.")),
                min_width="760px",
            ),
            overflow_x="auto",
            width="100%",
        ),
        margin_bottom="20px",
    )


def tx_row(r: rx.Var, cols) -> rx.Component:
    cells = [
        ui.cell(r["ref"], cols[0][1], font_size="13px", color=t.TEXT),
        ui.cell(r["ten"], cols[1][1], font_size="13px", padding_right="12px"),
        ui.cell(r["loai"], cols[2][1], font_size="13px", color=t.TEXT),
        ui.cell(r["so_luong"], cols[3][1], font_size="13px", font_weight="600", color=rx.cond(r["positive"], t.SUCCESS, t.INK)),
    ]
    if len(cols) > 4:
        cells.append(ui.cell(r["ghi_chu"], cols[4][1], font_size="12px", color=t.MUTED))
    return ui.table_row(*cells, height="39px")


def transaction_panel() -> rx.Component:
    return ui.card(
        rx.box(
            rx.box(
                ui.table_header(TX_COLS),
                rx.cond(
                    State.transaction_rows.length() > 0,
                    rx.foreach(State.transaction_rows, lambda r: tx_row(r, TX_COLS)),
                    ui.empty_state("Chưa có giao dịch kho."),
                ),
                min_width="760px",
            ),
            overflow_x="auto",
            width="100%",
            max_height="560px",
            overflow_y="auto",
        ),
        margin_bottom="20px",
    )


def recent_transactions() -> rx.Component:
    return ui.card(
        rx.hstack(
            rx.text("Giao dịch gần đây", font_size="16px", font_weight="600", color=t.INK),
            rx.spacer(),
            ui.text_link("Xem tất cả  →", on_click=State.set_inventory_tab("giao-dich"), font_size="12px"),
            width="100%",
            align="center",
            margin_bottom="18px",
        ),
        rx.box(
            rx.box(
                ui.table_header(RECENT_COLS),
                rx.foreach(State.recent_transaction_rows, lambda r: tx_row(r, RECENT_COLS)),
                min_width="560px",
            ),
            overflow_x="auto",
            width="100%",
        ),
        padding="17px 20px 10px 20px",
        min_height="228px",
    )


def expiry_watch() -> rx.Component:
    w = State.expiry_watch
    return rx.box(
        rx.text("Theo dõi hạn sử dụng", font_size="16px", font_weight="600", color=t.INK),
        ui.pill(
            rx.cond(w["count"].to(int) > 0, w["count"].to_string() + " lô cần ưu tiên", "Không có lô cần ưu tiên"),
            tone=rx.cond(w["count"].to(int) > 0, "warning", "success"),
            border_radius="4px",
            margin_top="12px",
        ),
        rx.text(w["title"], font_size="15px", font_weight="600", color=t.INK, margin_top="20px"),
        rx.text(w["detail"], font_size="13px", color=t.TEXT, margin_top="9px", white_space="pre"),
        rx.text("Ưu tiên xuất lô gần hết hạn trước.", font_size="13px", color=t.WARNING, margin_top="16px"),
        ui.text_link("Xem chi tiết lô hàng  →", on_click=State.set_inventory_tab("lo-hang"), margin_top="17px", display="block"),
        background="#FFF8E6",
        border="1px solid #F6E3B5",
        border_radius=t.RADIUS,
        padding="18px 20px",
        min_height="228px",
        width="100%",
    )


def num_field(label, field: str, disabled: rx.Var | bool = False) -> rx.Component:
    return rx.vstack(
        rx.text(label, font_size="13px", font_weight="500", color=t.INK),
        rx.input(
            value=State.ing_form[field],
            on_change=lambda v: State.set_ing_field(field, v),
            disabled=disabled,
            width="100%",
        ),
        spacing="1",
        width="100%",
    )


def _quick_chip(label, on_click, tone: str | rx.Var = "primary") -> rx.Component:
    bg = rx.cond(tone == "danger", t.DANGER_SOFT, rx.cond(tone == "warning", t.WARNING_SOFT, t.PRIMARY_SOFT)) if not isinstance(tone, str) else t.TONES.get(tone, t.TONES["primary"])[0]
    fg = rx.cond(tone == "danger", t.DANGER, rx.cond(tone == "warning", t.WARNING, t.PRIMARY)) if not isinstance(tone, str) else t.TONES.get(tone, t.TONES["primary"])[1]
    bd = rx.cond(tone == "danger", t.DANGER_BORDER, rx.cond(tone == "warning", t.WARNING_BORDER, "#C9DCF0")) if not isinstance(tone, str) else t.TONES.get(tone, t.TONES["primary"])[2]
    return rx.box(
        rx.text(label, font_size="12px", font_weight="500", line_height="1.2"),
        on_click=on_click,
        background=bg,
        color=fg,
        border="1px solid",
        border_color=bd,
        border_radius="999px",
        padding="4px 10px",
        cursor="pointer",
        _hover={"opacity": "0.85"},
    )


def _mini_preset_chip(label: str, field: str) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="11px", font_weight="500"),
        on_click=State.set_ing_field(field, label),
        background=t.SURFACE_MUTED,
        color=t.TEXT,
        border=f"1px solid {t.BORDER}",
        border_radius="6px",
        padding="2px 7px",
        cursor="pointer",
        _hover={"background": t.PRIMARY_SOFT, "color": t.PRIMARY, "border_color": t.PRIMARY},
    )


def ingredient_dialog() -> rx.Component:
    is_restock = (State.ing_restock_id > 0) & (State.ing_edit_id == 0)
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.cond(
                    State.ing_edit_id > 0,
                    "Sửa nguyên liệu",
                    rx.cond(State.ing_restock_id > 0, "Nhập thêm hàng vào kho", "Thêm nguyên liệu"),
                )
            ),
            rx.dialog.description(
                "Chọn nhanh từ danh sách đề xuất bên dưới để nhập thêm hàng hoặc thêm nguyên liệu mới mà không cần gõ từng chữ.",
                font_size="13px",
                color=t.MUTED,
                margin_bottom="12px",
            ),
            rx.vstack(
                # Khu vực chọn nhanh đề xuất (chỉ hiện khi thêm / nhập thêm)
                rx.cond(
                    State.ing_edit_id == 0,
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("sparkles", size=14, color=t.PRIMARY),
                                rx.text("Chọn nhanh từ đề xuất có sẵn", font_size="12px", font_weight="600", color=t.INK),
                                rx.spacer(),
                                rx.cond(
                                    State.ing_restock_id > 0,
                                    rx.text(
                                        "Đổi sang tạo mới",
                                        font_size="12px",
                                        font_weight="600",
                                        color=t.PRIMARY,
                                        cursor="pointer",
                                        on_click=State.clear_ing_restock_mode,
                                    ),
                                    rx.fragment(),
                                ),
                                width="100%",
                                align="center",
                            ),
                            rx.select.root(
                                rx.select.trigger(
                                    placeholder="Chọn nguyên liệu cần nhập thêm hoặc mẫu mới...",
                                    width="100%",
                                ),
                                rx.select.content(
                                    rx.foreach(
                                        State.ingredient_suggestion_options,
                                        lambda o: rx.select.item(o["label"], value=o["value"]),
                                    )
                                ),
                                value=State.ing_preset_selected,
                                on_change=State.apply_ingredient_suggestion,
                                size="2",
                            ),
                            rx.cond(
                                State.restock_quick_chips.length() > 0,
                                rx.vstack(
                                    rx.text("Gợi ý nhập thêm nhanh (ưu tiên hàng sắp thiếu):", font_size="11px", color=t.MUTED, font_weight="500"),
                                    rx.flex(
                                        rx.foreach(
                                            State.restock_quick_chips,
                                            lambda c: _quick_chip(
                                                c["label"],
                                                State.apply_ingredient_suggestion(c["key"]),
                                                tone=c["tone"],
                                            ),
                                        ),
                                        wrap="wrap",
                                        gap="6px",
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),
                                rx.fragment(),
                            ),
                            rx.cond(
                                State.new_preset_chips.length() > 0,
                                rx.vstack(
                                    rx.text("Hoặc chọn nhanh mẫu nguyên liệu mới:", font_size="11px", color=t.MUTED, font_weight="500"),
                                    rx.flex(
                                        rx.foreach(
                                            State.new_preset_chips,
                                            lambda c: _quick_chip(
                                                c["label"],
                                                State.apply_ingredient_suggestion(c["key"]),
                                                tone="neutral",
                                            ),
                                        ),
                                        wrap="wrap",
                                        gap="6px",
                                        width="100%",
                                    ),
                                    spacing="1",
                                    width="100%",
                                ),
                                rx.fragment(),
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        background=t.PRIMARY_TINT,
                        border=f"1px solid {t.BORDER_STRONG}",
                        border_radius=t.RADIUS_SM,
                        padding="12px",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    is_restock,
                    rx.box(
                        rx.text(
                            "Đang chọn nguyên liệu có sẵn: hệ thống sẽ cộng dồn số lượng nhập thêm vào tồn kho hiện tại và ghi lịch sử Nhập kho (không tạo trùng).",
                            font_size="12px",
                            color=t.INFO,
                            font_weight="500",
                        ),
                        background=t.INFO_SOFT,
                        border=f"1px solid {t.INFO_BORDER}",
                        border_radius=t.RADIUS_SM,
                        padding="8px 10px",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                num_field("Tên nguyên liệu", "ten_nguyen_lieu", disabled=is_restock),
                rx.grid(
                    rx.vstack(
                        num_field("Danh mục", "danh_muc", disabled=is_restock),
                        rx.cond(
                            ~is_restock,
                            rx.flex(
                                *[_mini_preset_chip(c, "danh_muc") for c in CATEGORY_PRESETS],
                                wrap="wrap",
                                gap="4px",
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        num_field("Đơn vị tính", "don_vi_tinh", disabled=is_restock),
                        rx.cond(
                            ~is_restock,
                            rx.flex(
                                *[_mini_preset_chip(u, "don_vi_tinh") for u in UNIT_PRESETS],
                                wrap="wrap",
                                gap="4px",
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    columns="2",
                    gap="12px",
                    width="100%",
                ),
                rx.grid(
                    num_field("Tồn an toàn", "muc_ton_an_toan", disabled=is_restock),
                    num_field("Tồn tối đa", "muc_ton_toi_da", disabled=is_restock),
                    num_field(
                        rx.cond(is_restock, "Số lượng nhập thêm", "Tồn hiện tại"),
                        "ton_kho_hien_tai",
                    ),
                    columns="3",
                    gap="12px",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(ui.secondary_button("Hủy")),
                ui.primary_button(
                    rx.cond(is_restock, "Nhập thêm vào kho", "Lưu nguyên liệu"),
                    on_click=State.save_ingredient,
                ),
                justify="end",
                width="100%",
                margin_top="20px",
                gap="10px",
            ),
            max_width="580px",
        ),
        open=State.ing_dialog_open,
        on_open_change=State.set_ing_dialog_open,
    )


def delete_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Ngừng sử dụng nguyên liệu?"),
            rx.alert_dialog.description(
                "“" + State.ing_delete_name + "” sẽ bị ẩn khỏi danh sách theo dõi. Dữ liệu lịch sử vẫn được giữ lại.",
                font_size="14px",
            ),
            rx.hstack(
                rx.alert_dialog.cancel(ui.secondary_button("Hủy")),
                rx.alert_dialog.action(ui.primary_button("Ngừng sử dụng", background=t.DANGER, _hover={"background": "#912018"}, on_click=State.confirm_delete_ingredient)),
                justify="end",
                gap="10px",
                margin_top="20px",
            ),
        ),
        open=State.ing_delete_id > 0,
        on_open_change=State.cancel_delete_ingredient,
    )


def tx_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nhập / xuất kho"),
            rx.dialog.description("Xuất bán và hao hụt sẽ tự trừ các lô theo FEFO (hết hạn trước xuất trước).", font_size="13px", color=t.MUTED, margin_bottom="12px"),
            rx.vstack(
                rx.text("Nguyên liệu", font_size="13px", font_weight="500"),
                rx.select.root(
                    rx.select.trigger(width="100%"),
                    rx.select.content(rx.foreach(State.ingredient_options, lambda o: rx.select.item(o["label"], value=o["value"]))),
                    value=State.tx_form["ma_nguyen_lieu"],
                    on_change=lambda v: State.set_tx_field("ma_nguyen_lieu", v),
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Loại giao dịch", font_size="13px", font_weight="500"),
                        rx.select.root(
                            rx.select.trigger(width="100%"),
                            rx.select.content(*[rx.select.item(label, value=v) for v, label in TX_TYPES]),
                            value=State.tx_form["loai_giao_dich"],
                            on_change=lambda v: State.set_tx_field("loai_giao_dich", v),
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Số lượng", font_size="13px", font_weight="500"),
                        rx.input(value=State.tx_form["so_luong"], on_change=lambda v: State.set_tx_field("so_luong", v), placeholder="VD: 2,5", width="100%"),
                        spacing="1",
                    ),
                    columns="2",
                    gap="12px",
                    width="100%",
                ),
                rx.text("Ghi chú", font_size="13px", font_weight="500"),
                rx.input(value=State.tx_form["ghi_chu"], on_change=lambda v: State.set_tx_field("ghi_chu", v), width="100%"),
                spacing="2",
                width="100%",
            ),
            rx.hstack(
                rx.dialog.close(ui.secondary_button("Hủy")),
                ui.primary_button("Ghi nhận", on_click=State.save_transaction),
                justify="end",
                width="100%",
                margin_top="20px",
                gap="10px",
            ),
            max_width="520px",
        ),
        open=State.tx_dialog_open,
        on_open_change=State.set_tx_dialog_open,
    )


def inventory_page() -> rx.Component:
    return layout(
        rx.vstack(
            ui.page_title(
                "Quản lý kho",
                "Quản lý nguyên liệu, lô hàng và toàn bộ biến động tồn kho.",
                ui.primary_button("+  Thêm nguyên liệu", on_click=State.open_add_ingredient, width="180px", justify_content="flex-start", white_space="pre"),
            ),
            ui.underline_tabs(
                [("nguyen-lieu", "Nguyên liệu"), ("lo-hang", "Lô hàng"), ("giao-dich", "Giao dịch kho")],
                State.active_tab_inventory,
                State.set_inventory_tab,
                margin_bottom="21px",
            ),
            rx.match(
                State.active_tab_inventory,
                ("lo-hang", batch_panel()),
                ("giao-dich", transaction_panel()),
                ingredient_panel(),
            ),
            rx.grid(
                recent_transactions(),
                expiry_watch(),
                grid_template_columns=rx.breakpoints(initial="1fr", lg="700fr 428fr"),
                gap="20px",
                width="100%",
            ),
            ingredient_dialog(),
            delete_dialog(),
            tx_dialog(),
            spacing="0",
            width="100%",
        ),
        active_page="inventory",
    )
