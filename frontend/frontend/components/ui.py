"""Các khối giao diện dùng chung, dựng theo thiết kế Figma."""

import reflex as rx

from frontend import theme as t


def card(*children, **props) -> rx.Component:
    """Thẻ trắng bo góc 12px, viền mảnh (khối nội dung chuẩn trong Figma)."""
    style = dict(
        background=t.SURFACE,
        border=f"1px solid {t.BORDER}",
        border_radius=t.RADIUS,
        padding="20px",
        width="100%",
    )
    style.update(props)
    return rx.box(*children, **style)


def section_title(text, **props) -> rx.Component:
    return rx.text(text, font_size="18px", font_weight="700", color=t.INK, line_height="23px", **props)


def eyebrow(text, **props) -> rx.Component:
    """Nhãn chữ in hoa nhỏ (VD: NGUYÊN LIỆU, TỔNG NHU CẦU 7 NGÀY)."""
    style = dict(font_size="11px", font_weight="600", color=t.SUBTLE, letter_spacing="0.06em", text_transform="uppercase")
    style.update(props)
    return rx.text(text, **style)


def _tone_style(tone):
    """Trả về (nền, chữ, viền) cho tone tĩnh hoặc tone là Var."""
    if isinstance(tone, str):
        return t.TONES.get(tone, t.TONES["neutral"])
    bg = rx.match(tone, *[(k, v[0]) for k, v in t.TONES.items()], t.TONES["neutral"][0])
    fg = rx.match(tone, *[(k, v[1]) for k, v in t.TONES.items()], t.TONES["neutral"][1])
    bd = rx.match(tone, *[(k, v[2]) for k, v in t.TONES.items()], t.TONES["neutral"][2])
    return bg, fg, bd


def pill(text, tone="neutral", **props) -> rx.Component:
    """Nhãn trạng thái dạng viên thuốc cao 25px (Thiếu hàng, Đủ hàng, Chờ duyệt...)."""
    bg, fg, bd = _tone_style(tone)
    style = dict(
        display="inline-flex",
        align_items="center",
        height="25px",
        padding="0 10px",
        border_radius="999px",
        background=bg,
        color=fg,
        border="1px solid",
        border_color=bd,
        font_size="12px",
        font_weight="600",
        white_space="nowrap",
        width="fit-content",
    )
    style.update(props)
    return rx.box(rx.text(text), **style)


def eyebrow_pill(text, dark: bool = False) -> rx.Component:
    """Nhãn in hoa có nền (VD: TRỢ LÝ MUA HÀNG CHO F&B, AI PROCUREMENT AGENT)."""
    return rx.box(
        rx.text(text, font_size="10px", font_weight="600", letter_spacing="0.04em"),
        display="inline-flex",
        align_items="center",
        height="25px",
        padding="0 10px",
        border_radius="4px",
        background=t.NAVY_2 if dark else t.PRIMARY_SOFT,
        color="#B3CFEB" if dark else t.PRIMARY,
        width="fit-content",
    )


def primary_button(label, icon: str | None = None, **props) -> rx.Component:
    """Nút chính màu navy cao 40px."""
    children = [rx.text(label)]
    if icon:
        children.append(rx.icon(icon, size=16))
    style = dict(
        background=t.PRIMARY,
        color="#FFFFFF",
        height="40px",
        padding="0 16px",
        border_radius=t.RADIUS_SM,
        font_size="14px",
        font_weight="600",
        cursor="pointer",
        _hover={"background": t.PRIMARY_HOVER},
    )
    style.update(props)
    return rx.button(*children, **style)


def secondary_button(label, icon: str | None = None, **props) -> rx.Component:
    """Nút phụ viền xám cao 40px."""
    children = [rx.text(label)]
    if icon:
        children.append(rx.icon(icon, size=16))
    style = dict(
        background=t.SURFACE,
        color=t.INK,
        border=f"1px solid {t.BORDER_STRONG}",
        height="40px",
        padding="0 16px",
        border_radius=t.RADIUS_SM,
        font_size="14px",
        font_weight="600",
        cursor="pointer",
        _hover={"background": t.SURFACE_MUTED},
    )
    style.update(props)
    return rx.button(*children, **style)


def text_link(label, href: str | None = None, on_click=None, **props) -> rx.Component:
    """Liên kết chữ có mũi tên (VD: Xem đề xuất →)."""
    style = dict(font_size="13px", font_weight="600", color=t.PRIMARY, cursor="pointer", white_space="nowrap")
    style.update(props)
    if href:
        return rx.link(label, href=href, underline="none", **style)
    return rx.text(label, on_click=on_click, **style)


def page_title(title, subtitle, action: rx.Component | None = None) -> rx.Component:
    """Tiêu đề trang: chữ 32px đậm + dòng mô tả, nút hành động bên phải."""
    return rx.hstack(
        rx.vstack(
            rx.text(title, font_size="32px", font_weight="700", color=t.INK, line_height="41px", letter_spacing="-0.02em"),
            rx.text(subtitle, font_size="14px", color=t.MUTED, line_height="17px"),
            spacing="0",
            gap="6px",
            align_items="start",
        ),
        rx.spacer(),
        action if action is not None else rx.fragment(),
        width="100%",
        align="start",
        margin_bottom="32px",
        wrap="wrap",
        gap="12px",
    )


def kpi_card(title, value, hint, inline_hint: bool = False, tone: str = "neutral") -> rx.Component:
    """Thẻ chỉ số KPI. inline_hint=True: dòng phụ nằm cạnh con số (màn Đề xuất / Lịch sử duyệt)."""
    value_color = {"danger": t.DANGER, "warning": t.WARNING}.get(tone, t.INK)
    number = rx.text(value, font_size="34px", font_weight="700", color=value_color, line_height="42px", letter_spacing="-0.02em")
    hint_el = rx.text(hint, font_size="13px", color=t.MUTED, line_height="16px")
    body = (
        rx.hstack(number, hint_el, align="end", spacing="0", gap="20px", padding_bottom="2px")
        if inline_hint
        else rx.vstack(number, hint_el, spacing="0", gap="4px", align_items="start")
    )
    return card(
        rx.vstack(
            rx.text(title, font_size="14px", font_weight="500", color=t.TEXT),
            body,
            spacing="0",
            gap="6px",
            align_items="start",
        ),
        padding="15px 20px 15px 20px",
        min_height="111px",
    )


def pad2(n) -> rx.Var:
    """Số nguyên dạng 2 chữ số như thiết kế (3 -> '03')."""
    return rx.cond(n < 10, "0" + n.to_string(), n.to_string())


def field_label(text) -> rx.Component:
    return eyebrow(text, font_size="10.5px", margin_bottom="4px")


def input_style() -> dict:
    return dict(
        height="40px",
        border_radius=t.RADIUS_SM,
        background=t.SURFACE,
        font_size="14px",
    )


def table_header(columns: list[tuple[str, str]], **props) -> rx.Component:
    """Hàng tiêu đề bảng nền xám nhạt cao 39px. columns = [(tên cột, độ rộng CSS)]."""
    style = dict(
        width="100%",
        min_width="fit-content",
        height="39px",
        align="center",
        padding_x="15px",
        background=t.SURFACE_MUTED,
        border_radius=t.RADIUS_SM,
        spacing="0",
    )
    style.update(props)
    return rx.hstack(
        *[
            rx.text(name, width=w, flex_shrink="0", font_size="12px", font_weight="600", color=t.MUTED)
            for name, w in columns
        ],
        **style,
    )


def table_row(*cells, height: str = "53px", **props) -> rx.Component:
    style = dict(
        width="100%",
        min_width="fit-content",
        min_height=height,
        align="center",
        padding_x="15px",
        border_bottom=f"1px solid {t.BORDER}",
        spacing="0",
        _hover={"background": t.SURFACE_MUTED},
    )
    style.update(props)
    return rx.hstack(*cells, **style)


def cell(content, width: str, **props) -> rx.Component:
    if isinstance(content, rx.Component):
        return rx.box(content, width=width, flex_shrink="0", **props)
    style = dict(font_size="14px", color=t.INK)
    style.update(props)
    return rx.text(content, width=width, flex_shrink="0", **style)


def underline_tabs(items: list[tuple[str, str]], active, on_select, gap: str = "70px", **props) -> rx.Component:
    """Thanh tab gạch chân (Nguyên liệu / Lô hàng / Giao dịch kho...). items = [(giá trị, nhãn)]."""
    return rx.hstack(
        *[
            rx.box(
                rx.text(
                    label,
                    font_size="15px",
                    font_weight=rx.cond(active == value, "700", "500"),
                    color=rx.cond(active == value, t.INK, t.MUTED),
                ),
                padding="8px 3px 18px 3px",
                border_bottom="3px solid",
                border_color=rx.cond(active == value, t.NAVY, "transparent"),
                margin_bottom="-1px",
                cursor="pointer",
                on_click=on_select(value),
            )
            for value, label in items
        ],
        width="100%",
        spacing="0",
        gap=gap,
        border_bottom=f"1px solid {t.BORDER}",
        overflow_x="auto",
        **props,
    )


def pagination(label, page, total_pages, on_prev, on_next) -> rx.Component:
    """Chân bảng: 'Hiển thị 1–6 / 24' + nút chuyển trang."""
    return rx.hstack(
        rx.text(label, font_size="13px", color=t.MUTED),
        rx.spacer(),
        rx.hstack(
            rx.icon_button(rx.icon("chevron-left", size=16), variant="ghost", color=t.TEXT, on_click=on_prev, disabled=page <= 1, cursor="pointer"),
            rx.text(page.to_string() + " / " + total_pages.to_string(), font_size="14px", color=t.TEXT),
            rx.icon_button(rx.icon("chevron-right", size=16), variant="ghost", color=t.TEXT, on_click=on_next, disabled=page >= total_pages, cursor="pointer"),
            align="center",
            spacing="3",
        ),
        width="100%",
        align="center",
        padding_top="16px",
    )


def empty_state(text: str, icon: str = "inbox") -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon(icon, size=28, color=t.SUBTLE),
            rx.text(text, font_size="14px", color=t.MUTED),
            align="center",
            spacing="2",
        ),
        width="100%",
        padding="40px",
    )


def guardrail(title, body, action: rx.Component | None = None, **props) -> rx.Component:
    """Khối nhắc nhở 'con người quyết định' cuối mỗi trang."""
    return card(
        rx.hstack(
            rx.vstack(
                rx.text(title, font_size="17px", font_weight="700", color=t.INK),
                rx.text(body, font_size="14px", color=t.MUTED),
                spacing="0",
                gap="10px",
                align_items="start",
            ),
            rx.spacer(),
            action if action is not None else rx.fragment(),
            width="100%",
            align="center",
            wrap="wrap",
            gap="12px",
        ),
        **{**dict(background=t.PRIMARY_SOFT, border="1px solid #D5DEF3"), **props},
    )


def info_row(label, value, **props) -> rx.Component:
    return rx.hstack(
        rx.text(label, font_size="14px", color=t.TEXT),
        rx.spacer(),
        rx.text(value, **{**dict(font_size="14px", font_weight="600", color=t.INK, text_align="right"), **props}),
        width="100%",
        align="center",
    )


def divider(**props) -> rx.Component:
    style = dict(height="1px", width="100%", background=t.BORDER, flex_shrink="0")
    style.update(props)
    return rx.box(**style)


def loading_state(text: str = "Đang tải dữ liệu...") -> rx.Component:
    """Trạng thái đang tải: vòng xoay + các dòng khung xám giữ chỗ bảng."""
    return rx.vstack(
        rx.hstack(rx.spinner(size="2"), rx.text(text, font_size="14px", color=t.MUTED), align="center", gap="10px", spacing="0"),
        *[
            rx.box(height="44px", width="100%", border_radius=t.RADIUS_SM, background=t.SURFACE_MUTED, opacity=str(1 - i * 0.2))
            for i in range(4)
        ],
        width="100%",
        spacing="0",
        gap="10px",
        padding="20px 0",
    )


def error_state(title: str, detail, on_retry, extra: rx.Component | None = None) -> rx.Component:
    """Trạng thái lỗi: thông điệp rõ ràng + nút Thử lại (và hành động phụ nếu có)."""
    return rx.center(
        rx.vstack(
            rx.center(rx.icon("cloud-off", size=22, color=t.DANGER), width="44px", height="44px", border_radius="999px", background=t.DANGER_SOFT),
            rx.text(title, font_size="16px", font_weight="600", color=t.INK, text_align="center"),
            rx.text(detail, font_size="13px", color=t.MUTED, text_align="center", max_width="560px", word_break="break-word"),
            rx.hstack(
                secondary_button("Thử lại", icon="rotate-cw", on_click=on_retry),
                extra if extra is not None else rx.fragment(),
                gap="10px",
                spacing="0",
                margin_top="6px",
                wrap="wrap",
                justify="center",
            ),
            align="center",
            spacing="0",
            gap="10px",
        ),
        width="100%",
        padding="36px 20px",
    )
