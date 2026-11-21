import reflex as rx


def stat_card(
    title: str,
    value: rx.Var[str | int | float] | str | int,
    hint: str = "",
    icon_name: str = "box",
    tone: str = "primary",
) -> rx.Component:
    """Thẻ thống kê KPI trên Dashboard."""
    # Màu sắc theo tone
    tone_colors = {
        "primary": {"bg": "#EFF6FF", "border": "#BFDBFE", "icon": "#2563EB", "val": "#1E3A8A"},
        "danger": {"bg": "#FEF2F2", "border": "#FECACA", "icon": "#DC2626", "val": "#991B1B"},
        "warning": {"bg": "#FFFBEB", "border": "#FDE68A", "icon": "#D97706", "val": "#92400E"},
        "success": {"bg": "#F0FDF4", "border": "#BBF7D0", "icon": "#16A34A", "val": "#14532D"},
    }
    c = tone_colors.get(tone, tone_colors["primary"])

    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(title, font_size="12px", font_weight="600", color="#64748B", text_transform="uppercase"),
                rx.heading(value, size="7", font_weight="800", color=c["val"]),
                rx.cond(
                    hint != "",
                    rx.text(hint, font_size="12px", color="#64748B", margin_top="2px"),
                    rx.fragment(),
                ),
                spacing="1",
                align_items="start",
            ),
            rx.spacer(),
            rx.box(
                rx.icon(icon_name, size=24, color=c["icon"]),
                background=c["bg"],
                border=f"1px solid {c['border']}",
                padding="10px",
                border_radius="10px",
            ),
            align="start",
            width="100%",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
        box_shadow="0 1px 3px 0 rgba(0, 0, 0, 0.05)",
        border_radius="12px",
        padding="18px",
        width="100%",
    )
