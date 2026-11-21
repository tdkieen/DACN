import typing
import reflex as rx
from frontend.components.header import layout, page_header
from frontend.state import State


def supplier_quotation_row(q: dict) -> rx.Component:
    """Một dòng báo giá của nhà cung cấp."""
    return rx.table.row(
        rx.table.cell(rx.text(q["ten_nguyen_lieu"], font_size="13px", font_weight="600", color="#0F172A")),
        rx.table.cell(rx.text(f"{q['don_gia']} đ", font_size="13px", font_weight="700", color="#0B6BCB")),
        rx.table.cell(rx.text(q["so_luong_dat_toi_thieu"].to_string(), font_size="13px", color="#475569")),
        rx.table.cell(rx.text(f"{q['thoi_gian_giao_hang']} ngày", font_size="13px", color="#475569")),
        align="center",
    )


def supplier_card(sup: dict) -> rx.Component:
    """Thẻ thông tin của một Nhà cung cấp."""
    is_expanded = State.expanded_suppliers.contains(sup["ma_nha_cung_cap"])

    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.text(sup["ten_nha_cung_cap"], font_size="16px", font_weight="700", color="#0F172A"),
                        rx.badge(
                            rx.hstack(
                                rx.icon("star", size=12, color="#EAB308"),
                                rx.text(sup["diem_uy_tin"].to_string() + "/5.0", font_size="11px", font_weight="700"),
                                spacing="1",
                                align="center",
                            ),
                            color_scheme="amber",
                            variant="surface",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.icon("user", size=13, color="#64748B"),
                        rx.text("LH: " + sup["nguoi_lien_he"].to_string(), font_size="12px", color="#64748B"),
                        rx.text("•", color="#CBD5E1"),
                        rx.icon("phone", size=13, color="#64748B"),
                        rx.text(sup["sdt"].to_string(), font_size="12px", color="#64748B"),
                        rx.text("•", color="#CBD5E1"),
                        rx.icon("truck", size=13, color="#64748B"),
                        rx.text(f"Giao {sup['thoi_gian_giao_du_kien']} ngày", font_size="12px", color="#0B6BCB", font_weight="600"),
                        spacing="2",
                        align="center",
                        wrap="wrap",
                    ),
                    spacing="1",
                    align_items="start",
                ),
                rx.spacer(),
                rx.button(
                    rx.hstack(
                        rx.text(rx.cond(is_expanded, "Thu gọn", "Xem báo giá")),
                        rx.icon(rx.cond(is_expanded, "chevron-up", "chevron-down"), size=15),
                        spacing="1",
                        align="center",
                    ),
                    variant="surface",
                    size="2",
                    on_click=State.toggle_supplier_expand(sup["ma_nha_cung_cap"]),
                    cursor="pointer",
                ),
                width="100%",
                align="center",
            ),

            # Bảng báo giá mở rộng
            rx.cond(
                is_expanded,
                rx.vstack(
                    rx.divider(margin_y="12px"),
                    rx.text("Bảng giá nguyên liệu cung ứng:", font_size="13px", font_weight="600", color="#334155"),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Nguyên liệu"),
                                rx.table.column_header_cell("Đơn giá"),
                                rx.table.column_header_cell("MOQ (Tối thiểu)"),
                                rx.table.column_header_cell("Thời gian giao"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(sup["quotations"].to(list[dict[str, typing.Any]]), supplier_quotation_row),
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    width="100%",
                    spacing="2",
                ),
                rx.fragment(),
            ),

            width="100%",
            spacing="2",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
        border_radius="12px",
        padding="18px",
        width="100%",
        margin_bottom="12px",
    )


def price_compare_row(row: dict) -> rx.Component:
    """Một dòng trong bảng so sánh giá."""
    return rx.table.row(
        rx.table.cell(rx.text(row["ten_nha_cung_cap"], font_size="13px", font_weight="600", color="#0F172A")),
        rx.table.cell(rx.text(row["ten_nguyen_lieu"], font_size="13px", color="#475569")),
        rx.table.cell(rx.text(f"{row['don_gia']} đ", font_size="13px", font_weight="700", color="#0B6BCB")),
        rx.table.cell(rx.text(row["so_luong_dat_toi_thieu"].to_string(), font_size="13px", color="#475569")),
        rx.table.cell(rx.text(f"{row['thoi_gian_giao_hang']} ngày", font_size="13px", color="#475569")),
        rx.table.cell(
            rx.badge(
                row["diem_uy_tin"].to_string() + " ★",
                color_scheme="amber",
                variant="surface",
            )
        ),
        align="center",
    )


def suppliers_page() -> rx.Component:
    """Trang Quản lý Nhà cung cấp & So sánh báo giá."""
    return layout(
        rx.vstack(
            page_header(
                title="Nhà cung cấp & Báo giá",
                description="Thông tin đối tác cung ứng, lead time, độ uy tín và bảng so sánh báo giá đa tiêu chuẩn (MCDM).",
                action_btn=rx.button(
                    rx.hstack(
                        rx.icon("refresh-cw", size=15),
                        rx.text("Làm mới"),
                        align="center",
                        spacing="2",
                    ),
                    on_click=State.load_suppliers,
                    variant="outline",
                    size="2",
                    cursor="pointer",
                ),
            ),

            # Chuyển tab
            rx.hstack(
                rx.button(
                    rx.hstack(rx.icon("truck", size=16), rx.text("Danh sách nhà cung cấp")),
                    variant=rx.cond(State.active_tab_suppliers == "danh-sach", "solid", "surface"),
                    color_scheme=rx.cond(State.active_tab_suppliers == "danh-sach", "blue", "gray"),
                    on_click=State.set_suppliers_tab("danh-sach"),
                    cursor="pointer",
                ),
                rx.button(
                    rx.hstack(rx.icon("scale", size=16), rx.text("So sánh giá đa tiêu chí")),
                    variant=rx.cond(State.active_tab_suppliers == "so-sanh", "solid", "surface"),
                    color_scheme=rx.cond(State.active_tab_suppliers == "so-sanh", "blue", "gray"),
                    on_click=State.set_suppliers_tab("so-sanh"),
                    cursor="pointer",
                ),
                spacing="2",
                margin_bottom="16px",
            ),

            # TAB 1: DANH SÁCH NHÀ CUNG CẤP
            rx.cond(
                State.active_tab_suppliers == "danh-sach",
                rx.vstack(
                    rx.card(
                        rx.hstack(
                            rx.input(
                                placeholder="Tìm kiếm tên nhà cung cấp...",
                                value=State.supplier_search,
                                on_change=State.set_supplier_search,
                                width="320px",
                                size="2",
                            ),
                            rx.button(
                                "Tìm kiếm",
                                on_click=State.load_suppliers,
                                size="2",
                                color_scheme="blue",
                                cursor="pointer",
                            ),
                            rx.spacer(),
                            rx.badge(
                                State.suppliers.length().to_string() + " nhà cung cấp",
                                color_scheme="gray",
                                variant="surface",
                            ),
                            width="100%",
                            align="center",
                        ),
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        border_radius="12px",
                        padding="14px",
                        width="100%",
                        margin_bottom="16px",
                    ),
                    rx.cond(
                        State.suppliers.length() == 0,
                        rx.center(rx.text("Không tìm thấy nhà cung cấp nào.", color="#64748B"), padding="40px", width="100%"),
                        rx.vstack(
                            rx.foreach(State.suppliers, supplier_card),
                            width="100%",
                            spacing="0",
                        ),
                    ),
                    width="100%",
                    spacing="0",
                ),

                # TAB 2: SO SÁNH GIÁ ĐA TIÊU CHÍ
                rx.vstack(
                    rx.card(
                        rx.hstack(
                            rx.text("Lọc theo nguyên liệu:", font_size="13px", font_weight="600", color="#475569"),
                            rx.select(
                                State.supplier_ingredient_options,
                                value=State.compare_ingredient_name,
                                on_change=State.set_compare_ingredient,
                                size="2",
                                width="240px",
                            ),
                            rx.spacer(),
                            rx.badge("Thuật toán MCDM / TCO", color_scheme="blue", variant="soft"),
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
                                    rx.table.column_header_cell("Nhà cung cấp"),
                                    rx.table.column_header_cell("Nguyên liệu"),
                                    rx.table.column_header_cell("Đơn giá"),
                                    rx.table.column_header_cell("MOQ"),
                                    rx.table.column_header_cell("Lead time"),
                                    rx.table.column_header_cell("Điểm uy tín"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(State.price_comparison_rows, price_compare_row),
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
        active_page="suppliers",
    )
