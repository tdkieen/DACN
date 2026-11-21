import reflex as rx
from frontend.state import State


def nav_item(text: str, icon_name: str, href: str, active: bool = False, count: rx.Var[int] | None = None) -> rx.Component:
    """Mục menu trong Sidebar."""
    return rx.link(
        rx.hstack(
            rx.icon(icon_name, size=18, color=rx.cond(active, "#60A5FA", "#94A3B8")),
            rx.text(text, font_size="14px", font_weight=rx.cond(active, "600", "400"), color=rx.cond(active, "#FFFFFF", "#CBD5E1")),
            rx.spacer(),
            rx.cond(
                count is not None and count > 0,
                rx.badge(count, color_scheme="amber", variant="solid", radius="full", size="1"),
                rx.fragment(),
            ),
            align="center",
            width="100%",
            padding_x="12px",
            padding_y="10px",
            border_radius="8px",
            background=rx.cond(active, "rgba(255, 255, 255, 0.08)", "transparent"),
            _hover={"background": "rgba(255, 255, 255, 0.05)", "color": "#FFFFFF"},
            transition="all 0.15s ease",
        ),
        href=href,
        underline="none",
        width="100%",
    )


def sidebar(active_page: str = "dashboard") -> rx.Component:
    """Thanh điều hướng Sidebar phía bên trái."""
    return rx.vstack(
        # 1. Logo & Tên dự án
        rx.hstack(
            rx.box(
                rx.icon("bot", size=22, color="#FFFFFF"),
                background="#0B6BCB",
                padding="8px",
                border_radius="10px",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.vstack(
                rx.text("AI Procurement", font_size="16px", font_weight="700", color="#FFFFFF", line_height="1.2"),
                rx.text("Quản lý tồn kho F&B", font_size="11px", color="#94A3B8"),
                spacing="0",
                align_items="start",
            ),
            spacing="3",
            align="center",
            width="100%",
            padding_x="16px",
            padding_y="20px",
        ),

        # 2. Không gian làm việc
        rx.box(
            rx.text("KHÔNG GIAN LÀM VIỆC", font_size="10px", font_weight="700", color="#64748B", margin_bottom="6px"),
            rx.vstack(
                rx.text("Cà phê · Chi nhánh 01", font_size="13px", font_weight="600", color="#E2E8F0"),
                rx.text("TP. Hồ Chí Minh · Kho tổng", font_size="11px", color="#94A3B8"),
                spacing="0",
                align_items="start",
                background="#1E293B",
                padding="10px 12px",
                border_radius="8px",
                width="100%",
                border="1px solid #334155",
            ),
            padding_x="16px",
            width="100%",
            margin_bottom="12px",
        ),

        # 3. Danh mục menu
        rx.box(
            rx.text("VẬN HÀNH & QUẢN TRỊ", font_size="10px", font_weight="700", color="#64748B", margin_bottom="8px", padding_x="8px"),
            rx.vstack(
                rx.cond(
                    State.allowed_pages.contains("/dashboard"),
                    nav_item("Tổng quan", "layout-dashboard", "/dashboard", active=(active_page == "dashboard")),
                    rx.fragment(),
                ),
                rx.cond(
                    State.allowed_pages.contains("/inventory"),
                    nav_item("Tồn kho", "package", "/inventory", active=(active_page == "inventory")),
                    rx.fragment(),
                ),
                rx.cond(
                    State.allowed_pages.contains("/forecast"),
                    nav_item("Dự báo nhu cầu", "trending-up", "/forecast", active=(active_page == "forecast")),
                    rx.fragment(),
                ),
                rx.cond(
                    State.allowed_pages.contains("/suppliers"),
                    nav_item("Nhà cung cấp", "truck", "/suppliers", active=(active_page == "suppliers")),
                    rx.fragment(),
                ),
                rx.cond(
                    State.allowed_pages.contains("/proposals"),
                    nav_item(
                        "Đề xuất mua hàng",
                        "clipboard-check",
                        "/proposals",
                        active=(active_page == "proposals"),
                        count=State.pending_proposals_count,
                    ),
                    rx.fragment(),
                ),
                spacing="1",
                width="100%",
            ),
            padding_x="12px",
            width="100%",
        ),

        rx.spacer(),

        # 4. Người dùng đang đăng nhập + Đăng xuất
        rx.hstack(
            rx.center(
                rx.text(State.user_initials, font_size="12px", font_weight="700", color="#FFFFFF"),
                width="34px",
                height="34px",
                border_radius="50%",
                background="#334155",
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(State.display_name, font_size="13px", font_weight="600", color="#E2E8F0", line_height="1.2"),
                rx.text(State.role_label, font_size="11px", color="#94A3B8"),
                spacing="0",
                align_items="start",
            ),
            rx.spacer(),
            rx.cond(
                State.auth_enabled,
                rx.tooltip(
                rx.icon_button(
                    rx.icon("log-out", size=16),
                    variant="ghost",
                    color="#94A3B8",
                    _hover={"color": "#FFFFFF", "background": "rgba(255, 255, 255, 0.08)"},
                    cursor="pointer",
                    aria_label="Đăng xuất",
                    on_click=State.logout,
                ),
                content="Đăng xuất",
                ),
                rx.fragment(),
            ),
            align="center",
            spacing="3",
            width="100%",
            padding="12px 16px",
            border_top="1px solid #1E293B",
        ),

        # 5. Trạng thái kết nối Backend
        rx.box(
            rx.hstack(
                rx.box(
                    width="8px",
                    height="8px",
                    border_radius="50%",
                    background=rx.cond(State.backend_online, "#10B981", "#EF4444"),
                ),
                rx.text(
                    rx.cond(State.backend_online, "FastAPI Backend Online", "Backend Offline"),
                    font_size="11px",
                    color=rx.cond(State.backend_online, "#10B981", "#EF4444"),
                    font_weight="500",
                ),
                align="center",
                spacing="2",
            ),
            rx.text("Đồ án Chuyên ngành - HUTECH", font_size="10px", color="#64748B", margin_top="4px"),
            padding="16px",
            width="100%",
            border_top="1px solid #1E293B",
        ),

        width="260px",
        min_width="260px",
        height="100vh",
        background="#0F172A",
        border_right="1px solid #1E293B",
        position="sticky",
        top="0",
        spacing="0",
        align_items="start",
        display=["none", "none", "flex", "flex"],
    )
