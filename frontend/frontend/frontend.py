import reflex as rx

from frontend import theme as t
from frontend.pages.dashboard import dashboard_page
from frontend.pages.forecast import forecast_page
from frontend.pages.history import history_page
from frontend.pages.inventory import inventory_page
from frontend.pages.login import login_page
from frontend.pages.proposal_detail import proposal_detail_page
from frontend.pages.proposals import proposals_page
from frontend.pages.suppliers import suppliers_page
from frontend.state import State

# Reflex App: font Be Vietnam Pro + Radix Theme sáng (màu chi tiết nằm ở frontend/theme.py)
app = rx.App(
    stylesheets=[t.FONT_URL],
    style={
        "font_family": t.FONT_FAMILY,
        "::selection": {"background": t.PRIMARY_SOFT},
    },
    theme=rx.theme(
        appearance="light",
        has_background=True,
        accent_color="blue",
        gray_color="slate",
        radius="medium",
    ),
    head_components=[
        rx.el.meta(name="description", content="Hệ thống AI Procurement Agent & Quản lý tồn kho quán cà phê - HUTECH"),
    ],
)

# Trang đăng nhập (công khai)
app.add_page(login_page, route="/login", title="Đăng nhập | AI Procurement", on_load=State.redirect_if_logged_in)

# Các trang nội bộ: luôn chạy State.require_access trước để kiểm tra đăng nhập và vai trò
PAGES = [
    (dashboard_page, "/", "Tổng quan tồn kho", State.load_dashboard),
    (dashboard_page, "/dashboard", "Tổng quan tồn kho", State.load_dashboard),
    (inventory_page, "/inventory", "Quản lý kho", [State.load_inventory, State.load_rop_plan]),
    (forecast_page, "/forecast", "Dự báo nhu cầu", State.load_forecast),
    (suppliers_page, "/suppliers", "Nhà cung cấp và báo giá", [State.load_suppliers, State.load_rop_plan]),
    (proposals_page, "/proposals", "Đề xuất mua hàng", State.load_proposals),
    (proposal_detail_page, "/proposals/[ma_phieu]", "Chi tiết đề xuất", State.load_proposal_detail),
    (history_page, "/history", "Lịch sử duyệt", State.load_history),
]

for component, route, title, loader in PAGES:
    app.add_page(component, route=route, title=f"{title} | AI Procurement", on_load=[State.require_access, *(loader if isinstance(loader, list) else [loader])])
