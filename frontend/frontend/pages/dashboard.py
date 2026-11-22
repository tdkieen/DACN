"""Trang Tổng quan tồn kho — Figma frame "02 · Tổng quan tồn kho"."""

import reflex as rx

from frontend import theme as t
from frontend.components import ui
from frontend.components.header import layout
from frontend.state import State


def kpi(title, value, hint, hint_color) -> rx.Component:
    return ui.card(
        rx.vstack(
            rx.text(title, font_size="13px", font_weight="500", color=t.TEXT),
            rx.text(value, font_size="30px", font_weight="600", color=t.INK, line_height="42px"),
            rx.text(hint, font_size="12px", font_weight="500", color=hint_color),
            spacing="0",
            gap="4px",
            align_items="start",
        ),
        padding="15px 20px",
        min_height="115px",
    )


def alert_banner() -> rx.Component:
    return rx.cond(
        State.shortage_names != "",
        rx.hstack(
            rx.vstack(
                rx.text("Cần chú ý: " + State.shortage_names + " đang dưới điểm đặt hàng lại.", font_size="13px", font_weight="600", color=t.DANGER),
                rx.text("AI đã chuẩn bị đề xuất bổ sung. Hãy xem xét trước khi đặt hàng.", font_size="12px", color="#D1665C"),
                spacing="0",
                gap="5px",
                align_items="start",
            ),
            rx.spacer(),
            ui.text_link("Xem đề xuất  →", href="/proposals", color=t.DANGER, font_size="12px"),
            width="100%",
            align="center",
            padding="12px 20px",
            min_height="64px",
            background=t.DANGER_SOFT,
            border=f"1px solid {t.DANGER_BORDER}",
            border_radius=t.RADIUS,
            wrap="wrap",
            gap="8px",
            margin_bottom="20px",
        ),
        rx.fragment(),
    )


def forecast_mini_chart() -> rx.Component:
    return ui.card(
        rx.hstack(
            rx.vstack(
                rx.text("Dự báo nhu cầu 7 ngày", font_size="16px", font_weight="600", color=t.INK),
                rx.text(State.active_forecast_name + " · " + State.active_forecast_unit, font_size="12px", color=t.MUTED),
                spacing="0",
                gap="6px",
                align_items="start",
            ),
            rx.spacer(),
            ui.pill("Tổng " + State.forecast_total_fmt, tone="primary", border_radius="4px", font_size="11px"),
            width="100%",
            align="start",
        ),
        rx.cond(
            State.active_forecast_data.length() > 0,
            rx.recharts.area_chart(
                rx.recharts.cartesian_grid(vertical=False, stroke=t.BORDER),
                rx.recharts.x_axis(data_key="t", axis_line=False, tick_line=False, tick={"fontSize": 11, "fill": t.MUTED}),
                rx.recharts.y_axis(axis_line=False, tick_line=False, tick={"fontSize": 11, "fill": t.MUTED}, width=30),
                rx.recharts.graphing_tooltip(),
                rx.recharts.area(
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
                height=190,
                width="100%",
                margin={"top": 16, "right": 8, "left": 0, "bottom": 0},
            ),
            ui.empty_state("Chưa có dữ liệu dự báo.", "chart-line"),
        ),
        padding="18px 20px 12px 20px",
        min_height="281px",
    )


def ai_recommendation() -> rx.Component:
    return rx.box(
        rx.vstack(
            ui.eyebrow_pill("AI PROCUREMENT AGENT", dark=True),
            rx.text("Bổ sung đúng lúc.", rx.el.br(), "Không mua dư thừa.", font_size="24px", font_weight="600", color="#FFFFFF", line_height="35px", margin_top="18px"),
            rx.text(State.ai_reco["text"], font_size="12px", color=t.NAVY_TEXT, line_height="17px", margin_top="10px"),
            rx.spacer(),
            rx.link(
                rx.box(
                    rx.text("Xem giải trình  →", font_size="13px", font_weight="600", color=t.INK),
                    width="100%",
                    height="40px",
                    padding="0 14px",
                    display="flex",
                    align_items="center",
                    background="#FFFFFF",
                    border_radius="6px",
                    _hover={"background": t.PRIMARY_SOFT},
                ),
                href=State.ai_reco["href"].to(str),
                underline="none",
                width="100%",
                margin_top="20px",
            ),
            spacing="0",
            align_items="start",
            height="100%",
        ),
        background=t.NAVY,
        border_radius=t.RADIUS,
        padding="20px",
        min_height="281px",
        width="100%",
    )


WATCH_COLS = [("Nguyên liệu", "26%"), ("Đơn vị", "10%"), ("Tồn hiện tại", "14.5%"), ("Tồn an toàn", "15.5%"), ("ROP", "16%"), ("Trạng thái", "18%")]


def watch_row(r: rx.Var) -> rx.Component:
    return ui.table_row(
        ui.cell(r["ten_nguyen_lieu"], WATCH_COLS[0][1], font_size="12px", font_weight="600", padding_right="12px"),
        ui.cell(r["don_vi_tinh"], WATCH_COLS[1][1], font_size="12px", color=t.TEXT),
        ui.cell(r["ton_fmt"], WATCH_COLS[2][1], font_size="12px", color=t.TEXT),
        ui.cell(r["an_toan_fmt"], WATCH_COLS[3][1], font_size="12px", color=t.TEXT),
        ui.cell(r["rop_fmt"], WATCH_COLS[4][1], font_size="12px", color=t.TEXT),
        ui.cell(ui.pill(r["status_label"], tone=r["tone"], border_radius="4px", font_size="11px"), WATCH_COLS[5][1]),
        height="48px",
    )


def watchlist() -> rx.Component:
    return ui.card(
        rx.hstack(
            rx.text("Nguyên liệu cần theo dõi", font_size="16px", font_weight="600", color=t.INK),
            rx.spacer(),
            ui.text_link("Xem tất cả nguyên liệu  →", href="/inventory", font_size="11px"),
            width="100%",
            align="center",
            margin_bottom="18px",
        ),
        rx.box(
            ui.table_header(WATCH_COLS, height="37px"),
            rx.foreach(State.watchlist_rows, watch_row),
            overflow_x="auto",
            width="100%",
        ),
        padding="17px 20px 8px 20px",
    )


def dashboard_page() -> rx.Component:
    return layout(
        rx.vstack(
            ui.page_title(
                "Tổng quan tồn kho",
                State.today_text,
                ui.primary_button(
                    rx.cond(State.generating, "AI đang phân tích…", "Tạo đề xuất với AI"),
                    on_click=State.generate_ai_proposal,
                    disabled=State.generating,
                    width="180px",
                    justify_content="flex-start",
                ),
            ),
            rx.grid(
                kpi("Nguyên liệu đang theo dõi", State.kpi_tracked, State.kpi_tracked_hint, t.SUCCESS),
                kpi("Nguy cơ thiếu hàng", State.kpi_shortage, State.kpi_shortage_hint, t.DANGER),
                kpi("Nguy cơ tồn dư", State.kpi_overstock, State.kpi_overstock_hint, t.WARNING),
                kpi("Đề xuất chờ duyệt", State.kpi_pending, "Tổng dự kiến " + State.pending_total_fmt, t.PRIMARY),
                columns=rx.breakpoints(initial="1", sm="2", lg="4"),
                gap="20px",
                width="100%",
                margin_bottom="20px",
            ),
            alert_banner(),
            rx.grid(
                forecast_mini_chart(),
                ai_recommendation(),
                grid_template_columns=rx.breakpoints(initial="1fr", lg="730fr 398fr"),
                gap="20px",
                width="100%",
                margin_bottom="20px",
            ),
            watchlist(),
            spacing="0",
            width="100%",
        ),
        active_page="dashboard",
    )
