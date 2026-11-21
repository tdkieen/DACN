import reflex as rx
from frontend.state import State


def step_item(num: str, title: str, desc: str) -> rx.Component:
    return rx.vstack(
        rx.text(num, font_size="22px", font_weight="600", color="#93C5FD"),
        rx.text(title, font_size="14px", font_weight="600", color="#F1F5F9"),
        rx.text(desc, font_size="12px", color="#94A3B8"),
        spacing="1",
        align_items="start",
        flex="1",
    )


def left_panel() -> rx.Component:
    """Cột trái: giới thiệu hệ thống (ẩn trên màn hình nhỏ)."""
    return rx.vstack(
        rx.hstack(
            rx.box(rx.icon("bot", size=22, color="#FFFFFF"), background="#0B6BCB", padding="8px", border_radius="10px"),
            rx.text("AI Procurement", font_size="18px", font_weight="700", color="#FFFFFF"),
            align="center",
            spacing="3",
        ),
        rx.spacer(),
        rx.vstack(
            rx.badge("TRỢ LÝ MUA HÀNG CHO QUÁN CÀ PHÊ", variant="soft", color_scheme="blue", size="1"),
            rx.heading(
                "Mua hàng thông minh. Vận hành chủ động.",
                size="8",
                color="#FFFFFF",
                line_height="1.15",
                max_width="460px",
            ),
            rx.text(
                "Từ dự báo nhu cầu đến đề xuất mua hàng. Luôn minh bạch, luôn do bạn quyết định.",
                font_size="14px",
                color="#94A3B8",
                max_width="420px",
            ),
            spacing="4",
            align_items="start",
        ),
        rx.box(
            rx.text("MỘT QUY TRÌNH. LUÔN TRONG TẦM KIỂM SOÁT.", font_size="10px", font_weight="700", color="#94A3B8", margin_bottom="14px"),
            rx.hstack(
                step_item("01", "Phát hiện", "Tồn kho dưới ngưỡng"),
                step_item("02", "Đề xuất", "AI phân tích và giải trình"),
                step_item("03", "Phê duyệt", "Quản lý quyết định"),
                width="100%",
                spacing="4",
            ),
            rx.divider(margin_y="14px", color_scheme="gray"),
            rx.text("Không tự động gửi đơn hàng khi chưa được phê duyệt.", font_size="12px", color="#94A3B8"),
            background="#1E293B",
            padding="20px",
            border_radius="10px",
            width="100%",
            max_width="520px",
            margin_top="32px",
        ),
        rx.spacer(),
        rx.text("DÀNH CHO QUẢN LÝ VÀ ĐỘI NGŨ VẬN HÀNH · ĐỒ ÁN HUTECH", font_size="10px", color="#64748B"),
        background="#0F172A",
        padding="40px",
        width="50%",
        min_height="100vh",
        align_items="start",
        display=["none", "none", "flex", "flex"],
    )


def demo_chip(label: str, email: str) -> rx.Component:
    return rx.button(
        label,
        type="button",
        variant="soft",
        color_scheme="gray",
        size="1",
        cursor="pointer",
        on_click=State.fill_demo_account(email),
    )


def login_form() -> rx.Component:
    return rx.vstack(
        rx.badge("CHÀO MỪNG TRỞ LẠI", variant="soft", color_scheme="blue", size="1"),
        rx.heading("Đăng nhập", size="8", color="#0F172A"),
        rx.text("Sẵn sàng cho một ngày vận hành chủ động.", font_size="14px", color="#64748B"),
        rx.form(
            rx.vstack(
                rx.vstack(
                    rx.text("Email", font_size="13px", font_weight="600", color="#0F172A"),
                    rx.input(
                        name="email",
                        type="email",
                        placeholder="ten@congty.vn",
                        value=State.login_email,
                        on_change=State.set_login_email,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                    align_items="start",
                ),
                rx.vstack(
                    rx.text("Mật khẩu", font_size="13px", font_weight="600", color="#0F172A"),
                    rx.input(
                        name="password",
                        type="password",
                        placeholder="Nhập mật khẩu",
                        value=State.login_password,
                        on_change=State.set_login_password,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                    align_items="start",
                ),
                rx.cond(
                    State.login_error != "",
                    rx.callout(
                        State.login_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        variant="surface",
                        size="1",
                        width="100%",
                        role="alert",
                    ),
                    rx.fragment(),
                ),
                rx.button(
                    "Đăng nhập",
                    type="submit",
                    size="3",
                    width="100%",
                    cursor="pointer",
                    background="#0B6BCB",
                    loading=State.login_loading,
                ),
                spacing="4",
                width="100%",
            ),
            on_submit=State.handle_login,
            width="100%",
            margin_top="12px",
        ),
        rx.vstack(
            rx.text("Tài khoản thử nghiệm (bấm để điền sẵn):", font_size="12px", color="#64748B"),
            rx.hstack(
                demo_chip("Quản lý", "quanly@coffee.vn"),
                demo_chip("Nhân viên kho", "kho@coffee.vn"),
                demo_chip("Quản trị", "admin@coffee.vn"),
                spacing="2",
                wrap="wrap",
            ),
            spacing="2",
            align_items="start",
            margin_top="12px",
        ),
        rx.text("Quyền truy cập được phân theo vai trò của tài khoản.", font_size="12px", color="#94A3B8", margin_top="8px"),
        spacing="3",
        align_items="start",
        width="100%",
        max_width="400px",
    )


def login_page() -> rx.Component:
    """Trang đăng nhập (JWT)."""
    return rx.hstack(
        left_panel(),
        rx.center(
            login_form(),
            width=["100%", "100%", "50%", "50%"],
            min_height="100vh",
            padding="32px",
            background="#F8FAFC",
        ),
        spacing="0",
        width="100%",
        min_height="100vh",
        align_items="stretch",
    )
