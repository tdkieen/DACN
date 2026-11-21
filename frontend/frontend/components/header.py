import reflex as rx
from frontend.components.sidebar import sidebar
from frontend.state import State


def page_header(title: str, description: str, action_btn: rx.Component | None = None) -> rx.Component:
    """Tiêu đề đầu mỗi trang."""
    return rx.hstack(
        rx.vstack(
            rx.heading(title, size="6", font_weight="700", color="#0F172A"),
            rx.text(description, font_size="13px", color="#64748B"),
            spacing="1",
            align_items="start",
        ),
        rx.spacer(),
        rx.cond(action_btn is not None, action_btn, rx.fragment()),
        align="center",
        width="100%",
        padding_bottom="20px",
        border_bottom="1px solid #E2E8F0",
        margin_bottom="24px",
    )


def layout(content: rx.Component, active_page: str = "dashboard") -> rx.Component:
    """Khung layout chuẩn: Sidebar bên trái + Vùng nội dung chính bên phải."""
    return rx.hstack(
        sidebar(active_page=active_page),
        rx.vstack(
            # Topbar cho màn hình nhỏ
            rx.hstack(
                rx.hstack(
                    rx.box(
                        rx.icon("bot", size=18, color="#FFFFFF"),
                        background="#0B6BCB",
                        padding="6px",
                        border_radius="8px",
                    ),
                    rx.text("AI Procurement", font_weight="700", font_size="14px", color="#0F172A"),
                    align="center",
                    spacing="2",
                ),
                rx.spacer(),
                rx.badge(
                    rx.cond(State.backend_online, "Backend: Online", "Backend: Offline"),
                    color_scheme=rx.cond(State.backend_online, "green", "red"),
                    variant="soft",
                ),
                display=["flex", "flex", "none", "none"],
                width="100%",
                padding="12px 16px",
                border_bottom="1px solid #E2E8F0",
                background="#FFFFFF",
            ),

            # Cảnh báo mất kết nối Backend
            rx.cond(
                ~State.backend_online,
                rx.callout(
                    rx.hstack(
                        rx.icon("triangle-alert", color="#DC2626"),
                        rx.text(State.error_message, font_size="13px", color="#991B1B"),
                        align="center",
                        spacing="2",
                    ),
                    color_scheme="red",
                    variant="surface",
                    width="100%",
                    margin_bottom="16px",
                ),
                rx.fragment(),
            ),

            # Nội dung trang con (chỉ hiện khi đã đăng nhập)
            rx.cond(
                State.is_logged_in,
                content,
                rx.center(rx.spinner(size="3"), width="100%", padding="80px"),
            ),

            width="100%",
            min_height="100vh",
            background="#F8FAFC",
            padding=["16px", "20px", "32px", "32px"],
            spacing="0",
            align_items="start",
            overflow_y="auto",
        ),
        spacing="0",
        width="100%",
        min_height="100vh",
        align_items="start",
    )
