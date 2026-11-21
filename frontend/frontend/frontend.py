import reflex as rx
from frontend.pages.dashboard import dashboard_page
from frontend.pages.inventory import inventory_page
from frontend.pages.forecast import forecast_page
from frontend.pages.suppliers import suppliers_page
from frontend.pages.proposals import proposals_page
from frontend.pages.login import login_page
from frontend.state import State

# Khởi tạo Reflex App với cấu hình Radix Theme hiện đại
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        accent_color="blue",
        gray_color="slate",
        radius="medium",
    ),
    head_components=[
        rx.el.title("AI Procurement Agent & Quản lý tồn kho cà phê"),
        rx.el.meta(name="description", content="Hệ thống AI Procurement Agent & Quản lý tồn kho quán cà phê - HUTECH"),
    ],
)

# Trang đăng nhập (công khai)
app.add_page(
    login_page,
    route="/login",
    title="Đăng nhập | AI Procurement",
    on_load=State.redirect_if_logged_in,
)

# Các trang nội bộ: luôn chạy State.require_access trước để kiểm tra đăng nhập và vai trò
app.add_page(
    dashboard_page,
    route="/",
    title="Tổng quan tồn kho | AI Procurement",
    on_load=[State.require_access, State.load_dashboard],
)

app.add_page(
    dashboard_page,
    route="/dashboard",
    title="Tổng quan tồn kho | AI Procurement",
    on_load=[State.require_access, State.load_dashboard],
)

app.add_page(
    inventory_page,
    route="/inventory",
    title="Quản lý tồn kho | AI Procurement",
    on_load=[State.require_access, State.load_inventory],
)

app.add_page(
    forecast_page,
    route="/forecast",
    title="Dự báo nhu cầu 7 ngày | AI Procurement",
    on_load=[State.require_access, State.load_dashboard],
)

app.add_page(
    suppliers_page,
    route="/suppliers",
    title="Nhà cung cấp & Báo giá | AI Procurement",
    on_load=[State.require_access, State.load_suppliers],
)

app.add_page(
    proposals_page,
    route="/proposals",
    title="Đề xuất mua hàng AI | AI Procurement",
    on_load=[State.require_access, State.load_proposals],
)
