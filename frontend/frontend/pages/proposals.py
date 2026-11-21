import typing
import reflex as rx
from frontend.components.header import layout, page_header
from frontend.state import State


def proposal_item_row(item: dict) -> rx.Component:
    """Một dòng chi tiết nguyên liệu trong phiếu đề xuất mua hàng."""
    return rx.table.row(
        rx.table.cell(rx.text(item["ten_nguyen_lieu"], font_size="13px", font_weight="600", color="#0F172A")),
        rx.table.cell(rx.badge(item["ten_nha_cung_cap"], color_scheme="blue", variant="surface")),
        rx.table.cell(rx.text(item["so_luong_de_xuat"].to_string() + " " + item["don_vi_tinh"].to_string(), font_size="13px", font_weight="700", color="#0F172A")),
        rx.table.cell(rx.text(f"{item['don_gia_du_kien']} đ", font_size="13px", color="#475569")),
        rx.table.cell(rx.text(f"{item['thanh_tien']} đ", font_size="13px", font_weight="700", color="#0B6BCB")),
        rx.table.cell(
            rx.text(
                item["ly_do_de_xuat"],
                font_size="12px",
                color="#64748B",
                font_style="italic",
            )
        ),
        align="center",
    )


def proposal_card(p: dict) -> rx.Component:
    """Thẻ hiển thị một phiếu đề xuất mua hàng do AI Agent tạo."""
    is_pending = p["trang_thai"] == "CHO_DUYET"
    is_approved = p["trang_thai"] == "DA_DUYET"
    is_rejected = p["trang_thai"] == "TU_CHOI"

    pid = p["ma_phieu_de_xuat"]

    return rx.card(
        rx.vstack(
            # Tiêu đề phiếu đề xuất
            rx.hstack(
                rx.hstack(
                    rx.box(
                        rx.icon("bot", size=22, color="#0B6BCB"),
                        background="#EFF6FF",
                        padding="8px",
                        border_radius="50%",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.heading(f"Phiếu đề xuất mua hàng #{pid}", size="4", color="#0F172A"),
                            rx.cond(
                                is_pending,
                                rx.badge(
                                    rx.hstack(rx.icon("clock", size=12), rx.text("Chờ quản lý duyệt"), spacing="1"),
                                    color_scheme="amber",
                                    variant="solid",
                                    radius="full",
                                ),
                                rx.cond(
                                    is_approved,
                                    rx.badge(
                                        rx.hstack(rx.icon("circle-check", size=12), rx.text("Đã duyệt"), spacing="1"),
                                        color_scheme="green",
                                        variant="solid",
                                        radius="full",
                                    ),
                                    rx.badge(
                                        rx.hstack(rx.icon("circle-x", size=12), rx.text("Đã từ chối"), spacing="1"),
                                        color_scheme="red",
                                        variant="solid",
                                        radius="full",
                                    ),
                                ),
                            ),
                            align="center",
                            spacing="2",
                        ),
                        rx.text(
                            "Tạo bởi: " + p["nguoi_tao"].to_string() + " • " + p["ngay_tao"].to_string(),
                            font_size="12px",
                            color="#64748B",
                        ),
                        spacing="0",
                        align_items="start",
                    ),
                    align="center",
                    spacing="3",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text("Tổng tiền dự kiến", font_size="11px", color="#64748B"),
                    rx.text(f"{p['tong_tien_du_kien']} đ", font_size="16px", font_weight="800", color="#0B6BCB"),
                    spacing="0",
                    align_items="end",
                ),
                width="100%",
                align="center",
                padding_bottom="14px",
                border_bottom="1px solid #E2E8F0",
            ),

            # Lập luận của AI Agent
            rx.callout(
                rx.hstack(
                    rx.icon("sparkles", size=16, color="#2563EB"),
                    rx.vstack(
                        rx.text("Lập luận của AI Procurement Agent:", font_size="12px", font_weight="700", color="#1E40AF"),
                        rx.text(p["ly_do_tong_quan"], font_size="13px", color="#1E3A8A"),
                        spacing="1",
                        align_items="start",
                    ),
                    align="start",
                    spacing="2",
                ),
                color_scheme="blue",
                variant="surface",
                width="100%",
                margin_y="8px",
            ),

            # Bảng chi tiết nguyên liệu cần mua
            rx.text("Danh mục nguyên liệu và nhà cung cấp đề xuất:", font_size="13px", font_weight="600", color="#334155"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Nguyên liệu"),
                        rx.table.column_header_cell("NCC đề xuất"),
                        rx.table.column_header_cell("Số lượng"),
                        rx.table.column_header_cell("Đơn giá"),
                        rx.table.column_header_cell("Thành tiền"),
                        rx.table.column_header_cell("Lý do chọn NCC / Số lượng"),
                    ),
                ),
                rx.table.body(
                    rx.foreach(p["details"].to(list[dict[str, typing.Any]]), proposal_item_row),
                ),
                width="100%",
                variant="surface",
            ),

            # Tài khoản không có quyền duyệt: chỉ xem
            rx.cond(
                is_pending & ~State.can_approve,
                rx.callout(
                    "Phiếu đang chờ Quản lý cửa hàng phê duyệt. Tài khoản của bạn chỉ có quyền xem.",
                    icon="lock",
                    color_scheme="gray",
                    variant="surface",
                    size="1",
                    width="100%",
                ),
                rx.fragment(),
            ),

            # Vùng xét duyệt Human-in-the-loop (Chỉ hiện khi CHO_DUYET và là Quản lý)
            rx.cond(
                is_pending & State.can_approve,
                rx.vstack(
                    rx.divider(margin_y="12px"),
                    rx.hstack(
                        rx.icon("shield-check", size=18, color="#0B6BCB"),
                        rx.text("Phê duyệt của Quản lý (Human-in-the-loop):", font_size="13px", font_weight="700", color="#0F172A"),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Nhập ý kiến hoặc lý do phê duyệt / từ chối...",
                            on_change=lambda val: State.set_proposal_comment(pid.to_string(), val),
                            width="100%",
                            size="2",
                        ),
                        rx.button(
                            rx.hstack(rx.icon("check", size=15), rx.text("Phê duyệt")),
                            color_scheme="green",
                            size="2",
                            cursor="pointer",
                            on_click=State.handle_proposal_action(pid, "APPROVE"),
                        ),
                        rx.button(
                            rx.hstack(rx.icon("x", size=15), rx.text("Từ chối")),
                            color_scheme="red",
                            variant="surface",
                            size="2",
                            cursor="pointer",
                            on_click=State.handle_proposal_action(pid, "REJECT"),
                        ),
                        width="100%",
                        align="center",
                        spacing="2",
                    ),
                    width="100%",
                    spacing="2",
                    background="#F8FAFC",
                    padding="14px",
                    border_radius="10px",
                    border="1px dashed #CBD5E1",
                ),
                rx.fragment(),
            ),

            width="100%",
            spacing="3",
        ),
        background="#FFFFFF",
        border="1px solid " + rx.cond(is_pending, "#BFDBFE", "#E2E8F0"),
        border_radius="12px",
        padding="20px",
        width="100%",
        margin_bottom="20px",
    )


def proposals_page() -> rx.Component:
    """Trang Đề xuất mua hàng (AI Procurement Agent - Human-in-the-loop)."""
    return layout(
        rx.vstack(
            page_header(
                title="Đề xuất mua hàng (AI Human-in-the-loop)",
                description="Phiếu đề xuất thông minh do AI Procurement Agent tự động lập; Quản lý xem xét, chỉnh sửa và phê duyệt.",
                action_btn=rx.button(
                    rx.hstack(
                        rx.icon("refresh-cw", size=15),
                        rx.text("Làm mới danh sách"),
                        align="center",
                        spacing="2",
                    ),
                    on_click=State.load_proposals,
                    variant="outline",
                    size="2",
                    cursor="pointer",
                ),
            ),

            rx.cond(
                State.proposals.length() == 0,
                rx.center(
                    rx.vstack(
                        rx.icon("inbox", size=40, color="#94A3B8"),
                        rx.text("Chưa có phiếu đề xuất mua hàng nào.", font_size="14px", color="#64748B"),
                        spacing="2",
                        align="center",
                        padding="60px",
                    ),
                    width="100%",
                ),
                rx.vstack(
                    rx.foreach(State.proposals, proposal_card),
                    width="100%",
                    spacing="0",
                ),
            ),

            spacing="0",
            width="100%",
        ),
        active_page="proposals",
    )
