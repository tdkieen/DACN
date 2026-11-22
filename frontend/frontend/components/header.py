import reflex as rx

from frontend import theme as t
from frontend.components.sidebar import PAGE_LABELS, mobile_nav_menu, sidebar
from frontend.state import State


def top_bar(active_page: str) -> rx.Component:
    """Thanh trên cao 76px: breadcrumb, nhãn dữ liệu, chuông, ngôn ngữ, vai trò (Figma: Top bar)."""
    crumb = PAGE_LABELS.get(active_page, "")
    return rx.hstack(
        rx.box(mobile_nav_menu(), display=["block", "block", "none", "none"]),
        rx.hstack(
            rx.text("Không gian làm việc", font_size="14px", color=t.MUTED, display=["none", "inline", "inline", "inline"]),
            rx.text("/", font_size="14px", color=t.SUBTLE, display=["none", "inline", "inline", "inline"]),
            rx.text(crumb, font_size="14px", font_weight="600", color=t.INK),
            align="center",
            spacing="0",
            gap="12px",
        ),
        rx.spacer(),
        rx.hstack(
            rx.box(
                width="8px",
                height="8px",
                border_radius="50%",
                background=rx.cond(State.backend_online, "#12B76A", "#F04438"),
            ),
            rx.text(
                rx.cond(State.backend_online, "Dữ liệu trực tiếp", "Mất kết nối máy chủ"),
                font_size="13px",
                color=t.MUTED,
            ),
            align="center",
            spacing="2",
            display=["none", "none", "flex", "flex"],
        ),
        rx.box(width="1px", height="30px", background=t.BORDER, margin_x="24px", display=["none", "none", "block", "block"]),
        rx.link(
            rx.box(
                rx.icon("bell", size=21, color=t.TEXT),
                rx.cond(
                    State.alerts.length() > 0,
                    rx.box(width="8px", height="8px", border_radius="50%", background="#F04438", position="absolute", top="0", right="0", border="2px solid #FFFFFF"),
                    rx.fragment(),
                ),
                position="relative",
                display="flex",
            ),
            href="/inventory",
            aria_label="Cảnh báo tồn kho",
        ),
        rx.hstack(
            rx.text("VI", font_size="14px", font_weight="600", color=t.INK),
            rx.icon("chevron-down", size=14, color=t.MUTED),
            align="center",
            spacing="0",
            gap="11px",
            margin_left="29px",
        ),
        rx.text(State.short_role, font_size="14px", font_weight="600", color=t.INK, margin_left="32px", display=["none", "inline", "inline", "inline"]),
        width="100%",
        height=t.TOPBAR_H,
        min_height=t.TOPBAR_H,
        align="center",
        padding_x=["16px", "24px", "32px", "32px"],
        gap="12px",
        background=t.SURFACE,
        border_bottom=f"1px solid {t.BORDER}",
        position="sticky",
        top="0",
        z_index="10",
    )


def layout(content: rx.Component, active_page: str = "dashboard") -> rx.Component:
    """Khung chuẩn: Sidebar 228px + Top bar 76px + vùng làm việc (padding 27px / 32px)."""
    return rx.hstack(
        # Ô nền navy kéo dài hết chiều cao trang; sidebar bên trong dính (sticky) khi cuộn
        rx.box(
            sidebar(active_page=active_page),
            background=t.NAVY,
            align_self="stretch",
            flex_shrink="0",
            display=["none", "none", "block", "block"],
        ),
        rx.vstack(
            top_bar(active_page),
            rx.box(
                rx.cond(
                    ~State.backend_online,
                    rx.hstack(
                        rx.icon("triangle-alert", size=16, color=t.DANGER),
                        rx.text(State.error_message, font_size="13px", color=t.DANGER),
                        align="center",
                        spacing="2",
                        width="100%",
                        padding="12px 16px",
                        margin_bottom="20px",
                        border_radius=t.RADIUS_SM,
                        background=t.DANGER_SOFT,
                        border=f"1px solid {t.DANGER_BORDER}",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    State.is_logged_in,
                    content,
                    rx.center(rx.spinner(size="3"), width="100%", padding="80px"),
                ),
                width="100%",
                max_width="1212px",
                padding=["20px 16px 32px", "24px 24px 32px", "27px 32px 32px", "27px 32px 32px"],
            ),
            width="100%",
            min_width="0",
            min_height="100vh",
            background=t.BG,
            spacing="0",
            align_items="start",
        ),
        spacing="0",
        width="100%",
        min_height="100vh",
        align_items="start",
        background=t.BG,
        font_family=t.FONT_FAMILY,
    )
