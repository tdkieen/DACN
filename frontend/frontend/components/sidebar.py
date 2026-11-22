import reflex as rx

from frontend import theme as t
from frontend.state import State

# (khóa trang, nhãn, icon, đường dẫn) – đúng thứ tự menu trong Figma
NAV_ITEMS = [
    ("dashboard", "Tổng quan", "layout-grid", "/dashboard"),
    ("inventory", "Quản lý kho", "box", "/inventory"),
    ("forecast", "Dự báo nhu cầu", "chart-line", "/forecast"),
    ("suppliers", "Nhà cung cấp", "truck", "/suppliers"),
    ("proposals", "Đề xuất mua hàng", "file-text", "/proposals"),
    ("history", "Lịch sử duyệt", "clock", "/history"),
]

PAGE_LABELS = {key: label for key, label, _, _ in NAV_ITEMS}


def brand_mark(size: int = 30, icon_size: int = 20) -> rx.Component:
    return rx.center(
        rx.image(src="/procurement-mark.svg", width=f"{icon_size}px", height=f"{icon_size}px"),
        width=f"{size}px",
        height=f"{size}px",
        border_radius="8px",
        background=t.PRIMARY,
        flex_shrink="0",
    )


def nav_item(key: str, label: str, icon: str, href: str, active: bool) -> rx.Component:
    badge = rx.fragment()
    if key == "proposals":
        badge = rx.cond(
            State.pending_proposals_count > 0,
            rx.center(
                rx.text(State.pending_proposals_count, font_size="12px", font_weight="600", color="#FFFFFF"),
                min_width="21px",
                height="20px",
                padding="0 6px",
                border_radius="6px",
                background=t.PRIMARY,
            ),
            rx.fragment(),
        )
    item = rx.link(
        rx.hstack(
            rx.icon(icon, size=18, color="#FFFFFF" if active else t.NAVY_MUTED, flex_shrink="0"),
            rx.text(label, font_size="12.5px", font_weight="600" if active else "500", color="#FFFFFF" if active else t.NAVY_TEXT, white_space="nowrap"),
            rx.spacer(),
            badge,
            align="center",
            spacing="0",
            gap="13px",
            width="100%",
            height="43px",
            padding="0 12px 0 13px",
            border_radius="8px",
            background=t.NAVY_2 if active else "transparent",
            _hover={"background": t.NAVY_2},
        ),
        href=href,
        underline="none",
        width="100%",
    )
    return rx.cond(State.allowed_pages.contains(href), item, rx.fragment())


def sidebar(active_page: str = "dashboard") -> rx.Component:
    """Thanh điều hướng bên trái rộng 228px (Figma: Navigation)."""
    return rx.vstack(
        # Logo
        rx.hstack(
            brand_mark(),
            rx.text("AI Procurement", font_size="17px", font_weight="600", color="#FFFFFF", white_space="nowrap"),
            align="center",
            spacing="0",
            gap="11px",
            padding="27px 24px 0 24px",
        ),
        # Không gian làm việc
        rx.text("KHÔNG GIAN LÀM VIỆC", font_size="10px", font_weight="600", color=t.NAVY_MUTED, letter_spacing="0.04em", padding="42px 24px 12px 24px"),
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text("Cà phê · Chi nhánh 01", font_size="12px", font_weight="600", color="#FFFFFF", white_space="nowrap"),
                    rx.text("Thành phố Hồ Chí Minh", font_size="10.5px", color=t.NAVY_MUTED, white_space="nowrap"),
                    spacing="0",
                    gap="5px",
                    align_items="start",
                ),
                rx.spacer(),
                rx.icon("chevrons-up-down", size=14, color=t.NAVY_MUTED),
                align="center",
                width="100%",
            ),
            margin_x="16px",
            padding="10px 13px",
            min_height="64px",
            display="flex",
            align_items="center",
            border_radius="10px",
            background=t.NAVY_2,
            border=f"1px solid {t.NAVY_3}",
            width="196px",
        ),
        # Menu
        rx.text("VẬN HÀNH", font_size="10px", font_weight="600", color=t.NAVY_MUTED, letter_spacing="0.04em", padding="32px 24px 15px 24px"),
        rx.vstack(
            *[nav_item(k, label, icon, href, active=(k == active_page)) for k, label, icon, href in NAV_ITEMS],
            spacing="0",
            gap="6px",
            width="100%",
            padding_x="12px",
        ),
        rx.spacer(min_height="24px"),
        # Nhắc nhở con người phê duyệt
        rx.vstack(
            rx.icon("sparkles", size=19, color="#B3CFEB"),
            rx.text("AI đề xuất. Bạn quyết định.", font_size="11.5px", font_weight="600", color="#FFFFFF"),
            rx.text("Mọi đơn mua hàng đều cần quản lý phê duyệt.", font_size="11px", color=t.NAVY_TEXT, line_height="16px"),
            spacing="0",
            gap="9px",
            align_items="start",
            margin_x="16px",
            padding="15px",
            width="196px",
            border_radius="10px",
            background=t.NAVY_2,
            border=f"1px solid {t.NAVY_3}",
        ),
        # Tài khoản
        rx.hstack(
            rx.vstack(
                rx.text(State.display_name, font_size="12.5px", font_weight="600", color="#FFFFFF"),
                rx.text(State.role_label, font_size="11px", color=t.NAVY_MUTED),
                spacing="0",
                gap="5px",
                align_items="start",
            ),
            rx.spacer(),
            rx.cond(
                State.auth_enabled,
                rx.tooltip(
                    rx.icon_button(
                        rx.icon("log-out", size=16),
                        variant="ghost",
                        color=t.NAVY_MUTED,
                        cursor="pointer",
                        aria_label="Đăng xuất",
                        on_click=State.logout,
                        _hover={"color": "#FFFFFF", "background": t.NAVY_2},
                    ),
                    content="Đăng xuất",
                ),
                rx.fragment(),
            ),
            align="center",
            width="188px",
            margin="28px 20px 0 20px",
            padding="17px 4px 44px 4px",
            border_top=f"1px solid {t.NAVY_3}",
        ),
        width=t.SIDEBAR_W,
        min_width=t.SIDEBAR_W,
        height="100vh",
        background=t.NAVY,
        position="sticky",
        top="0",
        spacing="0",
        align_items="start",
        overflow_y="auto",
        display=["none", "none", "flex", "flex"],
    )


def mobile_nav_menu() -> rx.Component:
    """Menu thả xuống thay cho sidebar trên màn hình nhỏ."""
    return rx.menu.root(
        rx.menu.trigger(
            rx.icon_button(rx.icon("menu", size=18), variant="ghost", color=t.INK, cursor="pointer", aria_label="Mở menu"),
        ),
        rx.menu.content(
            *[
                rx.cond(
                    State.allowed_pages.contains(href),
                    rx.menu.item(rx.hstack(rx.icon(icon, size=16), rx.text(label), align="center"), on_click=rx.redirect(href)),
                    rx.fragment(),
                )
                for _, label, icon, href in NAV_ITEMS
            ],
        ),
    )
