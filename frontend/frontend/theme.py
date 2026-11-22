"""Design tokens lấy theo bộ thiết kế Figma "DACN" (8 màn hình 1440 x 1040).

Bố cục, kích thước, khoảng cách và nội dung chữ khớp với file Figma.
Màu lấy từ Figma: navy #0E2031 (sidebar, panel), xanh chính #0B6BCB (nút, liên kết),
nhãn #E7EFF6, chữ #15222F / #636B73, viền #D4E1EF, font Be Vietnam Pro.
Muốn đổi màu toàn bộ giao diện chỉ cần sửa các hằng số dưới đây.
"""

FONT_FAMILY = "'Be Vietnam Pro', system-ui, -apple-system, 'Segoe UI', sans-serif"
FONT_URL = "https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap"

# Màu nền & bề mặt
BG = "#F3F6F9"            # nền vùng làm việc
SURFACE = "#FFFFFF"       # thẻ / bảng
SURFACE_MUTED = "#F4F7FA" # tiêu đề bảng, ô nhập
BORDER = "#E3EAF2"
BORDER_STRONG = "#D4E1EF"

# Chữ
INK = "#15222F"           # tiêu đề
TEXT = "#3A4651"          # nội dung
MUTED = "#636B73"         # phụ
SUBTLE = "#8D9BA9"        # nhãn nhỏ, chữ in hoa

# Màu thương hiệu (navy)
NAVY = "#0E2031"          # sidebar, nút chính, panel giới thiệu
NAVY_2 = "#1A2D3F"        # hover / khối nổi trên nền navy
NAVY_3 = "#263B50"
NAVY_TEXT = "#BCC6D0"     # chữ trên nền navy
NAVY_MUTED = "#8D9BA9"
PRIMARY = "#0B6BCB"       # liên kết, điểm nhấn
PRIMARY_SOFT = "#E7EFF6"
PRIMARY_HOVER = "#0959A8"
PRIMARY_TINT = "#F2F7FC"   # nền khối giải trình / ghi chú xanh nhạt

# Trạng thái
DANGER = "#B42318"
DANGER_SOFT = "#FEF3F2"
DANGER_BORDER = "#FECDCA"
WARNING = "#B54708"
WARNING_SOFT = "#FFFAEB"
WARNING_BORDER = "#FEDF89"
SUCCESS = "#067647"
SUCCESS_SOFT = "#ECFDF3"
SUCCESS_BORDER = "#ABEFC6"
INFO = "#175CD3"
INFO_SOFT = "#EFF8FF"
INFO_BORDER = "#B2DDFF"
NEUTRAL_SOFT = "#F2F4F7"

# Kích thước khung (theo Figma)
SIDEBAR_W = "228px"
TOPBAR_H = "76px"
RADIUS = "12px"
RADIUS_SM = "8px"

# Tông màu cho nhãn trạng thái (pill)
TONES = {
    "danger": (DANGER_SOFT, DANGER, DANGER_BORDER),
    "warning": (WARNING_SOFT, WARNING, WARNING_BORDER),
    "success": (SUCCESS_SOFT, SUCCESS, SUCCESS_BORDER),
    "info": (INFO_SOFT, INFO, INFO_BORDER),
    "neutral": (NEUTRAL_SOFT, TEXT, BORDER),
    "navy": (PRIMARY_SOFT, NAVY, "#C8D4F0"),
    "primary": (PRIMARY_SOFT, PRIMARY, "#C9DCF0"),
    "yellow": ("#FEF7C3", "#A15C07", "#FDE272"),
}
