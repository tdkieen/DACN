"""Trang đăng nhập — dựng theo Figma frame "01 · Đăng nhập" (node 2:2)."""
import reflex as rx

from frontend.state import State

FONT = "'Be Vietnam Pro', sans-serif"

# Màu lấy từ Figma
NAVY = "#0e2031"
NAVY_CARD = "#1a2d3f"
PRIMARY = "#0B6BCB"
BADGE_BG = "#e7eff6"
INK = "#15222f"
MUTED = "#636b73"
BORDER = "#d4e1ef"
PAGE_BG = "#f9fbfc"
PANEL_TEXT = "#bcc6d0"


class LoginUI(rx.State):
    """Trạng thái giao diện riêng của trang đăng nhập."""

    show_password: bool = False
    remember: bool = False

    @rx.event
    def toggle_password(self):
        self.show_password = not self.show_password

    @rx.event
    def set_remember(self, val: bool):
        self.remember = val

    @rx.event
    def forgot_password(self):
        return rx.toast.info("Vui lòng liên hệ quản trị viên để đặt lại mật khẩu.")


def _badge(text: str) -> rx.Component:
    return rx.box(
        text,
        background=BADGE_BG,
        color=PRIMARY,
        font_size="10px",
        font_weight="500",
        padding="4px 10px",
        border_radius="4px",
        line_height="1.45",
        width="fit-content",
    )


def _step(num: str, title: str, desc: str) -> rx.Component:
    return rx.box(
        rx.text(num, font_size="28px", font_weight="600", color="#b3cfeb", line_height="1.45"),
        rx.text(title, font_size="14px", font_weight="600", color="#ffffff", margin_top="8px", line_height="1.45"),
        rx.text(desc, font_size="10px", color=PANEL_TEXT, margin_top="6px", line_height="1.45"),
        flex="1",
    )


def left_panel() -> rx.Component:
    return rx.box(
        # Logo
        rx.hstack(
            rx.center(
                rx.image(src="/procurement-mark.svg", width="24px", height="24px"),
                width="36px",
                height="36px",
                background=PRIMARY,
                border_radius="8px",
            ),
            rx.text("AI Procurement", font_size="22px", font_weight="600", color="#ffffff", line_height="1.45"),
            spacing="4",
            align="center",
        ),
        rx.box(margin_top="84px"),
        _badge("TRỢ LÝ MUA HÀNG CHO F&B"),
        rx.box(
            rx.text("Mua hàng", display="block"),
            rx.text("thông minh.", display="block"),
            rx.text("Vận hành", display="block"),
            rx.text("chủ động.", display="block"),
            font_size="58px",
            font_weight="600",
            color="#eaf1f7",
            line_height="1.45",
            margin_top="33px",
        ),
        rx.box(
            rx.text("Từ dự báo nhu cầu đến đề xuất mua hàng."),
            rx.text("Luôn minh bạch, luôn do bạn quyết định."),
            font_size="16px",
            color=PANEL_TEXT,
            line_height="1.45",
            margin_top="26px",
            padding_left="4px",
        ),
        # Thẻ 3 bước
        rx.box(
            rx.text("MỘT QUY TRÌNH. LUÔN TRONG TẦM KIỂM SOÁT.", font_size="10px", font_weight="600", color="#b9c6d3", line_height="1.45"),
            rx.hstack(
                _step("01", "Phát hiện", "Tồn kho dưới ngưỡng"),
                _step("02", "Đề xuất", "AI phân tích & giải trình"),
                _step("03", "Phê duyệt", "Quản lý quyết định"),
                spacing="0",
                width="100%",
                margin_top="26px",
            ),
            rx.box(height="1px", background=BORDER, margin_top="26px"),
            rx.text("Không tự động gửi đơn hàng khi chưa được phê duyệt.", font_size="10px", color=PANEL_TEXT, margin_top="11px", line_height="1.45"),
            background=NAVY_CARD,
            border_radius="8px",
            padding="18px 22px 14px 22px",
            width="100%",
            max_width="552px",
            margin_top="66px",
        ),
        rx.text(
            "DÀNH CHO QUẢN LÝ VÀ ĐỘI NGŨ VẬN HÀNH",
            font_size="10px",
            font_weight="600",
            color="#8d9ba9",
            margin_top="60px",
            line_height="1.45",
        ),
        background=NAVY,
        padding="51px 54px 40px 54px",
        width="660px",
        flex_shrink="0",
        min_height="100vh",
        font_family=FONT,
        display=["none", "none", "none", "block"],
    )


def _label(text: str) -> rx.Component:
    return rx.text(text, font_size="13px", font_weight="500", color=INK, line_height="1.45")


_INPUT_STYLE = dict(
    width="100%",
    height="52px",
    background="#ffffff",
    border=f"1px solid {BORDER}",
    border_radius="8px",
    padding="0 15px",
    font_size="14px",
    color=INK,
    font_family=FONT,
    outline="none",
    _placeholder={"color": MUTED},
    _focus={"border": f"1px solid {PRIMARY}", "box_shadow": "0 0 0 3px rgba(11,107,203,0.15)"},
)


def login_form() -> rx.Component:
    return rx.box(
        _badge("CHÀO MỪNG TRỞ LẠI"),
        rx.text("Đăng nhập", font_size="38px", font_weight="600", color=INK, line_height="1.45", margin_top="22px"),
        rx.text("Sẵn sàng cho một ngày vận hành chủ động.", font_size="14px", color=MUTED, line_height="1.45", margin_top="6px"),
        rx.form(
            _label("Email"),
            rx.el.input(
                name="email",
                type="email",
                placeholder="ten@congty.vn",
                auto_complete="username",
                value=State.login_email,
                on_change=State.set_login_email,
                margin_top="10px",
                **_INPUT_STYLE,
            ),
            rx.box(_label("Mật khẩu"), margin_top="20px"),
            rx.box(
                rx.el.input(
                    name="password",
                    type=rx.cond(LoginUI.show_password, "text", "password"),
                    placeholder="Nhập mật khẩu",
                    auto_complete="current-password",
                    value=State.login_password,
                    on_change=State.set_login_password,
                    **{**_INPUT_STYLE, "padding": "0 52px 0 15px"},
                ),
                rx.box(
                    rx.cond(
                        LoginUI.show_password,
                        rx.icon("eye-off", size=20, color=MUTED),
                        rx.image(src="/eye.svg", width="22px", height="22px"),
                    ),
                    on_click=LoginUI.toggle_password,
                    role="button",
                    aria_label="Hiện hoặc ẩn mật khẩu",
                    position="absolute",
                    right="18px",
                    top="15px",
                    cursor="pointer",
                ),
                position="relative",
                margin_top="10px",
            ),
            rx.hstack(
                rx.el.label(
                    rx.el.input(
                        type="checkbox",
                        checked=LoginUI.remember,
                        on_change=LoginUI.set_remember,
                        style={"width": "16px", "height": "16px", "accent_color": PRIMARY, "border_radius": "4px", "margin": "0", "cursor": "pointer"},
                    ),
                    rx.text("Ghi nhớ đăng nhập", font_size="12px", color=MUTED, line_height="1.45"),
                    display="flex",
                    align_items="center",
                    gap="11px",
                    cursor="pointer",
                ),
                rx.box(
                    "Quên mật khẩu?",
                    on_click=LoginUI.forgot_password,
                    role="button",
                    font_size="12px",
                    font_weight="600",
                    color=PRIMARY,
                    cursor="pointer",
                ),
                justify="between",
                align="center",
                width="100%",
                margin_top="22px",
            ),
            rx.cond(
                State.login_error != "",
                rx.box(
                    rx.icon("triangle-alert", size=16, color="#b42318"),
                    rx.text(State.login_error, font_size="13px", color="#b42318"),
                    display="flex",
                    align_items="center",
                    gap="8px",
                    background="#fef3f2",
                    border="1px solid #fecdca",
                    border_radius="8px",
                    padding="10px 12px",
                    margin_top="16px",
                    role="alert",
                ),
                rx.fragment(),
            ),
            rx.el.button(
                rx.cond(State.login_loading, "Đang đăng nhập…", "Đăng nhập  →"),
                type="submit",
                disabled=State.login_loading,
                style={
                    "width": "100%",
                    "height": "52px",
                    "background": PRIMARY,
                    "color": "#ffffff",
                    "border": "none",
                    "border_radius": "6px",
                    "font_size": "13px",
                    "font_weight": "600",
                    "font_family": FONT,
                    "cursor": "pointer",
                    "margin_top": "24px",
                    "white_space": "pre",
                    "_hover": {"background": "#0959a8"},
                    "_disabled": {"opacity": "0.7", "cursor": "not-allowed"},
                },
            ),
            on_submit=State.handle_login,
            width="100%",
            margin_top="46px",
        ),
        rx.text(
            "Quyền truy cập được phân theo vai trò của tài khoản.",
            font_size="12px",
            color=MUTED,
            line_height="1.45",
            margin_top="26px",
        ),
        # Tài khoản thử nghiệm (không có trong Figma, chỉ phục vụ demo đồ án)
        rx.hstack(
            rx.text("Tài khoản thử nghiệm:", font_size="11px", color=MUTED),
            _demo_chip("Quản lý", "quanly@coffee.vn"),
            _demo_chip("Nhân viên kho", "kho@coffee.vn"),
            _demo_chip("Quản trị", "admin@coffee.vn"),
            spacing="2",
            wrap="wrap",
            align="center",
            margin_top="14px",
        ),
        width="100%",
        max_width="480px",
    )


def _demo_chip(label: str, email: str) -> rx.Component:
    return rx.box(
        label,
        on_click=State.fill_demo_account(email),
        role="button",
        font_size="11px",
        color=PRIMARY,
        background=BADGE_BG,
        padding="3px 8px",
        border_radius="4px",
        cursor="pointer",
    )


def login_page() -> rx.Component:
    return rx.box(
        rx.hstack(
            left_panel(),
            rx.box(
                rx.text(
                    "Tiếng Việt  ⌄",
                    font_size="12px",
                    color=MUTED,
                    position="absolute",
                    top="57px",
                    right="60px",
                ),
                rx.center(
                    login_form(),
                    width="100%",
                    min_height="100vh",
                    padding="80px 24px",
                ),
                rx.text(
                    "AI Procurement Agent  ·  Dữ liệu minh họa",
                    font_size="11px",
                    color=MUTED,
                    position="absolute",
                    bottom="40px",
                    left="0",
                    right="0",
                    text_align="center",
                    white_space="pre",
                ),
                position="relative",
                flex="1",
                background=PAGE_BG,
                min_height="100vh",
            ),
            spacing="0",
            align_items="stretch",
            width="100%",
        ),
        font_family=FONT,
        width="100%",
    )
