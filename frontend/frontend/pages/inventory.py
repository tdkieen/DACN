import reflex as rx
from frontend.components.header import layout, page_header
from frontend.state import State


def ingredient_row(item: dict) -> rx.Component:
    """Một dòng nguyên liệu trong bảng tồn kho."""
    is_danger = item["tinh_trang"] == "NGUY_CO_THIEU"
    is_warning = item["tinh_trang"] == "TON_DU"

    return rx.table.row(
        rx.table.cell(rx.text(f"#{item['ma_nguyen_lieu']}", font_size="13px", color="#64748B")),
        rx.table.cell(
            rx.vstack(
                rx.text(item["ten_nguyen_lieu"], font_size="14px", font_weight="600", color="#0F172A"),
                rx.cond(
                    item["thong_bao_canh_bao"] != "",
                    rx.text(item["thong_bao_canh_bao"], font_size="11px", color="#DC2626"),
                    rx.fragment(),
                ),
                spacing="0",
                align_items="start",
            )
        ),
        rx.table.cell(rx.text(item["don_vi_tinh"], font_size="13px", color="#475569")),
        rx.table.cell(
            rx.text(
                f"{item['ton_kho_hien_tai']} {item['don_vi_tinh']}",
                font_size="13px",
                font_weight="700",
                color=rx.cond(is_danger, "#DC2626", rx.cond(is_warning, "#D97706", "#0F172A")),
            )
        ),
        rx.table.cell(rx.text(f"{item['muc_ton_an_toan']} {item['don_vi_tinh']}", font_size="13px", color="#64748B")),
        rx.table.cell(rx.text(f"{item['diem_dat_hang_lai_rop']} {item['don_vi_tinh']}", font_size="13px", font_weight="600", color="#475569")),
        rx.table.cell(rx.text(f"{item['nhu_cau_du_bao_7ngay']} {item['don_vi_tinh']}", font_size="13px", color="#0B6BCB")),
        rx.table.cell(
            rx.cond(
                is_danger,
                rx.badge("Nguy cơ thiếu", color_scheme="red", variant="solid", radius="full"),
                rx.cond(
                    is_warning,
                    rx.badge("Tồn dư", color_scheme="amber", variant="solid", radius="full"),
                    rx.badge("An toàn", color_scheme="green", variant="solid", radius="full"),
                ),
            )
        ),
        align="center",
    )


def batch_row(batch: dict) -> rx.Component:
    """Một dòng lô hàng nhập kho."""
    is_expired = batch["so_ngay_con_han"].to(int) < 0
    is_warning = batch["canh_bao_het_han"]

    return rx.table.row(
        rx.table.cell(rx.text(batch["ten_nguyen_lieu"], font_size="14px", font_weight="600", color="#0F172A")),
        rx.table.cell(rx.badge(batch["ma_lo_nha_cung_cap"], color_scheme="gray", variant="surface")),
        rx.table.cell(rx.text(batch["so_luong_nhap"].to_string() + " / " + batch["so_luong_con_lai"].to_string(), font_size="13px", font_weight="600")),
        rx.table.cell(rx.text(batch["han_su_dung"], font_size="13px", color="#475569")),
        rx.table.cell(
            rx.cond(
                is_expired,
                rx.badge("Đã hết hạn", color_scheme="red", variant="solid", radius="full"),
                rx.cond(
                    is_warning,
                    rx.badge("Sắp hết hạn", color_scheme="amber", variant="solid", radius="full"),
                    rx.badge("Còn hạn", color_scheme="green", variant="solid", radius="full"),
                ),
            )
        ),
        align="center",
    )


def inventory_page() -> rx.Component:
    """Trang Quản lý tồn kho."""
    return layout(
        rx.vstack(
            page_header(
                title="Quản lý tồn kho",
                description="Theo dõi tồn kho thực tế, ngưỡng an toàn và điểm đặt hàng lại (ROP) tự động theo thời gian thực.",
                action_btn=rx.button(
                    rx.hstack(
                        rx.icon("refresh-cw", size=15),
                        rx.text("Làm mới"),
                        align="center",
                        spacing="2",
                    ),
                    on_click=State.load_inventory,
                    variant="outline",
                    size="2",
                    cursor="pointer",
                ),
            ),

            # Chuyển đổi tab
            rx.hstack(
                rx.button(
                    rx.hstack(rx.icon("package", size=16), rx.text("Nguyên liệu")),
                    variant=rx.cond(State.active_tab_inventory == "nguyen-lieu", "solid", "surface"),
                    color_scheme=rx.cond(State.active_tab_inventory == "nguyen-lieu", "blue", "gray"),
                    on_click=State.set_inventory_tab("nguyen-lieu"),
                    cursor="pointer",
                ),
                rx.button(
                    rx.hstack(rx.icon("layers", size=16), rx.text("Lô hàng & Hạn sử dụng")),
                    variant=rx.cond(State.active_tab_inventory == "lo-hang", "solid", "surface"),
                    color_scheme=rx.cond(State.active_tab_inventory == "lo-hang", "blue", "gray"),
                    on_click=State.set_inventory_tab("lo-hang"),
                    cursor="pointer",
                ),
                spacing="2",
                margin_bottom="16px",
            ),

            # TAB 1: NGUYÊN LIỆU
            rx.cond(
                State.active_tab_inventory == "nguyen-lieu",
                rx.vstack(
                    # Thanh tìm kiếm & Bộ lọc
                    rx.card(
                        rx.hstack(
                            rx.input(
                                placeholder="Tìm kiếm tên nguyên liệu...",
                                value=State.ingredient_search,
                                on_change=State.set_ingredient_search,
                                width="320px",
                                size="2",
                            ),
                            rx.button(
                                "Tìm kiếm",
                                on_click=State.load_inventory,
                                size="2",
                                color_scheme="blue",
                                cursor="pointer",
                            ),
                            rx.spacer(),
                            rx.button(
                                "Tất cả",
                                variant=rx.cond(State.ingredient_status_filter == "ALL", "solid", "outline"),
                                size="2",
                                on_click=[State.set_status_filter("ALL"), State.load_inventory],
                                cursor="pointer",
                            ),
                            rx.button(
                                "Nguy cơ thiếu (ROP)",
                                color_scheme="red",
                                variant=rx.cond(State.ingredient_status_filter == "NGUY_CO_THIEU", "solid", "outline"),
                                size="2",
                                on_click=[State.set_status_filter("NGUY_CO_THIEU"), State.load_inventory],
                                cursor="pointer",
                            ),
                            rx.button(
                                "Tồn dư đọng vốn",
                                color_scheme="amber",
                                variant=rx.cond(State.ingredient_status_filter == "TON_DU", "solid", "outline"),
                                size="2",
                                on_click=[State.set_status_filter("TON_DU"), State.load_inventory],
                                cursor="pointer",
                            ),
                            rx.button(
                                "An toàn",
                                color_scheme="green",
                                variant=rx.cond(State.ingredient_status_filter == "AN_TOAN", "solid", "outline"),
                                size="2",
                                on_click=[State.set_status_filter("AN_TOAN"), State.load_inventory],
                                cursor="pointer",
                            ),
                            width="100%",
                            align="center",
                            wrap="wrap",
                            gap="8px",
                        ),
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        border_radius="12px",
                        padding="14px",
                        width="100%",
                        margin_bottom="16px",
                    ),

                    # Bảng dữ liệu nguyên liệu
                    rx.card(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Mã"),
                                    rx.table.column_header_cell("Tên nguyên liệu"),
                                    rx.table.column_header_cell("Đơn vị"),
                                    rx.table.column_header_cell("Tồn kho hiện tại"),
                                    rx.table.column_header_cell("Ngưỡng an toàn"),
                                    rx.table.column_header_cell("Điểm ROP"),
                                    rx.table.column_header_cell("Dự báo 7 ngày"),
                                    rx.table.column_header_cell("Tình trạng"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(State.ingredients, ingredient_row),
                            ),
                            width="100%",
                            variant="surface",
                        ),
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        border_radius="12px",
                        padding="16px",
                        width="100%",
                        overflow_x="auto",
                    ),
                    width="100%",
                    spacing="0",
                ),

                # TAB 2: LÔ HÀNG & HẠN SỬ DỤNG
                rx.vstack(
                    rx.card(
                        rx.hstack(
                            rx.checkbox(
                                "Chỉ hiển thị các lô hàng sắp hết hạn hoặc đã quá hạn",
                                checked=State.only_expiring_batches,
                                on_change=[State.toggle_expiring_batches, State.load_inventory],
                            ),
                            rx.spacer(),
                            rx.badge(
                                State.batches.length().to_string() + " lô hàng",
                                color_scheme="gray",
                                variant="surface",
                            ),
                            align="center",
                            width="100%",
                        ),
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        border_radius="12px",
                        padding="14px",
                        width="100%",
                        margin_bottom="16px",
                    ),
                    rx.card(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Nguyên liệu"),
                                    rx.table.column_header_cell("Mã lô NCC"),
                                    rx.table.column_header_cell("Nhập / Còn lại"),
                                    rx.table.column_header_cell("Hạn sử dụng"),
                                    rx.table.column_header_cell("Tình trạng HSD"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(State.batches, batch_row),
                            ),
                            width="100%",
                            variant="surface",
                        ),
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        border_radius="12px",
                        padding="16px",
                        width="100%",
                        overflow_x="auto",
                    ),
                    width="100%",
                    spacing="0",
                ),
            ),

            spacing="0",
            width="100%",
        ),
        active_page="inventory",
    )
