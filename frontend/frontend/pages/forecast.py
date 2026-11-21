import reflex as rx
from frontend.components.header import layout, page_header
from frontend.state import State


def forecast_ingredient_select() -> rx.Component:
    """Ô chọn nguyên liệu hiển thị TÊN (dùng chung cho Dashboard và trang Dự báo)."""
    return rx.select.root(
        rx.select.trigger(placeholder="Chọn nguyên liệu", width="280px"),
        rx.select.content(
            rx.foreach(
                State.forecast_options,
                lambda opt: rx.select.item(opt["label"], value=opt["value"]),
            ),
        ),
        value=State.selected_forecast_id,
        on_change=State.set_selected_forecast,
        size="2",
    )


def forecast_day_row(item: dict) -> rx.Component:
    """Một dòng chi tiết theo ngày dự báo."""
    return rx.table.row(
        rx.table.cell(rx.text(item["ngay"], font_size="13px", font_weight="600", color="#0F172A")),
        rx.table.cell(
            rx.text(
                item["so_luong"].to_string() + " " + State.active_forecast_unit,
                font_size="13px",
                font_weight="700",
                color="#0B6BCB",
            )
        ),
        rx.table.cell(
            rx.badge(
                item["do_tin_cay_pct"].to_string() + "%",
                color_scheme=rx.cond(State.active_forecast_is_estimate, "gray", "green"),
                variant="surface",
                radius="full",
            )
        ),
        rx.table.cell(rx.badge(State.active_forecast_method, color_scheme="gray", variant="soft")),
        align="center",
    )


def stat_box(label: str, value, color: str = "#0F172A") -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(label, font_size="11px", font_weight="700", color="#64748B"),
            rx.heading(value, size="6", color=color),
            spacing="1",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
        border_radius="10px",
        padding="16px",
    )


def forecast_page() -> rx.Component:
    """Trang Chi tiết dự báo nhu cầu (AI Demand Forecasting)."""
    return layout(
        rx.vstack(
            page_header(
                title="Dự báo nhu cầu nguyên liệu",
                description="Nhu cầu nguyên liệu dự kiến trong 7 ngày tới, kèm độ tin cậy và phương pháp dự báo.",
                action_btn=rx.button(
                    rx.hstack(
                        rx.icon("refresh-cw", size=15),
                        rx.text("Cập nhật dự báo"),
                        align="center",
                        spacing="2",
                    ),
                    on_click=State.load_dashboard,
                    variant="outline",
                    size="2",
                    cursor="pointer",
                ),
            ),

            # Chọn nguyên liệu để xem dự báo
            rx.card(
                rx.hstack(
                    rx.text("Nguyên liệu:", font_size="13px", font_weight="600", color="#475569"),
                    forecast_ingredient_select(),
                    rx.spacer(),
                    rx.badge(
                        rx.hstack(rx.icon("cpu", size=13), rx.text("Phương pháp: " + State.active_forecast_method), spacing="1"),
                        color_scheme=rx.cond(State.active_forecast_is_estimate, "gray", "blue"),
                        variant="soft",
                    ),
                    align="center",
                    width="100%",
                    wrap="wrap",
                ),
                background="#FFFFFF",
                border="1px solid #E2E8F0",
                border_radius="12px",
                padding="16px",
                width="100%",
                margin_bottom="20px",
            ),

            # Cảnh báo khi chưa có dự báo thật từ mô hình
            rx.cond(
                State.active_forecast_is_estimate,
                rx.callout(
                    "Nguyên liệu này chưa có dự báo từ mô hình. Các con số bên dưới chỉ là ước tính tạm "
                    "và sẽ được thay khi mô hình chạy xong.",
                    icon="triangle-alert",
                    color_scheme="amber",
                    variant="surface",
                    size="1",
                    width="100%",
                    margin_bottom="20px",
                ),
                rx.fragment(),
            ),

            rx.cond(
                State.active_forecast_data.length() == 0,
                rx.center(
                    rx.vstack(
                        rx.icon("inbox", size=40, color="#94A3B8"),
                        rx.text("Chưa có dữ liệu dự báo.", font_size="14px", color="#64748B"),
                        spacing="2",
                        align="center",
                        padding="60px",
                    ),
                    width="100%",
                ),
                rx.vstack(
                    # 3 thẻ thống kê tổng hợp của nguyên liệu đang chọn
                    rx.grid(
                        stat_box(
                            "TỔNG NHU CẦU 7 NGÀY",
                            State.active_forecast_info["tong_nhu_cau_7ngay"].to_string()
                            + " "
                            + State.active_forecast_unit,
                            "#0B6BCB",
                        ),
                        stat_box(
                            "TRUNG BÌNH MỖI NGÀY",
                            State.active_forecast_info["trung_binh_ngay"].to_string()
                            + " "
                            + State.active_forecast_unit
                            + "/ngày",
                        ),
                        stat_box(
                            "ĐỘ TIN CẬY TRUNG BÌNH",
                            State.active_forecast_confidence,
                            rx.cond(State.active_forecast_is_estimate, "#64748B", "#059669"),
                        ),
                        columns=rx.breakpoints(initial="1", sm="3"),
                        gap="16px",
                        width="100%",
                        margin_bottom="24px",
                    ),

                    # Biểu đồ đường dự báo
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("chart-line", size=18, color="#0B6BCB"),
                                rx.text("Đường cong dự báo tiêu thụ 7 ngày tiếp theo", font_size="15px", font_weight="700", color="#0F172A"),
                                align="center",
                                spacing="2",
                                padding_bottom="12px",
                                border_bottom="1px solid #E2E8F0",
                                width="100%",
                            ),
                            rx.recharts.line_chart(
                                rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="#E2E8F0"),
                                rx.recharts.x_axis(data_key="ngay", stroke="#64748B", font_size="12px"),
                                rx.recharts.y_axis(stroke="#64748B", font_size="12px"),
                                rx.recharts.tooltip(),
                                rx.recharts.line(
                                    data_key="so_luong",
                                    name="Số lượng dự báo",
                                    stroke="#0B6BCB",
                                    stroke_width=3,
                                    dot=True,
                                ),
                                data=State.active_forecast_data,
                                height=280,
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        border_radius="12px",
                        padding="20px",
                        width="100%",
                        margin_bottom="24px",
                    ),

                    # Bảng chi tiết từng ngày
                    rx.card(
                        rx.vstack(
                            rx.text("Bảng chi tiết 7 ngày", font_size="15px", font_weight="700", color="#0F172A", margin_bottom="12px"),
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Ngày dự báo"),
                                        rx.table.column_header_cell("Số lượng dự báo"),
                                        rx.table.column_header_cell("Độ tin cậy"),
                                        rx.table.column_header_cell("Phương pháp"),
                                    ),
                                ),
                                rx.table.body(
                                    rx.foreach(State.active_forecast_data, forecast_day_row),
                                ),
                                width="100%",
                                variant="surface",
                            ),
                            width="100%",
                            spacing="0",
                        ),
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        border_radius="12px",
                        padding="20px",
                        width="100%",
                    ),
                    width="100%",
                    spacing="0",
                ),
            ),

            spacing="0",
            width="100%",
        ),
        active_page="forecast",
    )
