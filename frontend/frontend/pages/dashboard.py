import reflex as rx
from frontend.components.header import layout, page_header
from frontend.components.stat_card import stat_card
from frontend.pages.forecast import forecast_ingredient_select
from frontend.state import State


def alert_row(alert: dict) -> rx.Component:
    """Một dòng cảnh báo trong mục 'Cần chú ý'."""
    is_danger = alert["muc_do"] == "DANGER"
    return rx.hstack(
        rx.box(
            width="8px",
            height="8px",
            border_radius="50%",
            background=rx.cond(is_danger, "#DC2626", "#D97706"),
            margin_top="6px",
        ),
        rx.vstack(
            rx.text(alert["ten_nguyen_lieu"], font_size="14px", font_weight="600", color="#0F172A"),
            rx.text(alert["noi_dung"], font_size="12px", color="#64748B"),
            spacing="0",
            align_items="start",
            flex="1",
        ),
        rx.cond(
            alert["so_luong_can_bo_sung"].to(float) > 0,
            rx.vstack(
                rx.text(f"+{alert['so_luong_can_bo_sung']} {alert['don_vi_tinh']}", font_size="13px", font_weight="700", color="#DC2626"),
                rx.text("cần bổ sung", font_size="11px", color="#94A3B8"),
                spacing="0",
                align_items="end",
            ),
            rx.fragment(),
        ),
        align="start",
        width="100%",
        padding="12px 16px",
        border_bottom="1px solid #F1F5F9",
        _hover={"background": "#F8FAFC"},
    )


def dashboard_page() -> rx.Component:
    """Trang Tổng quan (Dashboard)."""
    return layout(
        rx.vstack(
            page_header(
                title="Tổng quan tồn kho",
                description="Tồn kho hiện tại, nguyên liệu cần chú ý, xu hướng tiêu hao theo định mức BOM và nhu cầu dự kiến 7 ngày tới.",
                action_btn=rx.link(
                    rx.button(
                        rx.hstack(
                            rx.text("Xem đề xuất mua hàng"),
                            rx.icon("arrow-right", size=16),
                            align="center",
                            spacing="2",
                        ),
                        background="#0B6BCB",
                        color="#FFFFFF",
                        size="2",
                        cursor="pointer",
                    ),
                    href="/proposals",
                ),
            ),

            # 1. 4 Thẻ KPI thống kê
            rx.grid(
                stat_card(
                    title="Nguyên liệu theo dõi",
                    value=State.stats["tong_nguyen_lieu_dang_dung"],
                    hint="Tỷ lệ an toàn: " + State.stats["ty_le_an_toan"].to_string() + "%",
                    icon_name="package",
                    tone="primary",
                ),
                stat_card(
                    title="Nguy cơ thiếu hàng",
                    value=State.stats["nguy_co_thieu_hang"],
                    hint="Tồn kho ≤ Điểm đặt hàng lại (ROP)",
                    icon_name="circle-alert",
                    tone="danger",
                ),
                stat_card(
                    title="Nguy cơ tồn dư",
                    value=State.stats["nguy_co_ton_du"],
                    hint="Vượt mức tối đa / Đọng vốn",
                    icon_name="triangle-alert",
                    tone="warning",
                ),
                stat_card(
                    title="Đề xuất chờ duyệt",
                    value=State.stats["phieu_cho_duyet"],
                    hint="Do AI Agent lập, chờ quản lý",
                    icon_name="clipboard-check",
                    tone="success",
                ),
                columns="4",
                gap="16px",
                width="100%",
                margin_bottom="24px",
            ),

            # 2. Hai khối chính: Cảnh báo & Biểu đồ tiêu hao 12 tháng
            rx.grid(
                # Cột trái: Cảnh báo
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.hstack(
                                rx.icon("bell", size=18, color="#0B6BCB"),
                                rx.text("Cần chú ý", font_size="15px", font_weight="700", color="#0F172A"),
                                rx.badge(
                                    State.alerts.length(),
                                    color_scheme="red",
                                    variant="surface",
                                    radius="full",
                                ),
                                align="center",
                                spacing="2",
                            ),
                            rx.spacer(),
                            rx.link(
                                rx.hstack(
                                    rx.text("Mở tồn kho", font_size="12px", color="#0B6BCB", font_weight="600"),
                                    rx.icon("arrow-right", size=14, color="#0B6BCB"),
                                    align="center",
                                    spacing="1",
                                ),
                                href="/inventory",
                            ),
                            width="100%",
                            padding_bottom="12px",
                            border_bottom="1px solid #E2E8F0",
                        ),
                        rx.cond(
                            State.alerts.length() == 0,
                            rx.center(
                                rx.vstack(
                                    rx.icon("circle-check", size=32, color="#10B981"),
                                    rx.text("Mọi nguyên liệu đang ở mức an toàn", font_size="13px", color="#64748B"),
                                    spacing="2",
                                    align="center",
                                    padding="32px",
                                ),
                                width="100%",
                            ),
                            rx.vstack(
                                rx.foreach(State.alerts, alert_row),
                                width="100%",
                                spacing="0",
                                max_height="320px",
                                overflow_y="auto",
                            ),
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    background="#FFFFFF",
                    border="1px solid #E2E8F0",
                    border_radius="12px",
                    padding="20px",
                    width="100%",
                ),

                # Cột phải: Tiêu hao & Chi phí 12 tháng
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("bar-chart-3", size=18, color="#0B6BCB"),
                            rx.text("Tiêu hao và chi phí 12 tháng", font_size="15px", font_weight="700", color="#0F172A"),
                            rx.spacer(),
                            rx.badge("BOM quy đổi", color_scheme="blue", variant="soft", size="1"),
                            width="100%",
                            align="center",
                            padding_bottom="12px",
                            border_bottom="1px solid #E2E8F0",
                        ),
                        rx.cond(
                            State.trends.length() > 0,
                            rx.recharts.composed_chart(
                                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="#E2E8F0"),
                                rx.recharts.x_axis(data_key="thang", stroke="#64748B", font_size="11px"),
                                rx.recharts.y_axis(y_axis_id="left", stroke="#64748B", font_size="11px"),
                                rx.recharts.y_axis(y_axis_id="right", orientation="right", stroke="#64748B", font_size="11px"),
                                rx.recharts.tooltip(),
                                rx.recharts.legend(),
                                rx.recharts.bar(data_key="tong_tieu_hao_kg", name="Tiêu hao (kg/đv)", fill="#0B6BCB", y_axis_id="left", radius=[4, 4, 0, 0]),
                                rx.recharts.line(data_key="chi_phi_trieu", name="Chi phí (Triệu đ)", stroke="#D97706", stroke_width=2, y_axis_id="right"),
                                data=State.trends,
                                height=280,
                                width="100%",
                            ),
                            rx.center(rx.text("Đang tải dữ liệu biểu đồ...", color="#94A3B8"), height="280px", width="100%"),
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    background="#FFFFFF",
                    border="1px solid #E2E8F0",
                    border_radius="12px",
                    padding="20px",
                    width="100%",
                ),
                columns="2",
                gap="16px",
                width="100%",
                margin_bottom="24px",
            ),

            # 3. Khối Dự báo nhu cầu 7 ngày
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.hstack(
                            rx.icon("sparkles", size=18, color="#0B6BCB"),
                            rx.text("Dự báo nhu cầu 7 ngày tới (AI Demand Forecasting)", font_size="15px", font_weight="700", color="#0F172A"),
                            align="center",
                            spacing="2",
                        ),
                        rx.spacer(),
                        forecast_ingredient_select(),
                        width="100%",
                        align="center",
                        padding_bottom="12px",
                        border_bottom="1px solid #E2E8F0",
                    ),
                    rx.cond(
                        State.active_forecast_data.length() > 0,
                        rx.vstack(
                            rx.hstack(
                                rx.badge("Tổng 7 ngày: " + State.active_forecast_info["tong_nhu_cau_7ngay"].to_string() + " " + State.active_forecast_unit, color_scheme="blue", variant="surface"),
                                rx.badge("Trung bình: " + State.active_forecast_info["trung_binh_ngay"].to_string() + "/ngày", color_scheme="gray", variant="surface"),
                                rx.spacer(),
                                rx.text("Mô hình: Prophet & XGBoost Regressor", font_size="12px", color="#64748B"),
                                width="100%",
                                align="center",
                                margin_bottom="8px",
                            ),
                            rx.recharts.line_chart(
                                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="#E2E8F0"),
                                rx.recharts.x_axis(data_key="ngay", stroke="#64748B", font_size="11px"),
                                rx.recharts.y_axis(stroke="#64748B", font_size="11px"),
                                rx.recharts.tooltip(),
                                rx.recharts.line(
                                    data_key="so_luong",
                                    name="Nhu cầu dự báo",
                                    stroke="#0B6BCB",
                                    stroke_width=3,
                                    dot=True,
                                ),
                                data=State.active_forecast_data,
                                height=240,
                                width="100%",
                            ),
                            width="100%",
                        ),
                        rx.center(rx.text("Chưa có dữ liệu dự báo cho nguyên liệu này.", color="#94A3B8"), height="240px", width="100%"),
                    ),
                    spacing="3",
                    width="100%",
                ),
                background="#FFFFFF",
                border="1px solid #E2E8F0",
                border_radius="12px",
                padding="20px",
                width="100%",
            ),

            spacing="0",
            width="100%",
        ),
        active_page="dashboard",
    )
