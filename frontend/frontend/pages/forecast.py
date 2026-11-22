"""Trang Dự báo nhu cầu — Figma frame "03 · Dự báo nhu cầu"."""

import reflex as rx

from frontend import theme as t
from frontend.components import ui
from frontend.components.header import layout
from frontend.state import State


def forecast_ingredient_select(width: str = "272px") -> rx.Component:
    """Ô chọn nguyên liệu hiển thị TÊN (dùng chung cho Dashboard và trang Dự báo)."""
    return rx.select.root(
        rx.select.trigger(placeholder="Chọn nguyên liệu", width=width, height="40px"),
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


def filters() -> rx.Component:
    return ui.card(
        rx.hstack(
            rx.vstack(ui.field_label("NGUYÊN LIỆU"), forecast_ingredient_select(), spacing="0", gap="4px", align_items="start"),
            rx.vstack(
                ui.field_label("KỲ DỰ BÁO"),
                rx.box(
                    rx.text(State.forecast_period, font_size="14px", color=t.INK),
                    height="40px",
                    width="280px",
                    padding="0 14px",
                    display="flex",
                    align_items="center",
                    border=f"1px solid {t.BORDER_STRONG}",
                    border_radius=t.RADIUS_SM,
                    background=t.SURFACE,
                ),
                spacing="0",
                gap="4px",
                align_items="start",
            ),
            rx.spacer(),
            ui.pill("Cập nhật " + State.today_short, tone="primary", border_radius="4px", font_size="11px", align_self="center"),
            width="100%",
            align="end",
            gap="28px",
            wrap="wrap",
        ),
        padding="12px 20px",
        margin_bottom="20px",
    )


def chart_card() -> rx.Component:
    return ui.card(
        rx.hstack(
            rx.vstack(
                rx.text("Nhu cầu tiêu thụ dự kiến", font_size="16px", font_weight="600", color=t.INK),
                rx.text("Đơn vị: " + State.active_forecast_unit + "  ·  Mô hình " + State.forecast_method, font_size="12px", color=t.MUTED, white_space="pre"),
                spacing="0",
                gap="8px",
                align_items="start",
            ),
            rx.spacer(),
            ui.pill("Dự báo 7 ngày", tone="primary", border_radius="4px", font_size="11px"),
            width="100%",
            align="start",
        ),
        rx.cond(
            State.active_forecast_data.length() > 0,
            rx.recharts.area_chart(
                rx.recharts.cartesian_grid(vertical=False, stroke=t.BORDER),
                rx.recharts.x_axis(data_key="ngay", axis_line=False, tick_line=False, tick={"fontSize": 11, "fill": t.MUTED}),
                rx.recharts.y_axis(axis_line=False, tick_line=False, tick={"fontSize": 11, "fill": t.MUTED}, width=34),
                rx.recharts.graphing_tooltip(),
                rx.recharts.area(
                    rx.recharts.label_list(data_key="nhan", position="top", offset=10, fill=t.PRIMARY, custom_attrs={"fontSize": 11, "fontWeight": 600}),
                    data_key="so_luong",
                    name="Nhu cầu dự báo",
                    stroke=t.PRIMARY,
                    stroke_width=2,
                    fill="#DCE8F5",
                    fill_opacity=0.8,
                    dot={"r": 4, "fill": t.PRIMARY, "stroke": t.PRIMARY},
                    type_="linear",
                ),
                data=State.active_forecast_data,
                height=300,
                width="100%",
                margin={"top": 30, "right": 16, "left": 0, "bottom": 0},
            ),
            ui.empty_state("Chưa có dữ liệu dự báo cho nguyên liệu này.", "chart-line"),
        ),
        rx.cond(
            State.forecast_is_estimate,
            rx.text("Nguyên liệu này chưa có dự báo từ mô hình, đang hiển thị số ước tính tạm.", font_size="12px", color=t.WARNING, margin_top="4px"),
            rx.fragment(),
        ),
        padding="19px 22px",
        min_height="397px",
    )


def summary_card() -> rx.Component:
    return ui.card(
        rx.text("Tóm tắt dự báo", font_size="16px", font_weight="600", color=t.INK),
        ui.eyebrow("TỔNG NHU CẦU 7 NGÀY", margin_top="25px"),
        rx.text(State.forecast_total_fmt, font_size="36px", font_weight="600", color=t.INK, line_height="52px", margin_top="9px"),
        ui.divider(margin="16px 0 18px 0"),
        rx.vstack(
            ui.info_row("Trung bình mỗi ngày", State.forecast_avg_fmt),
            ui.info_row("Khoảng tin cậy", State.forecast_confidence, color=t.PRIMARY),
            ui.info_row("Ngày tiêu thụ cao nhất", State.forecast_peak_day),
            spacing="0",
            gap="21px",
            width="100%",
        ),
        rx.vstack(
            rx.text(State.forecast_note, font_size="13px", font_weight="600", color=t.PRIMARY),
            rx.text("Cân nhắc lead time khi đặt hàng.", font_size="12px", color=t.MUTED),
            spacing="0",
            gap="10px",
            align_items="start",
            width="100%",
            margin_top="28px",
            padding="12px 13px",
            border_radius=t.RADIUS_SM,
            background=t.PRIMARY_SOFT,
        ),
        padding="19px 22px",
        min_height="397px",
    )


def step(value, label, highlight: bool = False) -> rx.Component:
    return rx.vstack(
        rx.text(value, font_size="24px", font_weight="600", color=t.PRIMARY if highlight else t.INK, line_height="35px", white_space="nowrap"),
        rx.text(label, font_size="12px", color=t.MUTED),
        spacing="0",
        gap="5px",
        align_items="start",
    )


def replenishment() -> rx.Component:
    r = State.replenishment
    return ui.card(
        rx.text("Từ dự báo đến lượng cần mua", font_size="16px", font_weight="600", color=t.INK),
        rx.grid(
            step(r["demand"], "Nhu cầu 7 ngày"),
            step(r["safety"], "Tồn an toàn"),
            step(r["current"], "Tồn hiện tại"),
            step(r["incoming"], "Hàng đang về"),
            step(r["need"], "Đề xuất bổ sung", highlight=True),
            columns=rx.breakpoints(initial="2", md="5"),
            gap="20px",
            width="100%",
            margin_top="20px",
        ),
        background=t.PRIMARY_TINT,
        padding="18px 22px 26px 22px",
        margin_bottom="20px",
    )


def forecast_page() -> rx.Component:
    return layout(
        rx.vstack(
            ui.page_title(
                "Dự báo nhu cầu",
                "Ước tính nhu cầu nguyên liệu cho 7 ngày tiếp theo.",
                ui.primary_button("Xuất báo cáo", on_click=State.export_forecast, width="180px", justify_content="flex-start"),
            ),
            filters(),
            rx.grid(
                chart_card(),
                summary_card(),
                grid_template_columns=rx.breakpoints(initial="1fr", lg="782fr 346fr"),
                gap="20px",
                width="100%",
                margin_bottom="20px",
            ),
            replenishment(),
            ui.guardrail(
                "Dự báo hỗ trợ quyết định, không thay thế phê duyệt.",
                "AI sử dụng nhu cầu dự báo, tồn kho và báo giá để soạn đề xuất. Quản lý kiểm tra số lượng trước khi duyệt.",
                rx.link(ui.primary_button("Xem đề xuất mua hàng  →", white_space="pre"), href="/proposals"),
                background=t.SURFACE,
                border=f"1px solid {t.BORDER}",
            ),
            spacing="0",
            width="100%",
        ),
        active_page="forecast",
    )
