import csv
import io
import math
import os
import typing
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

import httpx
import reflex as rx

from frontend import replenishment as rp
from frontend.permissions import AUTH_ENABLED, CAN_APPROVE, HOME_PAGE, PAGE_ACCESS, ROLE_LABELS, ROLE_SHORT

API_BASE = os.getenv("NEXT_PUBLIC_API_URL", os.getenv("API_URL", "http://localhost:8000/api/v1"))

PAGE_SIZE_INGREDIENTS = 6
PAGE_SIZE_PROPOSALS = 6
PAGE_SIZE_HISTORY = 5

WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

Row = dict[str, typing.Any]


# ==========================================
# HÀM ĐỊNH DẠNG SỐ / TIỀN / NGÀY KIỂU VIỆT NAM
# ==========================================

def _f(v: typing.Any) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def fmt_num(v: typing.Any, decimals: int = 2) -> str:
    """2.5 -> '2,5'; 1250 -> '1.250'; 7.567 -> '7,57'."""
    x = round(_f(v), decimals)
    s = f"{x:,.{decimals}f}"
    if decimals:
        s = s.rstrip("0").rstrip(".")
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_money(v: typing.Any) -> str:
    return fmt_num(round(_f(v)), 0) + " ₫"


def _parse_dt(value: typing.Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", ""))
    except ValueError:
        try:
            return datetime.combine(date.fromisoformat(str(value)[:10]), datetime.min.time())
        except ValueError:
            return None


def fmt_dt(value: typing.Any) -> str:
    d = _parse_dt(value)
    return d.strftime("%d/%m/%Y · %H:%M") if d else "—"


def fmt_date(value: typing.Any) -> str:
    d = _parse_dt(value)
    return d.strftime("%d/%m/%Y") if d else "—"


def short_name(name: str) -> str:
    """Rút gọn tên nguyên liệu dài cho các dòng tóm tắt."""
    words = str(name or "").split()
    return " ".join(words[:4]) if len(words) > 4 else str(name or "")


def proposal_code(p: Row) -> str:
    d = _parse_dt(p.get("ngay_tao"))
    prefix = d.strftime("%d%m") if d else "0000"
    return f"DX-{prefix}-{int(p.get('ma_phieu_de_xuat', 0)):03d}"


INGREDIENT_STATUS = {
    "NGUY_CO_THIEU": ("Thiếu hàng", "danger"),
    "TON_DU": ("Tồn dư", "yellow"),
    "CHAM_NGUONG": ("Chạm ngưỡng", "warning"),
    "AN_TOAN": ("Đủ hàng", "primary"),
}

PROPOSAL_STATUS = {
    "CHO_DUYET": ("Chờ duyệt", "yellow"),
    "DA_DUYET": ("Đã duyệt", "primary"),
    "DA_SUA": ("Đã sửa", "warning"),
    "TU_CHOI": ("Từ chối", "danger"),
}

ACTION_LABELS = {
    "APPROVE": ("Phê duyệt", "primary"),
    "MODIFY": ("Điều chỉnh", "warning"),
    "REJECT": ("Từ chối", "danger"),
}

TRANSACTION_TYPES = {
    "NHAP": ("Nhập kho", "+"),
    "XUAT_BAN": ("Xuất bán (BOM)", "−"),
    "HAO_HUT": ("Hao hụt", "−"),
    "KIEM_KE": ("Kiểm kê", "±"),
}

CATEGORY_PRESETS = ["Cà phê", "Sữa & Kem", "Siro & Xốt", "Bột & Topping", "Trà", "Bao bì"]
UNIT_PRESETS = ["kg", "hộp", "lon", "chai", "túi", "cái"]
DISCRETE_UNITS = {"chai", "hộp", "lon", "cái", "túi", "gói", "chiếc", "ly", "thùng"}


def _is_discrete_unit(unit: str) -> bool:
    return str(unit or "").strip().lower() in DISCRETE_UNITS


def _round_half_up(v: typing.Any) -> int:
    """Làm tròn số nguyên chuẩn (>= 0.5 làm tròn lên, < 0.5 làm tròn xuống)."""
    x = _f(v)
    if not math.isfinite(x):
        return 0
    return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _qty_for_unit(v: typing.Any, unit: str, decimals: int = 2) -> float:
    """Đơn vị đóng gói rời rạc (chai, hộp, lon, cái, túi...) làm tròn số nguyên; đơn vị cân/đo giữ thập phân."""
    if _is_discrete_unit(unit):
        return float(_round_half_up(v))
    return round(_f(v), decimals)


def fmt_qty(v: typing.Any, unit: str, decimals: int = 2) -> str:
    """Định dạng số lượng theo đơn vị: đơn vị rời rạc hiển thị số nguyên (>= 0,5 lên; < 0,5 xuống)."""
    if _is_discrete_unit(unit):
        return fmt_num(_round_half_up(v), 0)
    return fmt_num(v, decimals)


def _round_restock_qty(qty: float, unit: str) -> float:
    """Làm tròn lên số nguyên cho đơn vị đóng gói rời rạc (chai, hộp, lon, cái, túi...)."""
    if _is_discrete_unit(unit):
        return float(math.ceil(max(qty, 1.0)))
    return round(max(qty, 0.5), 2)


def _fmt_input_num(val: typing.Any) -> str:
    """Hiển thị gọn trong ô input: 5.0 -> '5', 19.5 -> '19.5'."""
    x = _f(val)
    return str(int(x)) if x == int(x) else str(round(x, 2))

INGREDIENT_CATALOG_PRESETS: list[dict[str, str]] = [
    {"ten_nguyen_lieu": "Sữa yến mạch Oatside Barista 1L", "danh_muc": "Sữa & Kem", "don_vi_tinh": "hộp", "muc_ton_an_toan": "12", "muc_ton_toi_da": "60", "ton_kho_hien_tai": "24"},
    {"ten_nguyen_lieu": "Kem béo thực vật Rich's 454g", "danh_muc": "Sữa & Kem", "don_vi_tinh": "hộp", "muc_ton_an_toan": "10", "muc_ton_toi_da": "40", "ton_kho_hien_tai": "15"},
    {"ten_nguyen_lieu": "Siro Vani Monin 700ml", "danh_muc": "Siro & Xốt", "don_vi_tinh": "chai", "muc_ton_an_toan": "4", "muc_ton_toi_da": "20", "ton_kho_hien_tai": "6"},
    {"ten_nguyen_lieu": "Siro Caramel Torani 750ml", "danh_muc": "Siro & Xốt", "don_vi_tinh": "chai", "muc_ton_an_toan": "4", "muc_ton_toi_da": "20", "ton_kho_hien_tai": "6"},
    {"ten_nguyen_lieu": "Đường nước Hàn Quốc 1L", "danh_muc": "Siro & Xốt", "don_vi_tinh": "chai", "muc_ton_an_toan": "8", "muc_ton_toi_da": "30", "ton_kho_hien_tai": "12"},
    {"ten_nguyen_lieu": "Bột Kem Muối Biển Pha Chế", "danh_muc": "Bột & Topping", "don_vi_tinh": "kg", "muc_ton_an_toan": "3", "muc_ton_toi_da": "15", "ton_kho_hien_tai": "5"},
    {"ten_nguyen_lieu": "Trân châu trắng 3Q 2kg", "danh_muc": "Bột & Topping", "don_vi_tinh": "túi", "muc_ton_an_toan": "5", "muc_ton_toi_da": "25", "ton_kho_hien_tai": "10"},
    {"ten_nguyen_lieu": "Trà Nhài Lài Đặc Biệt Bảo Lộc", "danh_muc": "Trà", "don_vi_tinh": "kg", "muc_ton_an_toan": "5", "muc_ton_toi_da": "30", "ton_kho_hien_tai": "10"},
    {"ten_nguyen_lieu": "Nắp cầu nhựa PET phi 95", "danh_muc": "Bao bì", "don_vi_tinh": "cái", "muc_ton_an_toan": "500", "muc_ton_toi_da": "5000", "ton_kho_hien_tai": "1500"},
    {"ten_nguyen_lieu": "Túi chữ T đựng ly mang đi", "danh_muc": "Bao bì", "don_vi_tinh": "kg", "muc_ton_an_toan": "5", "muc_ton_toi_da": "30", "ton_kho_hien_tai": "10"},
]


def ingredient_status_key(i: Row) -> str:
    """Thêm mức 'Chạm ngưỡng' (an toàn nhưng sát điểm đặt hàng lại) như thiết kế."""
    status = i.get("tinh_trang", "AN_TOAN")
    if status == "AN_TOAN" and _f(i.get("ton_kho_hien_tai")) <= _f(i.get("diem_dat_hang_lai_rop")) * 1.25:
        return "CHAM_NGUONG"
    return status


def enrich_ingredient(i: Row) -> Row:
    unit = i.get("don_vi_tinh", "")
    key = ingredient_status_key(i)
    label, tone = INGREDIENT_STATUS.get(key, INGREDIENT_STATUS["AN_TOAN"])
    return {
        **i,
        "ma": str(i.get("ma_nguyen_lieu", "")),
        "ton_fmt": fmt_qty(i.get("ton_kho_hien_tai"), unit),
        "an_toan_fmt": fmt_qty(i.get("muc_ton_an_toan"), unit),
        "rop_fmt": fmt_qty(i.get("diem_dat_hang_lai_rop"), unit),
        "du_bao_fmt": fmt_qty(i.get("nhu_cau_du_bao_7ngay"), unit),
        "bo_sung_fmt": fmt_qty(i.get("so_luong_can_bo_sung"), unit) + " " + unit,
        "status_key": key,
        "status_label": label,
        "tone": tone,
    }


def enrich_proposal(p: Row) -> Row:
    details = p.get("details", []) or []
    names = [short_name(d.get("ten_nguyen_lieu", "")) for d in details]
    summary = ", ".join(names[:2]) + (f" +{len(names) - 2}" if len(names) > 2 else "")
    suppliers = {d.get("ma_nha_cung_cap") for d in details}
    label, tone = PROPOSAL_STATUS.get(p.get("trang_thai", ""), ("Không rõ", "neutral"))
    lines = []
    for d in details:
        unit = d.get("don_vi_tinh", "")
        lines.append({
            "ten": d.get("ten_nguyen_lieu", ""),
            "ncc": d.get("ten_nha_cung_cap", "") or "",
            "so_luong": fmt_qty(d.get("so_luong_de_xuat"), unit) + " " + unit,
            "don_gia": fmt_money(d.get("don_gia_du_kien")),
            "thanh_tien": fmt_money(d.get("thanh_tien")),
            "ly_do": d.get("ly_do_de_xuat") or "",
        })
    return {
        "id": int(p.get("ma_phieu_de_xuat", 0)),
        "code": proposal_code(p),
        "created": fmt_dt(p.get("ngay_tao")),
        "created_raw": str(p.get("ngay_tao") or ""),
        "summary": summary or "—",
        "total": _f(p.get("tong_tien_du_kien")),
        "total_fmt": fmt_money(p.get("tong_tien_du_kien")),
        "status": p.get("trang_thai", ""),
        "status_label": label,
        "tone": tone,
        "reason": p.get("ly_do_tong_quan") or "",
        "creator": p.get("nguoi_tao") or "AI Procurement Agent",
        "n_items": len(details),
        "n_suppliers": len(suppliers),
        "lines": lines,
        "history": p.get("approval_history", []) or [],
    }


class State(rx.State):
    """Trạng thái ứng dụng Frontend Reflex, đồng bộ dữ liệu với FastAPI Backend."""

    # Kết nối & thông báo
    backend_online: bool = True
    error_message: str = ""
    is_loading: bool = False
    last_updated: str = ""

    # Dữ liệu gốc từ API
    stats: Row = {
        "tong_nguyen_lieu_dang_dung": 0,
        "nguy_co_thieu_hang": 0,
        "nguy_co_ton_du": 0,
        "phieu_cho_duyet": 0,
        "tong_gia_tri_ton_kho": 0.0,
        "ty_le_an_toan": 100.0,
    }
    alerts: list[Row] = []
    forecast_summary: list[Row] = []
    ingredients: list[Row] = []
    batches: list[Row] = []
    transactions: list[Row] = []
    suppliers: list[Row] = []
    proposals: list[Row] = []

    # Dự báo
    selected_forecast_id: str = ""

    # Quản lý kho
    active_tab_inventory: str = "nguyen-lieu"
    ingredient_search: str = ""
    ingredient_status_filter: str = "ALL"
    ingredient_page: int = 1
    only_expiring_batches: bool = False

    # Dialog nguyên liệu (thêm / sửa / nhập thêm nhanh từ đề xuất)
    ing_dialog_open: bool = False
    ing_edit_id: int = 0
    ing_restock_id: int = 0
    ing_preset_selected: str = ""
    ing_form: dict[str, str] = {}
    ing_delete_id: int = 0
    ing_delete_name: str = ""

    # Dialog nhập / xuất kho
    tx_dialog_open: bool = False
    tx_form: dict[str, str] = {}

    # Nhà cung cấp
    active_tab_suppliers: str = "lua-chon"
    compare_ingredient_id: str = ""
    compare_qty: str = ""
    compare_result: Row = {}
    supplier_dialog_open: bool = False
    supplier_form: dict[str, str] = {}

    # Tuần 7: kế hoạch bổ sung (ROP, Safety Stock, NCC được chọn)
    rop_plan: list[Row] = []
    rop_status: str = "idle"  # idle | loading | ok | error
    rop_source: str = ""      # api | derived | mock
    rop_error: str = ""
    rop_only_need: bool = False
    creating_proposal_id: int = 0

    # Đề xuất mua hàng
    proposal_filter: str = "ALL"
    proposal_search: str = ""
    proposal_page: int = 1
    generating: bool = False
    current_proposal: Row = {}
    proposal_comment: str = ""
    acting: bool = False

    # Lịch sử duyệt
    history_search: str = ""
    history_action_filter: str = "ALL"
    history_page: int = 1

    # Đăng nhập & phân quyền (lưu ở trình duyệt để F5 không bị mất phiên)
    token: str = rx.LocalStorage("", name="dacn_token")
    user_name: str = rx.LocalStorage("", name="dacn_user_name")
    user_email: str = rx.LocalStorage("", name="dacn_user_email")
    user_role: str = rx.LocalStorage("", name="dacn_user_role")
    login_email: str = ""
    login_password: str = ""
    show_password: bool = False
    remember_me: bool = True
    login_error: str = ""
    login_loading: bool = False
    session_expired: bool = False
    auth_enabled: bool = AUTH_ENABLED

    # ==========================================
    # HẠ TẦNG GỌI API
    # ==========================================

    def _client(self) -> httpx.AsyncClient:
        """HTTP client gửi kèm JWT; nếu Backend trả 401 thì đánh dấu phiên đã hết hạn."""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        async def _flag_401(response: httpx.Response) -> None:
            if response.status_code == 401:
                self.session_expired = True

        return httpx.AsyncClient(
            base_url=API_BASE,
            timeout=45.0,
            headers=headers,
            event_hooks={"response": [_flag_401]},
        )

    async def _get(self, client: httpx.AsyncClient, path: str, params: dict | None = None):
        res = await client.get(path, params=params)
        if res.status_code == 200:
            return res.json()
        return None

    def _offline(self, e: Exception):
        self.backend_online = False
        self.error_message = f"Không thể kết nối FastAPI backend ({API_BASE}). Hãy bật Backend rồi tải lại trang. Chi tiết: {e}"

    def _mark_updated(self):
        self.backend_online = True
        self.error_message = ""
        self.last_updated = datetime.now().strftime("%H:%M")

    def _allowed(self, path: str) -> bool:
        if not AUTH_ENABLED:
            return True
        if not self.token:
            return False
        roles = PAGE_ACCESS.get(path)
        return roles is None or self.user_role in roles

    def _force_logout(self):
        self.token = ""
        self.user_name = ""
        self.user_email = ""
        self.user_role = ""
        self.session_expired = False
        return [rx.toast.warning("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại."), rx.redirect("/login")]

    # ==========================================
    # ĐĂNG NHẬP / ĐĂNG XUẤT / PHÂN QUYỀN
    # ==========================================

    def set_login_email(self, val: str):
        self.login_email = val

    def set_login_password(self, val: str):
        self.login_password = val

    def toggle_show_password(self):
        self.show_password = not self.show_password

    def set_remember_me(self, val: bool):
        self.remember_me = val

    def fill_demo_account(self, email: str):
        """Điền nhanh tài khoản mẫu trong README (phục vụ demo)."""
        self.login_email = email
        self.login_password = "admin123"
        self.login_error = ""

    def forgot_password(self):
        return rx.toast.info("Vui lòng liên hệ Quản trị hệ thống để cấp lại mật khẩu.")

    async def handle_login(self, form_data: dict):
        """Gọi POST /auth/login, lưu JWT + thông tin người dùng rồi chuyển tới trang phù hợp vai trò."""
        email = self.login_email.strip()
        if not email or not self.login_password:
            self.login_error = "Vui lòng nhập email và mật khẩu."
            return
        self.login_loading = True
        self.login_error = ""
        yield
        try:
            async with httpx.AsyncClient(base_url=API_BASE, timeout=10.0) as client:
                res = await client.post("/auth/login", json={"email": email, "mat_khau": self.login_password})
            if res.status_code == 200:
                data = res.json()
                user = data.get("user", {})
                self.token = data.get("access_token", "")
                self.user_name = user.get("ten_nguoi_dung", "")
                self.user_email = user.get("email", email)
                self.user_role = user.get("vai_tro", "")
                self.login_password = ""
                self.backend_online = True
                yield rx.redirect(HOME_PAGE.get(self.user_role, "/inventory"))
            elif res.status_code == 401:
                self.login_error = "Email hoặc mật khẩu không chính xác."
            else:
                self.login_error = f"Đăng nhập thất bại (mã {res.status_code})."
        except Exception:
            self.backend_online = False
            self.login_error = f"Không kết nối được máy chủ ({API_BASE}). Hãy bật FastAPI Backend."
        finally:
            self.login_loading = False

    def logout(self):
        self.token = ""
        self.user_name = ""
        self.user_email = ""
        self.user_role = ""
        self.login_password = ""
        return rx.redirect("/login")

    def require_access(self):
        """on_load của mọi trang nội bộ: chưa đăng nhập -> /login; sai vai trò -> về trang của mình."""
        if not AUTH_ENABLED:
            return
        if not self.token:
            return rx.redirect("/login")
        path = self.router.route_id or "/"
        if not self._allowed(path):
            return [
                rx.toast.error("Tài khoản của bạn không có quyền truy cập trang này."),
                rx.redirect(HOME_PAGE.get(self.user_role, "/inventory")),
            ]

    def redirect_if_logged_in(self):
        if not AUTH_ENABLED:
            return rx.redirect("/dashboard")
        if self.token:
            return rx.redirect(HOME_PAGE.get(self.user_role, "/inventory"))

    @rx.var
    def is_logged_in(self) -> bool:
        return True if not AUTH_ENABLED else bool(self.token)

    @rx.var
    def display_name(self) -> str:
        return self.user_name or "Quản lý cửa hàng"

    @rx.var
    def role_label(self) -> str:
        if not AUTH_ENABLED:
            return "Chế độ demo · tắt đăng nhập"
        return ROLE_LABELS.get(self.user_role, "Chưa đăng nhập")

    @rx.var
    def short_role(self) -> str:
        if not AUTH_ENABLED:
            return "Quản lý"
        return ROLE_SHORT.get(self.user_role, "Khách")

    @rx.var
    def allowed_pages(self) -> list[str]:
        if not AUTH_ENABLED:
            return list(PAGE_ACCESS.keys())
        return [path for path, roles in PAGE_ACCESS.items() if self.user_role in roles]

    @rx.var
    def can_approve(self) -> bool:
        if not AUTH_ENABLED:
            return True
        return self.user_role in CAN_APPROVE

    # ==========================================
    # TẢI DỮ LIỆU THEO TRANG
    # ==========================================

    async def load_dashboard(self):
        """Tổng quan: thẻ KPI, cảnh báo, dự báo 7 ngày, nguyên liệu cần theo dõi, đề xuất chờ duyệt."""
        if not self._allowed("/dashboard"):
            return
        self.is_loading = True
        try:
            async with self._client() as client:
                self.stats = await self._get(client, "/dashboard/stats") or self.stats
                self.alerts = await self._get(client, "/dashboard/alerts") or []
                self.forecast_summary = await self._get(client, "/dashboard/forecast-summary") or []
                self.ingredients = await self._get(client, "/ingredients") or []
                self.proposals = await self._get(client, "/proposals") or []
            self._pick_default_forecast()
            self._mark_updated()
        except Exception as e:
            self._offline(e)
        finally:
            self.is_loading = False
        if self.session_expired:
            return self._force_logout()

    async def load_forecast(self):
        if not self._allowed("/forecast"):
            return
        self.is_loading = True
        try:
            async with self._client() as client:
                self.forecast_summary = await self._get(client, "/dashboard/forecast-summary") or []
                self.ingredients = await self._get(client, "/ingredients") or []
                self.stats = await self._get(client, "/dashboard/stats") or self.stats
            self._pick_default_forecast()
            self._mark_updated()
        except Exception as e:
            self._offline(e)
        finally:
            self.is_loading = False
        if self.session_expired:
            return self._force_logout()

    def _pick_default_forecast(self):
        ids = {str(i.get("ma_nguyen_lieu")) for i in self.forecast_summary}
        if self.forecast_summary and self.selected_forecast_id not in ids:
            # Ưu tiên nguyên liệu đang thiếu hàng, sau đó tới nguyên liệu có dự báo thật từ mô hình
            danger = [str(i.get("ma_nguyen_lieu")) for i in self.ingredients if i.get("tinh_trang") == "NGUY_CO_THIEU"]
            danger += [str(a.get("ma_nguyen_lieu")) for a in self.alerts if a.get("muc_do") == "DANGER"]
            pick = next((d for d in danger if d in ids), "")
            if not pick:
                real = [i for i in self.forecast_summary if not i.get("la_du_lieu_uoc_tinh")]
                pick = str((real or self.forecast_summary)[0].get("ma_nguyen_lieu", ""))
            self.selected_forecast_id = pick

    async def load_inventory(self):
        if not self._allowed("/inventory"):
            return
        self.is_loading = True
        try:
            async with self._client() as client:
                self.ingredients = await self._get(client, "/ingredients") or []
                params = {"canh_bao_het_han": "true"} if self.only_expiring_batches else None
                self.batches = await self._get(client, "/inventory/batches", params) or []
                self.transactions = await self._get(client, "/inventory/transactions") or []
                self.stats = await self._get(client, "/dashboard/stats") or self.stats
            self._mark_updated()
        except Exception as e:
            self._offline(e)
        finally:
            self.is_loading = False
        if self.session_expired:
            return self._force_logout()

    async def load_suppliers(self):
        if not self._allowed("/suppliers"):
            return
        self.is_loading = True
        try:
            async with self._client() as client:
                self.suppliers = await self._get(client, "/suppliers") or []
                self.ingredients = await self._get(client, "/ingredients") or []
                self.stats = await self._get(client, "/dashboard/stats") or self.stats
                quoted = sorted({str(q.get("ma_nguyen_lieu")) for s in self.suppliers for q in s.get("quotations", [])})
                if quoted and self.compare_ingredient_id not in quoted:
                    shortage = [str(i.get("ma_nguyen_lieu")) for i in self.ingredients if i.get("tinh_trang") == "NGUY_CO_THIEU"]
                    self.compare_ingredient_id = next((x for x in shortage if x in quoted), quoted[0])
                    self.compare_qty = ""
                if self.compare_ingredient_id:
                    self.compare_result = await self._get(client, f"/suppliers/compare/{self.compare_ingredient_id}") or {}
            if not self.compare_qty:
                self.compare_qty = self._default_qty(self.compare_ingredient_id)
            self._mark_updated()
        except Exception as e:
            self._offline(e)
        finally:
            self.is_loading = False
        if self.session_expired:
            return self._force_logout()

    def _default_qty(self, ingredient_id: str) -> str:
        for i in self.ingredients:
            if str(i.get("ma_nguyen_lieu")) == ingredient_id:
                unit = i.get("don_vi_tinh", "")
                need = _f(i.get("so_luong_can_bo_sung")) or _f(i.get("nhu_cau_du_bao_7ngay"))
                return fmt_qty(need, unit)
        return "1"

    async def load_proposals(self):
        if not self._allowed("/proposals"):
            return
        self.is_loading = True
        try:
            async with self._client() as client:
                self.proposals = await self._get(client, "/proposals") or []
                self.stats = await self._get(client, "/dashboard/stats") or self.stats
            self._mark_updated()
        except Exception as e:
            self._offline(e)
        finally:
            self.is_loading = False
        if self.session_expired:
            return self._force_logout()

    async def load_proposal_detail(self):
        if not self._allowed("/proposals/[ma_phieu]"):
            return
        raw = str(self.router.url.path or "").rstrip("/").split("/")[-1]
        self.current_proposal = {}
        self.proposal_comment = ""
        if not raw.isdigit():
            return rx.redirect("/proposals")
        self.is_loading = True
        try:
            async with self._client() as client:
                data = await self._get(client, f"/proposals/{raw}")
                self.stats = await self._get(client, "/dashboard/stats") or self.stats
            if data is None:
                self.is_loading = False
                return [rx.toast.error(f"Không tìm thấy phiếu đề xuất #{raw}."), rx.redirect("/proposals")]
            self.current_proposal = enrich_proposal(data)
            self._mark_updated()
        except Exception as e:
            self._offline(e)
        finally:
            self.is_loading = False
        if self.session_expired:
            return self._force_logout()

    async def load_history(self):
        if not self._allowed("/history"):
            return
        await self.load_proposals()

    # ==========================================
    # TỔNG QUAN (DASHBOARD)
    # ==========================================

    @rx.var
    def pending_proposals_count(self) -> int:
        return int(self.stats.get("phieu_cho_duyet", 0) or 0)

    @rx.var
    def today_text(self) -> str:
        now = datetime.now()
        text = f"{WEEKDAYS[now.weekday()]}, {now.day} tháng {now.month}, {now.year}"
        if self.last_updated:
            text += f"  ·  Cập nhật gần nhất {self.last_updated}"
        return text

    @rx.var
    def today_short(self) -> str:
        now = datetime.now()
        return f"{now:%d/%m} · {self.last_updated or now.strftime('%H:%M')}"

    @rx.var
    def kpi_tracked(self) -> str:
        return f"{int(self.stats.get('tong_nguyen_lieu_dang_dung', 0) or 0):02d}"

    @rx.var
    def kpi_tracked_hint(self) -> str:
        total = int(self.stats.get("tong_nguyen_lieu_dang_dung", 0) or 0)
        bad = int(self.stats.get("nguy_co_thieu_hang", 0) or 0) + int(self.stats.get("nguy_co_ton_du", 0) or 0)
        return f"{max(total - bad, 0)} nguyên liệu ở mức đủ"

    @rx.var
    def kpi_shortage(self) -> str:
        return f"{int(self.stats.get('nguy_co_thieu_hang', 0) or 0):02d}"

    @rx.var
    def kpi_shortage_hint(self) -> str:
        return "Cần bổ sung sớm" if int(self.stats.get("nguy_co_thieu_hang", 0) or 0) else "Không có nguyên liệu thiếu"

    @rx.var
    def kpi_overstock(self) -> str:
        return f"{int(self.stats.get('nguy_co_ton_du', 0) or 0):02d}"

    @rx.var
    def kpi_overstock_hint(self) -> str:
        over = [i for i in self.ingredients if i.get("tinh_trang") == "TON_DU"]
        if over:
            return f"{short_name(over[0].get('ten_nguyen_lieu', ''))} vượt nhu cầu"
        return "Không có tồn dư đọng vốn"

    @rx.var
    def kpi_pending(self) -> str:
        return f"{self.pending_proposals_count:02d}"

    @rx.var
    def pending_total_fmt(self) -> str:
        total = sum(_f(p.get("tong_tien_du_kien")) for p in self.proposals if p.get("trang_thai") == "CHO_DUYET")
        return fmt_money(total)

    @rx.var
    def shortage_names(self) -> str:
        names = [short_name(a.get("ten_nguyen_lieu", "")) for a in self.alerts if a.get("loai_canh_bao") == "NGUY_CO_THIEU"]
        if not names:
            return ""
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]} và {names[1]}"
        return f"{names[0]}, {names[1]} và {len(names) - 2} nguyên liệu khác"

    @rx.var
    def watchlist_rows(self) -> list[Row]:
        """4 nguyên liệu cần theo dõi nhất: thiếu hàng -> chạm ngưỡng -> tồn dư."""
        order = {"NGUY_CO_THIEU": 0, "CHAM_NGUONG": 1, "TON_DU": 2, "AN_TOAN": 3}
        rows = [enrich_ingredient(i) for i in self.ingredients]
        rows.sort(key=lambda r: (order.get(r["status_key"], 9), _f(r.get("ton_kho_hien_tai")) / max(_f(r.get("diem_dat_hang_lai_rop")), 1)))
        return rows[:4]

    @rx.var
    def ai_reco(self) -> Row:
        """Nội dung thẻ AI Procurement Agent: nguyên liệu thiếu nghiêm trọng nhất."""
        shortage = [i for i in self.ingredients if i.get("tinh_trang") == "NGUY_CO_THIEU"]
        if not shortage:
            return {"has": False, "text": "Tồn kho đang ở mức an toàn. AI sẽ tự đề xuất khi có nguyên liệu chạm điểm đặt hàng lại.", "href": "/proposals"}
        i = min(shortage, key=lambda x: _f(x.get("ton_kho_hien_tai")) / max(_f(x.get("diem_dat_hang_lai_rop")), 1))
        unit = i.get("don_vi_tinh", "")
        text = (
            f"{short_name(i.get('ten_nguyen_lieu', ''))} chỉ còn {fmt_qty(i.get('ton_kho_hien_tai'), unit)} {unit}, "
            f"trong khi nhu cầu 7 ngày tới là {fmt_qty(i.get('nhu_cau_du_bao_7ngay'), unit)} {unit}. "
            f"Đề xuất mua {fmt_qty(i.get('so_luong_can_bo_sung'), unit)} {unit} để duy trì tồn an toàn {fmt_qty(i.get('muc_ton_an_toan'), unit)} {unit}."
        )
        pending = [p for p in self.proposals if p.get("trang_thai") == "CHO_DUYET"]
        href = f"/proposals/{pending[0].get('ma_phieu_de_xuat')}" if pending else "/proposals"
        return {"has": True, "text": text, "href": href}

    # ==========================================
    # DỰ BÁO NHU CẦU
    # ==========================================

    def set_selected_forecast(self, val: str):
        self.selected_forecast_id = val

    @rx.var
    def forecast_options(self) -> list[dict[str, str]]:
        return [
            {"value": str(i.get("ma_nguyen_lieu", "")), "label": str(i.get("ten_nguyen_lieu", ""))}
            for i in self.forecast_summary
        ]

    @rx.var
    def active_forecast_info(self) -> Row:
        for item in self.forecast_summary:
            if str(item.get("ma_nguyen_lieu")) == str(self.selected_forecast_id):
                return item
        return self.forecast_summary[0] if self.forecast_summary else {}

    @rx.var
    def active_forecast_unit(self) -> str:
        return str(self.active_forecast_info.get("don_vi_tinh", ""))

    @rx.var
    def active_forecast_name(self) -> str:
        return str(self.active_forecast_info.get("ten_nguyen_lieu", "—"))

    @rx.var
    def active_forecast_data(self) -> list[Row]:
        """Điểm dữ liệu biểu đồ: kèm nhãn 'T+n' và nhãn giá trị '2,1 kg' / '10 chai'."""
        unit = self.active_forecast_unit
        discrete = _is_discrete_unit(unit)
        rows = []
        for idx, p in enumerate(self.active_forecast_info.get("du_lieu_7ngay", []) or []):
            conf = _f(p.get("do_tin_cay"))
            qty = _qty_for_unit(p.get("so_luong"), unit, 2)
            rows.append({
                "ngay": p.get("ngay", ""),
                "t": f"T+{idx + 1}",
                "so_luong": int(qty) if discrete else qty,
                "nhan": f"{fmt_qty(p.get('so_luong'), unit, 1)} {unit}",
                "do_tin_cay_pct": round(conf * 100 if conf <= 1 else conf),
            })
        return rows

    @rx.var
    def forecast_total_fmt(self) -> str:
        unit = self.active_forecast_unit
        return f"{fmt_qty(self.active_forecast_info.get('tong_nhu_cau_7ngay'), unit, 1)} {unit}"

    @rx.var
    def forecast_avg_fmt(self) -> str:
        unit = self.active_forecast_unit
        return f"{fmt_qty(self.active_forecast_info.get('trung_binh_ngay'), unit, 2)} {unit}"

    @rx.var
    def forecast_confidence(self) -> str:
        vals = [p["do_tin_cay_pct"] for p in self.active_forecast_data]
        return f"{round(sum(vals) / len(vals))}%" if vals else "—"

    @rx.var
    def forecast_peak_day(self) -> str:
        data = self.active_forecast_data
        return max(data, key=lambda p: p["so_luong"])["ngay"] if data else "—"

    @rx.var
    def forecast_period(self) -> str:
        data = self.active_forecast_data
        if not data:
            return "—"
        year = datetime.now().year
        return f"{data[0]['ngay']}/{year} – {data[-1]['ngay']}/{year}"

    @rx.var
    def forecast_method(self) -> str:
        return str(self.active_forecast_info.get("phuong_phap") or "Chưa rõ")

    @rx.var
    def forecast_is_estimate(self) -> bool:
        return bool(self.active_forecast_info.get("la_du_lieu_uoc_tinh", False))

    @rx.var
    def forecast_note(self) -> str:
        data = self.active_forecast_data
        if len(data) < 2:
            return "Chưa đủ dữ liệu để nhận định xu hướng."
        first, last = data[0]["so_luong"], max(p["so_luong"] for p in data[-3:])
        if last > first * 1.05:
            return "Nhu cầu tăng vào cuối kỳ dự báo."
        if last < first * 0.95:
            return "Nhu cầu giảm dần trong kỳ dự báo."
        return "Nhu cầu ổn định trong 7 ngày tới."

    @rx.var
    def replenishment(self) -> Row:
        """Từ dự báo đến lượng cần mua: nhu cầu 7 ngày + tồn an toàn − tồn hiện tại − hàng đang về."""
        unit = self.active_forecast_unit
        demand = _qty_for_unit(self.active_forecast_info.get("tong_nhu_cau_7ngay"), unit, 2)
        ing = next((i for i in self.ingredients if str(i.get("ma_nguyen_lieu")) == str(self.selected_forecast_id)), {})
        safety = _qty_for_unit(ing.get("muc_ton_an_toan"), unit, 2)
        current = _qty_for_unit(ing.get("ton_kho_hien_tai"), unit, 2)
        incoming = 0.0
        need = _qty_for_unit(max(demand + safety - current - incoming, 0), unit, 2)
        return {
            "demand": f"{fmt_qty(demand, unit)} {unit}",
            "safety": f"+ {fmt_qty(safety, unit)} {unit}",
            "current": f"− {fmt_qty(current, unit)} {unit}",
            "incoming": f"− {fmt_qty(incoming, unit)} {unit}",
            "need": f"= {fmt_qty(need, unit)} {unit}",
        }

    def export_forecast(self):
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Nguyên liệu", "Ngày", "Nhu cầu dự báo", "Đơn vị", "Độ tin cậy (%)", "Phương pháp"])
        for item in self.forecast_summary:
            unit = item.get("don_vi_tinh", "")
            discrete = _is_discrete_unit(unit)
            for p in item.get("du_lieu_7ngay", []) or []:
                conf = _f(p.get("do_tin_cay"))
                qty = _qty_for_unit(p.get("so_luong"), unit, 2)
                w.writerow([item.get("ten_nguyen_lieu"), p.get("ngay"), int(qty) if discrete else qty, unit,
                            round(conf * 100 if conf <= 1 else conf), item.get("phuong_phap")])
        return rx.download(data="﻿" + buf.getvalue(), filename="bao_cao_du_bao_7_ngay.csv")

    # ==========================================
    # QUẢN LÝ KHO
    # ==========================================

    def set_inventory_tab(self, tab: str):
        self.active_tab_inventory = tab

    def set_ingredient_search(self, val: str):
        self.ingredient_search = val
        self.ingredient_page = 1

    def set_status_filter(self, val: str):
        self.ingredient_status_filter = val
        self.ingredient_page = 1

    def prev_ingredient_page(self):
        self.ingredient_page = max(1, self.ingredient_page - 1)

    def next_ingredient_page(self):
        self.ingredient_page = min(self.ingredient_total_pages, self.ingredient_page + 1)

    async def toggle_expiring_batches(self, val: bool):
        self.only_expiring_batches = val
        return State.load_inventory

    @rx.var
    def filtered_ingredients(self) -> list[Row]:
        q = self.ingredient_search.strip().lower()
        rows = []
        for i in self.ingredients:
            r = enrich_ingredient(i)
            if q and q not in str(r.get("ten_nguyen_lieu", "")).lower() and q != r["ma"] and f"#{r['ma']}" != q:
                continue
            if self.ingredient_status_filter != "ALL" and r["status_key"] != self.ingredient_status_filter:
                continue
            rows.append(r)
        return rows

    @rx.var
    def ingredient_total_pages(self) -> int:
        return max(1, math.ceil(len(self.filtered_ingredients) / PAGE_SIZE_INGREDIENTS))

    @rx.var
    def ingredient_page_rows(self) -> list[Row]:
        start = (self.ingredient_page - 1) * PAGE_SIZE_INGREDIENTS
        return self.filtered_ingredients[start:start + PAGE_SIZE_INGREDIENTS]

    @rx.var
    def ingredient_page_label(self) -> str:
        total = len(self.filtered_ingredients)
        if not total:
            return "Không có nguyên liệu phù hợp"
        start = (self.ingredient_page - 1) * PAGE_SIZE_INGREDIENTS + 1
        end = min(start + PAGE_SIZE_INGREDIENTS - 1, total)
        return f"Hiển thị {start}–{end} / {total} nguyên liệu"

    @rx.var
    def batch_rows(self) -> list[Row]:
        rows = []
        for b in self.batches:
            days = b.get("so_ngay_con_han")
            if days is not None and int(days) < 0:
                label, tone = "Đã hết hạn", "danger"
            elif b.get("canh_bao_het_han"):
                label, tone = "Sắp hết hạn", "warning"
            else:
                label, tone = "Còn hạn", "success"
            rows.append({
                "ten": b.get("ten_nguyen_lieu", ""),
                "ma_lo": b.get("ma_lo_nha_cung_cap") or f"LH-{int(b.get('ma_lo_hang', 0)):04d}",
                "nhap_con": f"{fmt_num(b.get('so_luong_nhap'))} / {fmt_num(b.get('so_luong_con_lai'))}",
                "han": fmt_date(b.get("han_su_dung")),
                "ngay_nhap": fmt_date(b.get("ngay_nhap_kho")),
                "con_han": "—" if days is None else (f"Quá {abs(int(days))} ngày" if int(days) < 0 else f"{int(days)} ngày"),
                "label": label,
                "tone": tone,
            })
        return rows

    @rx.var
    def transaction_rows(self) -> list[Row]:
        rows = []
        for tx in self.transactions:
            label, sign = TRANSACTION_TYPES.get(tx.get("loai_giao_dich", ""), (tx.get("loai_giao_dich", ""), ""))
            d = _parse_dt(tx.get("ngay_giao_dich"))
            rows.append({
                "ref": f"GD-{int(tx.get('ma_giao_dich', 0)):04d} · {d.strftime('%d/%m %H:%M') if d else '—'}",
                "ten": tx.get("ten_nguyen_lieu", ""),
                "loai": label,
                "so_luong": f"{sign} {fmt_num(tx.get('so_luong'))} {tx.get('don_vi_tinh', '')}".strip(),
                "positive": tx.get("loai_giao_dich") == "NHAP",
                "ghi_chu": tx.get("ghi_chu") or tx.get("ma_tham_chieu") or "",
            })
        return rows

    @rx.var
    def recent_transaction_rows(self) -> list[Row]:
        return self.transaction_rows[:3]

    @rx.var
    def expiry_watch(self) -> Row:
        """Lô cần ưu tiên xuất (FEFO): còn hàng và đã/sắp hết hạn."""
        risky = [b for b in self.batches if b.get("canh_bao_het_han") and _f(b.get("so_luong_con_lai")) > 0]
        if not risky:
            return {"count": 0, "title": "Không có lô sắp hết hạn", "detail": "Tất cả lô hàng còn hạn sử dụng an toàn."}
        b = min(risky, key=lambda x: int(x.get("so_ngay_con_han") or 0))
        ing = next((i for i in self.ingredients if i.get("ma_nguyen_lieu") == b.get("ma_nguyen_lieu")), {})
        unit = ing.get("don_vi_tinh", "")
        days = int(b.get("so_ngay_con_han") or 0)
        state = "Đã hết hạn" if days < 0 else "Hết hạn"
        return {
            "count": len(risky),
            "title": f"{short_name(b.get('ten_nguyen_lieu', ''))} · Lô {b.get('ma_lo_nha_cung_cap') or b.get('ma_lo_hang')}",
            "detail": f"Còn lại {fmt_num(b.get('so_luong_con_lai'))} {unit}  ·  {state} {fmt_date(b.get('han_su_dung'))}",
        }

    @rx.var
    def ingredient_options(self) -> list[dict[str, str]]:
        return [
            {"value": str(i.get("ma_nguyen_lieu")), "label": str(i.get("ten_nguyen_lieu", ""))}
            for i in sorted(self.ingredients, key=lambda x: str(x.get("ten_nguyen_lieu", "")))
        ]

    @rx.var
    def restock_quick_chips(self) -> list[dict[str, str]]:
        """Top nguyên liệu cần nhập thêm (ưu tiên Thiếu hàng / Chạm ngưỡng) để bấm chọn 1 chạm."""
        priority = {"NGUY_CO_THIEU": 0, "CHAM_NGUONG": 1, "AN_TOAN": 2, "TON_DU": 3}
        enriched = [enrich_ingredient(i) for i in self.ingredients]
        enriched.sort(key=lambda x: (priority.get(x["status_key"], 9), -_f(x.get("so_luong_can_bo_sung"))))
        chips: list[dict[str, str]] = []
        for x in enriched[:6]:
            unit = x.get("don_vi_tinh", "")
            suggested = _f(x.get("so_luong_can_bo_sung"))
            if suggested <= 0:
                suggested = max(_f(x.get("muc_ton_an_toan")), 5.0)
            suggested = _round_restock_qty(suggested, unit)
            chips.append({
                "key": f"restock:{x['ma_nguyen_lieu']}",
                "label": f"{short_name(x.get('ten_nguyen_lieu', ''))} (+{fmt_num(suggested)} {unit})",
                "tone": x["tone"],
            })
        return chips

    @rx.var
    def new_preset_chips(self) -> list[dict[str, str]]:
        """Các mẫu nguyên liệu quán cà phê mới (chưa có trong kho) để bấm chọn nhanh."""
        existing = {str(i.get("ten_nguyen_lieu", "")).strip().lower() for i in self.ingredients}
        chips: list[dict[str, str]] = []
        for idx, p in enumerate(INGREDIENT_CATALOG_PRESETS):
            if p["ten_nguyen_lieu"].strip().lower() in existing:
                continue
            chips.append({
                "key": f"preset:{idx}",
                "label": f"{short_name(p['ten_nguyen_lieu'])} ({p['don_vi_tinh']})",
            })
        return chips[:5]

    @rx.var
    def ingredient_suggestion_options(self) -> list[dict[str, str]]:
        """Danh sách dropdown đề xuất đầy đủ gồm: (1) Nhập thêm hàng có sẵn, (2) Thêm nguyên liệu mẫu mới."""
        priority = {"NGUY_CO_THIEU": 0, "CHAM_NGUONG": 1, "AN_TOAN": 2, "TON_DU": 3}
        enriched = [enrich_ingredient(i) for i in self.ingredients]
        enriched.sort(key=lambda x: (priority.get(x["status_key"], 9), str(x.get("ten_nguyen_lieu", ""))))

        options: list[dict[str, str]] = []
        for x in enriched:
            unit = x.get("don_vi_tinh", "")
            suggested = _f(x.get("so_luong_can_bo_sung"))
            if suggested <= 0:
                suggested = max(_f(x.get("muc_ton_an_toan")), 5.0)
            suggested = _round_restock_qty(suggested, unit)
            prefix = "[Thiếu hàng · Nhập thêm]" if x["status_key"] == "NGUY_CO_THIEU" else "[Có sẵn · Nhập thêm]"
            options.append({
                "value": f"restock:{x['ma_nguyen_lieu']}",
                "label": f"{prefix} {x.get('ten_nguyen_lieu', '')} (+{fmt_num(suggested)} {unit})",
            })

        existing = {str(i.get("ten_nguyen_lieu", "")).strip().lower() for i in self.ingredients}
        for idx, p in enumerate(INGREDIENT_CATALOG_PRESETS):
            if p["ten_nguyen_lieu"].strip().lower() in existing:
                continue
            options.append({
                "value": f"preset:{idx}",
                "label": f"[Mẫu mới] {p['ten_nguyen_lieu']} ({p['danh_muc']} · {p['don_vi_tinh']})",
            })
        return options

    # --- Dialog thêm / sửa nguyên liệu ---
    def open_add_ingredient(self):
        self.ing_edit_id = 0
        self.ing_restock_id = 0
        self.ing_preset_selected = ""
        self.ing_form = {"ten_nguyen_lieu": "", "danh_muc": "", "don_vi_tinh": "kg", "muc_ton_an_toan": "10", "muc_ton_toi_da": "100", "ton_kho_hien_tai": "0"}
        self.ing_dialog_open = True

    def open_edit_ingredient(self, ingredient_id: int):
        i = next((x for x in self.ingredients if int(x.get("ma_nguyen_lieu", 0)) == int(ingredient_id)), None)
        if not i:
            return
        self.ing_edit_id = int(ingredient_id)
        self.ing_restock_id = 0
        self.ing_preset_selected = ""
        self.ing_form = {
            "ten_nguyen_lieu": str(i.get("ten_nguyen_lieu", "")),
            "danh_muc": str(i.get("danh_muc") or ""),
            "don_vi_tinh": str(i.get("don_vi_tinh", "")),
            "muc_ton_an_toan": str(i.get("muc_ton_an_toan", "")),
            "muc_ton_toi_da": str(i.get("muc_ton_toi_da", "")),
            "ton_kho_hien_tai": str(i.get("ton_kho_hien_tai", "")),
        }
        self.ing_dialog_open = True

    def apply_ingredient_suggestion(self, key: str):
        """Điền tự động toàn bộ thông tin khi người dùng chọn 1 nguyên liệu đề xuất."""
        self.ing_preset_selected = key
        if key.startswith("restock:"):
            try:
                iid = int(key.split(":", 1)[1])
            except ValueError:
                return
            i = next((x for x in self.ingredients if int(x.get("ma_nguyen_lieu", 0)) == iid), None)
            if not i:
                return
            unit = str(i.get("don_vi_tinh", ""))
            suggested_qty = _f(i.get("so_luong_can_bo_sung"))
            if suggested_qty <= 0:
                suggested_qty = max(_f(i.get("muc_ton_an_toan")), 5.0)
            suggested_qty = _round_restock_qty(suggested_qty, unit)
            self.ing_restock_id = iid
            self.ing_form = {
                "ten_nguyen_lieu": str(i.get("ten_nguyen_lieu", "")),
                "danh_muc": str(i.get("danh_muc") or ""),
                "don_vi_tinh": unit,
                "muc_ton_an_toan": _fmt_input_num(i.get("muc_ton_an_toan", "")),
                "muc_ton_toi_da": _fmt_input_num(i.get("muc_ton_toi_da", "")),
                "ton_kho_hien_tai": _fmt_input_num(suggested_qty),
            }
        elif key.startswith("preset:"):
            try:
                idx = int(key.split(":", 1)[1])
                p = INGREDIENT_CATALOG_PRESETS[idx]
            except (ValueError, IndexError):
                return
            self.ing_restock_id = 0
            self.ing_form = dict(p)

    def clear_ing_restock_mode(self):
        """Quay lại chế độ thêm nguyên liệu mới từ đầu."""
        self.ing_restock_id = 0
        self.ing_preset_selected = ""
        self.ing_form = {"ten_nguyen_lieu": "", "danh_muc": "", "don_vi_tinh": "kg", "muc_ton_an_toan": "10", "muc_ton_toi_da": "100", "ton_kho_hien_tai": "0"}

    def set_ing_dialog_open(self, val: bool):
        self.ing_dialog_open = val

    def set_ing_field(self, field: str, val: str):
        self.ing_form = {**self.ing_form, field: val}

    async def save_ingredient(self):
        f = self.ing_form
        # Chế độ nhập thêm hàng nhanh cho nguyên liệu đã có sẵn trong kho (cộng dồn, không tạo trùng)
        if self.ing_restock_id > 0 and self.ing_edit_id == 0:
            try:
                qty_add = float(str(f.get("ton_kho_hien_tai") or 0).replace(",", "."))
            except ValueError:
                return rx.toast.error("Số lượng nhập thêm phải là số.")
            if qty_add <= 0:
                return rx.toast.error("Số lượng nhập thêm phải lớn hơn 0.")
            unit_str = str(f.get("don_vi_tinh", "")).strip()
            if _is_discrete_unit(unit_str) and qty_add != int(qty_add):
                return rx.toast.error(f"Đơn vị '{unit_str}' khi nhập hàng phải là số nguyên (VD: {math.ceil(qty_add)}).")
            tx_payload = {
                "ma_nguyen_lieu": self.ing_restock_id,
                "loai_giao_dich": "NHAP",
                "so_luong": qty_add,
                "ma_tham_chieu": f"NHAP-NHANH-{datetime.now():%Y%m%d%H%M%S}",
                "ghi_chu": f"Nhập thêm hàng nhanh từ đề xuất ({f.get('ten_nguyen_lieu', '')})",
            }
            try:
                async with self._client() as client:
                    res = await client.post("/inventory/transactions", json=tx_payload)
                if res.status_code in (200, 201):
                    self.ing_dialog_open = False
                    self.ing_restock_id = 0
                    self.ing_preset_selected = ""
                    return [
                        rx.toast.success(f"Đã nhập thêm {fmt_num(qty_add)} {f.get('don_vi_tinh', '')} {f.get('ten_nguyen_lieu', '')} vào kho."),
                        State.load_inventory,
                    ]
                return rx.toast.error(f"Nhập thêm thất bại: {res.text[:200]}")
            except Exception as e:
                return rx.toast.error(f"Lỗi kết nối: {e}")

        if not f.get("ten_nguyen_lieu", "").strip() or not f.get("don_vi_tinh", "").strip():
            return rx.toast.error("Vui lòng nhập tên nguyên liệu và đơn vị tính.")
        try:
            payload = {
                "ten_nguyen_lieu": f["ten_nguyen_lieu"].strip(),
                "danh_muc": f.get("danh_muc", "").strip() or None,
                "don_vi_tinh": f["don_vi_tinh"].strip(),
                "muc_ton_an_toan": float(str(f.get("muc_ton_an_toan") or 0).replace(",", ".")),
                "muc_ton_toi_da": float(str(f.get("muc_ton_toi_da") or 0).replace(",", ".")),
                "ton_kho_hien_tai": float(str(f.get("ton_kho_hien_tai") or 0).replace(",", ".")),
            }
        except ValueError:
            return rx.toast.error("Các ô số lượng phải là số.")
        try:
            async with self._client() as client:
                if self.ing_edit_id:
                    res = await client.put(f"/ingredients/{self.ing_edit_id}", json=payload)
                else:
                    res = await client.post("/ingredients", json=payload)
            if res.status_code in (200, 201):
                self.ing_dialog_open = False
                self.ing_preset_selected = ""
                return [rx.toast.success("Đã lưu nguyên liệu."), State.load_inventory]
            return rx.toast.error(f"Lưu thất bại: {res.text[:200]}")
        except Exception as e:
            return rx.toast.error(f"Lỗi kết nối: {e}")

    def ask_delete_ingredient(self, ingredient_id: int, name: str):
        self.ing_delete_id = int(ingredient_id)
        self.ing_delete_name = name

    def cancel_delete_ingredient(self, _open: bool = False):
        self.ing_delete_id = 0

    async def confirm_delete_ingredient(self):
        iid = self.ing_delete_id
        self.ing_delete_id = 0
        try:
            async with self._client() as client:
                res = await client.delete(f"/ingredients/{iid}")
            if res.status_code == 200:
                return [rx.toast.success("Đã ngừng sử dụng nguyên liệu."), State.load_inventory]
            return rx.toast.error(f"Xóa thất bại: {res.text[:200]}")
        except Exception as e:
            return rx.toast.error(f"Lỗi kết nối: {e}")

    # --- Dialog nhập / xuất kho ---
    def open_tx_dialog(self):
        first = self.ingredient_options[0]["value"] if self.ingredient_options else ""
        self.tx_form = {"ma_nguyen_lieu": first, "loai_giao_dich": "NHAP", "so_luong": "", "ghi_chu": ""}
        self.tx_dialog_open = True

    def set_tx_dialog_open(self, val: bool):
        self.tx_dialog_open = val

    def set_tx_field(self, field: str, val: str):
        self.tx_form = {**self.tx_form, field: val}

    async def save_transaction(self):
        f = self.tx_form
        try:
            qty = float(str(f.get("so_luong") or "").replace(",", "."))
        except ValueError:
            return rx.toast.error("Số lượng phải là số.")
        if qty <= 0 or not f.get("ma_nguyen_lieu"):
            return rx.toast.error("Chọn nguyên liệu và nhập số lượng lớn hơn 0.")
        payload = {
            "ma_nguyen_lieu": int(f["ma_nguyen_lieu"]),
            "loai_giao_dich": f.get("loai_giao_dich", "NHAP"),
            "so_luong": qty,
            "ma_tham_chieu": f"UI-{datetime.now():%Y%m%d%H%M%S}",
            "ghi_chu": f.get("ghi_chu") or None,
        }
        try:
            async with self._client() as client:
                res = await client.post("/inventory/transactions", json=payload)
            if res.status_code in (200, 201):
                self.tx_dialog_open = False
                return [rx.toast.success("Đã ghi nhận giao dịch kho."), State.load_inventory]
            return rx.toast.error(f"Ghi nhận thất bại: {res.text[:200]}")
        except Exception as e:
            return rx.toast.error(f"Lỗi kết nối: {e}")

    # ==========================================
    # NHÀ CUNG CẤP & SO SÁNH BÁO GIÁ
    # ==========================================

    def set_suppliers_tab(self, tab: str):
        self.active_tab_suppliers = tab

    async def set_compare_ingredient(self, val: str):
        self.compare_ingredient_id = val
        self.compare_qty = self._default_qty(val)
        try:
            async with self._client() as client:
                self.compare_result = await self._get(client, f"/suppliers/compare/{val}") or {}
        except Exception as e:
            self._offline(e)

    def set_compare_qty(self, val: str):
        self.compare_qty = val

    @rx.var
    def compare_ingredient_options(self) -> list[dict[str, str]]:
        names: dict[str, str] = {}
        for s in self.suppliers:
            for q in s.get("quotations", []):
                names[str(q.get("ma_nguyen_lieu"))] = str(q.get("ten_nguyen_lieu") or f"Nguyên liệu #{q.get('ma_nguyen_lieu')}")
        return [{"value": k, "label": v} for k, v in sorted(names.items(), key=lambda kv: kv[1])]

    @rx.var
    def compare_unit(self) -> str:
        i = next((x for x in self.ingredients if str(x.get("ma_nguyen_lieu")) == self.compare_ingredient_id), {})
        return str(i.get("don_vi_tinh", ""))

    @rx.var
    def quote_updated(self) -> str:
        dates = [
            _parse_dt(q.get("ngay_cap_nhat_gia"))
            for s in self.suppliers
            for q in s.get("quotations", [])
            if str(q.get("ma_nguyen_lieu")) == self.compare_ingredient_id
        ]
        dates = [d for d in dates if d]
        return f"Báo giá cập nhật: {max(dates):%d/%m/%Y}" if dates else ""

    def _qty(self) -> float:
        try:
            return max(float(str(self.compare_qty).replace(".", "").replace(",", ".")), 0)
        except ValueError:
            return 0.0

    @rx.var
    def compare_cards(self) -> list[Row]:
        """Tối đa 3 NCC theo xếp hạng MCDM, kèm tổng tiền dự kiến theo số lượng cần mua."""
        unit = self.compare_unit
        qty = self._qty()
        name = str(self.compare_result.get("ten_nguyen_lieu", ""))
        cards = []
        for s in (self.compare_result.get("danh_sach_so_sanh") or [])[:3]:
            moq = _f(s.get("so_luong_dat_toi_thieu"))
            order_qty = max(qty, moq)
            cards.append({
                "id": s.get("ma_nha_cung_cap"),
                "best": bool(s.get("de_xuat")),
                "badge": "Đề xuất tốt nhất" if s.get("de_xuat") else "Lựa chọn thay thế",
                "name": s.get("ten_nha_cung_cap", ""),
                "sub": f"{short_name(name)} · Báo giá / {unit}",
                "price": fmt_money(s.get("don_gia")),
                "lead": f"{int(_f(s.get('thoi_gian_giao_hang')))} ngày",
                "moq": f"{fmt_num(moq)} {unit}",
                "rating": f"{fmt_num(s.get('diem_uy_tin'), 1)} / 5",
                "score": fmt_num(s.get("diem_tong_hop_mcdm"), 1),
                "total_raw": order_qty * _f(s.get("don_gia")),
                "total": fmt_money(order_qty * _f(s.get("don_gia"))),
                "moq_note": f"Áp dụng MOQ {fmt_num(moq)} {unit}" if qty < moq else "",
            })
        return cards

    @rx.var
    def compare_rationale(self) -> Row:
        cards = self.compare_cards
        if not cards:
            return {"title": "Chưa có báo giá để so sánh", "line1": "Chọn nguyên liệu có báo giá từ ít nhất một nhà cung cấp.", "line2": ""}
        best = cards[0]
        reasons = []
        others = cards[1:]
        prices = [_f(c["price"].replace(".", "").replace(" ₫", "")) for c in cards]
        if prices[0] == min(prices):
            reasons.append("đơn giá thấp nhất")
        reasons.append(f"giao trong {best['lead']}")
        reasons.append(f"MOQ {best['moq']}")
        line1 = (
            f"Điểm tổng hợp MCDM {best['score']}/100: {', '.join(reasons)}. "
            f"Phù hợp với nhu cầu bổ sung {fmt_num(self._qty())} {self.compare_unit} {short_name(str(self.compare_result.get('ten_nguyen_lieu', '')))}."
        )
        if others:
            diff = others[0]["total_raw"] - best["total_raw"]
            if diff >= 0:
                line2 = f"Tiết kiệm {fmt_money(diff)} so với lựa chọn kế tiếp. Quản lý có thể thay đổi nhà cung cấp khi thẩm định."
            else:
                line2 = f"Đắt hơn {fmt_money(-diff)} so với lựa chọn kế tiếp nhưng giao nhanh và uy tín hơn. Quản lý có thể thay đổi khi thẩm định."
        else:
            line2 = "Hiện chỉ có một nhà cung cấp báo giá cho nguyên liệu này."
        return {"title": f"Vì sao AI chọn {best['name']}?", "line1": line1, "line2": line2}

    @rx.var
    def supplier_rows(self) -> list[Row]:
        return [
            {
                "id": s.get("ma_nha_cung_cap"),
                "name": s.get("ten_nha_cung_cap", ""),
                "contact": s.get("nguoi_lien_he") or "—",
                "phone": s.get("sdt") or "—",
                "email": s.get("email") or "",
                "address": s.get("dia_chi") or "",
                "lead": f"{int(_f(s.get('thoi_gian_giao_du_kien')))} ngày",
                "rating": f"{fmt_num(s.get('diem_uy_tin'), 1)} / 5",
                "quality": f"{fmt_num(s.get('diem_chat_luong'), 1)} / 5",
                "n_quotes": f"{len(s.get('quotations', []))} báo giá",
                "active": bool(s.get("trang_thai", True)),
            }
            for s in self.suppliers
        ]

    def open_supplier_dialog(self):
        self.supplier_form = {"ten_nha_cung_cap": "", "nguoi_lien_he": "", "sdt": "", "email": "", "dia_chi": "", "thoi_gian_giao_du_kien": "2", "diem_uy_tin": "4.5"}
        self.supplier_dialog_open = True

    def set_supplier_dialog_open(self, val: bool):
        self.supplier_dialog_open = val

    def set_supplier_field(self, field: str, val: str):
        self.supplier_form = {**self.supplier_form, field: val}

    async def save_supplier(self):
        f = self.supplier_form
        if not f.get("ten_nha_cung_cap", "").strip():
            return rx.toast.error("Vui lòng nhập tên nhà cung cấp.")
        try:
            payload = {
                "ten_nha_cung_cap": f["ten_nha_cung_cap"].strip(),
                "nguoi_lien_he": f.get("nguoi_lien_he") or None,
                "sdt": f.get("sdt") or None,
                "email": f.get("email") or None,
                "dia_chi": f.get("dia_chi") or None,
                "thoi_gian_giao_du_kien": int(f.get("thoi_gian_giao_du_kien") or 2),
                "diem_uy_tin": float(str(f.get("diem_uy_tin") or 4.5).replace(",", ".")),
            }
        except ValueError:
            return rx.toast.error("Thời gian giao và điểm uy tín phải là số.")
        try:
            async with self._client() as client:
                res = await client.post("/suppliers", json=payload)
            if res.status_code in (200, 201):
                self.supplier_dialog_open = False
                self.active_tab_suppliers = "danh-ba"
                return [rx.toast.success("Đã thêm nhà cung cấp."), State.load_suppliers]
            return rx.toast.error(f"Thêm thất bại: {res.text[:200]}")
        except Exception as e:
            return rx.toast.error(f"Lỗi kết nối: {e}")

    # ==========================================
    # TUẦN 7 · KẾ HOẠCH BỔ SUNG (ROP, SAFETY STOCK, NCC ĐƯỢC CHỌN)
    # ==========================================

    @staticmethod
    def _is_missing_route(res: httpx.Response) -> bool:
        """FastAPI trả 404 {"detail": "Not Found"} khi endpoint chưa tồn tại."""
        if res.status_code in (405, 501):
            return True
        if res.status_code != 404:
            return False
        try:
            return res.json().get("detail") == "Not Found"
        except Exception:
            return True

    async def load_rop_plan(self):
        """Gọi API kế hoạch bổ sung; nếu Backend chưa có endpoint thì tính tạm từ /ingredients + /suppliers."""
        if not (self._allowed("/inventory") or self._allowed("/suppliers")):
            return
        if rp.FORCE_MOCK:
            self.use_rop_mock()
            return
        self.rop_status = "loading"
        self.rop_error = ""
        yield
        try:
            async with self._client() as client:
                res = await client.get(rp.PLAN_PATH)
                if res.status_code == 200:
                    self.rop_plan = rp.normalize(res.json())
                    self.rop_source = "api"
                elif self._is_missing_route(res):
                    ings = await self._get(client, "/ingredients") or []
                    sups = await self._get(client, "/suppliers") or []
                    self.rop_plan = rp.build_plan(ings, sups)
                    self.rop_source = "derived"
                else:
                    self.rop_status = "error"
                    self.rop_error = f"Backend trả lỗi {res.status_code}: {res.text[:160]}"
                    return
            self.rop_status = "ok"
        except Exception as e:
            self.rop_status = "error"
            self.rop_error = f"Không kết nối được Backend ({API_BASE}). Chi tiết: {e}"
        if self.session_expired:
            yield self._force_logout()

    def use_rop_mock(self):
        self.rop_plan = list(rp.MOCK_PLAN)
        self.rop_source = "mock"
        self.rop_status = "ok"
        self.rop_error = ""

    def open_compare_for(self, ingredient_id: int):
        """Từ thẻ NCC được chọn chuyển sang tab So sánh báo giá của đúng nguyên liệu đó."""
        self.active_tab_suppliers = "so-sanh"
        return State.set_compare_ingredient(str(int(_f(ingredient_id))))

    def set_rop_only_need(self, val: bool):
        self.rop_only_need = val

    @rx.var
    def rop_rows(self) -> list[Row]:
        rows = sorted((rp.display_row(p) for p in self.rop_plan), key=lambda r: (not r["can_dat"], r["urgency"]))
        if self.rop_only_need:
            rows = [r for r in rows if r["can_dat"]]
        return rows

    @rx.var
    def rop_selected_rows(self) -> list[Row]:
        """Nguyên liệu cần đặt hàng kèm nhà cung cấp được chọn (trang Nhà cung cấp)."""
        rows = [rp.display_row(p) for p in self.rop_plan]
        return sorted([r for r in rows if r["can_dat"]], key=lambda r: r["urgency"])

    @rx.var
    def rop_need_count(self) -> int:
        return sum(1 for p in self.rop_plan if rp.display_row(p)["can_dat"])

    @rx.var
    def rop_near_count(self) -> int:
        return sum(1 for p in self.rop_plan if rp.display_row(p)["tone"] == "warning")

    @rx.var
    def rop_total_fmt(self) -> str:
        total = sum(rp.display_row(p)["total_raw"] for p in self.rop_plan if rp.display_row(p)["can_dat"])
        return fmt_money(total)

    @rx.var
    def rop_supplier_count(self) -> int:
        return len({r["ncc_id"] for r in self.rop_selected_rows if r["ncc_id"]})

    @rx.var
    def rop_source_label(self) -> str:
        return {
            "api": "Dữ liệu từ API kế hoạch bổ sung",
            "derived": "Tính tạm tại giao diện (API /bo-sung chưa có)",
            "mock": "Dữ liệu mẫu, không phải số thật",
        }.get(self.rop_source, "")

    @rx.var
    def rop_source_tone(self) -> str:
        return {"api": "success", "derived": "info", "mock": "warning"}.get(self.rop_source, "neutral")

    async def create_proposal_for(self, ingredient_id: int):
        """Nút "Tạo đề xuất" trên dòng thiếu hàng: gửi phiếu cho 1 nguyên liệu, chờ Quản lý duyệt."""
        item = next((p for p in self.rop_plan if int(_f(p.get("ma_nguyen_lieu"))) == int(ingredient_id)), None)
        if not item:
            return
        name = short_name(str(item.get("ten_nguyen_lieu", "")))
        if self.rop_source == "mock":
            yield rx.toast.info(f"Đang xem dữ liệu mẫu nên chưa tạo phiếu thật cho {name}. Bật Backend rồi tải lại trang.")
            return
        self.creating_proposal_id = int(ingredient_id)
        yield
        ncc = item.get("nha_cung_cap_chon") or {}
        payload = {
            "ma_nguyen_lieu": int(ingredient_id),
            "so_luong": _f(item.get("so_luong_can_dat")),
            "ma_nha_cung_cap": ncc.get("ma_nha_cung_cap"),
        }
        note = ""
        try:
            async with self._client() as client:
                res = await client.post(rp.CREATE_PROPOSAL_PATH, json=payload)
                if self._is_missing_route(res):
                    # Backend chưa có API tạo phiếu cho 1 nguyên liệu: dùng AI quét toàn bộ nguyên liệu dưới ROP
                    res = await client.post("/proposals/generate-ai")
                    note = " (AI gộp chung các nguyên liệu đang dưới ROP vào cùng phiếu)"
            if res.status_code in (200, 201):
                pid = res.json().get("ma_phieu_de_xuat")
                if self._allowed("/proposals/[ma_phieu]") and pid:
                    yield rx.toast.success(f"Đã tạo đề xuất cho {name}{note}. Hãy xem lại trước khi duyệt.")
                    yield rx.redirect(f"/proposals/{pid}")
                else:
                    yield rx.toast.success(f"Đã gửi đề xuất mua {name}{note}. Phiếu đang chờ Quản lý duyệt.")
            else:
                detail = res.text[:200]
                try:
                    detail = res.json().get("detail", detail)
                except Exception:
                    pass
                yield rx.toast.error(f"Chưa tạo được đề xuất: {detail}")
        except Exception as e:
            yield rx.toast.error(f"Lỗi kết nối Backend: {e}")
        finally:
            self.creating_proposal_id = 0
        if self.session_expired:
            yield self._force_logout()

    # ==========================================
    # ĐỀ XUẤT MUA HÀNG
    # ==========================================

    def set_proposal_filter(self, val: str):
        self.proposal_filter = val
        self.proposal_page = 1

    def set_proposal_search(self, val: str):
        self.proposal_search = val
        self.proposal_page = 1

    def prev_proposal_page(self):
        self.proposal_page = max(1, self.proposal_page - 1)

    def next_proposal_page(self):
        self.proposal_page = min(self.proposal_total_pages, self.proposal_page + 1)

    @rx.var
    def proposal_rows(self) -> list[Row]:
        rows = [enrich_proposal(p) for p in self.proposals]
        rows.sort(key=lambda r: r["created_raw"], reverse=True)
        return rows

    @rx.var
    def filtered_proposals(self) -> list[Row]:
        q = self.proposal_search.strip().lower()
        return [
            r for r in self.proposal_rows
            if (self.proposal_filter == "ALL" or r["status"] == self.proposal_filter)
            and (not q or q in r["code"].lower() or q in r["summary"].lower())
        ]

    @rx.var
    def proposal_total_pages(self) -> int:
        return max(1, math.ceil(len(self.filtered_proposals) / PAGE_SIZE_PROPOSALS))

    @rx.var
    def proposal_page_rows(self) -> list[Row]:
        start = (self.proposal_page - 1) * PAGE_SIZE_PROPOSALS
        return self.filtered_proposals[start:start + PAGE_SIZE_PROPOSALS]

    @rx.var
    def proposal_page_label(self) -> str:
        n = len(self.filtered_proposals)
        return f"Hiển thị {len(self.proposal_page_rows)} / {n} đề xuất" if n else "Không có đề xuất phù hợp"

    @rx.var
    def proposal_counts(self) -> dict[str, int]:
        counts = {"ALL": len(self.proposals), "CHO_DUYET": 0, "DA_DUYET": 0, "DA_SUA": 0, "TU_CHOI": 0}
        for p in self.proposals:
            s = p.get("trang_thai", "")
            if s in counts:
                counts[s] += 1
        return counts

    @rx.var
    def approved_this_month(self) -> int:
        now = datetime.now()
        n = 0
        for p in self.proposals:
            for h in p.get("approval_history", []) or []:
                d = _parse_dt(h.get("thoi_gian_duyet"))
                if h.get("hanh_dong") == "APPROVE" and d and d.year == now.year and d.month == now.month:
                    n += 1
        return n

    async def generate_ai_proposal(self):
        """Kích hoạt AI quét kho và lập phiếu đề xuất mới, sau đó mở trang chi tiết."""
        self.generating = True
        yield
        try:
            async with self._client() as client:
                res = await client.post("/proposals/generate-ai")
            if res.status_code == 200:
                pid = res.json().get("ma_phieu_de_xuat")
                yield rx.toast.success("AI đã lập phiếu đề xuất mới. Hãy xem xét trước khi duyệt.")
                yield rx.redirect(f"/proposals/{pid}")
            else:
                detail = res.json().get("detail", res.text) if res.headers.get("content-type", "").startswith("application/json") else res.text
                yield rx.toast.info(f"AI chưa tạo đề xuất: {detail}")
        except Exception as e:
            err_detail = str(e).strip() or type(e).__name__
            yield rx.toast.error(f"Lỗi kết nối ({err_detail})")
        finally:
            self.generating = False

    def set_proposal_comment(self, val: str):
        self.proposal_comment = val

    @rx.var
    def current_is_pending(self) -> bool:
        return self.current_proposal.get("status") == "CHO_DUYET"

    @rx.var
    def current_lines(self) -> list[Row]:
        return self.current_proposal.get("lines", []) or []

    @rx.var
    def current_reasons(self) -> list[str]:
        return [f"{short_name(l['ten'])}: {l['ly_do']}" for l in self.current_lines if l.get("ly_do")]

    @rx.var
    def current_meta(self) -> str:
        p = self.current_proposal
        if not p:
            return ""
        return f"{p.get('creator')} tạo lúc {p.get('created')}  /  {p.get('n_items')} nguyên liệu  /  {p.get('n_suppliers')} nhà cung cấp"

    @rx.var
    def current_history(self) -> list[Row]:
        rows = []
        for h in self.current_proposal.get("history", []) or []:
            label, tone = ACTION_LABELS.get(h.get("hanh_dong", ""), (h.get("hanh_dong", ""), "neutral"))
            rows.append({"time": fmt_dt(h.get("thoi_gian_duyet")), "who": h.get("nguoi_duyet", ""), "label": label, "tone": tone, "comment": h.get("y_kien") or ""})
        return rows

    async def handle_proposal_action(self, action: str):
        """Phê duyệt / Từ chối / Điều chỉnh phiếu đang xem (Human-in-the-loop)."""
        if not self.can_approve:
            yield rx.toast.error("Chỉ Quản lý cửa hàng mới được phê duyệt hoặc từ chối đề xuất.")
            return
        pid = self.current_proposal.get("id")
        if not pid:
            return
        comment = self.proposal_comment.strip()
        if action in ("REJECT", "MODIFY") and not comment:
            yield rx.toast.warning("Vui lòng nhập lý do điều chỉnh / từ chối vào ô Ý kiến của quản lý.")
            return
        self.acting = True
        yield
        try:
            async with self._client() as client:
                res = await client.post(
                    f"/proposals/{pid}/action",
                    json={
                        "hanh_dong": action,
                        "nguoi_duyet": self.user_name or "Quản lý cửa hàng",
                        "y_kien": comment or "Đồng ý theo số lượng đề xuất.",
                    },
                )
            if res.status_code == 403:
                yield rx.toast.error("Bạn không có quyền thực hiện thao tác này.")
            elif res.status_code == 200:
                verb = {"APPROVE": "phê duyệt", "REJECT": "từ chối", "MODIFY": "yêu cầu điều chỉnh"}.get(action, "cập nhật")
                self.current_proposal = enrich_proposal(res.json())
                self.proposal_comment = ""
                yield rx.toast.success(f"Đã {verb} phiếu {self.current_proposal.get('code')}.")
            else:
                yield rx.toast.error(f"Thao tác thất bại: {res.text[:200]}")
        except Exception as e:
            yield rx.toast.error(f"Lỗi gửi yêu cầu: {e}")
        finally:
            self.acting = False
        if self.session_expired:
            yield self._force_logout()

    def export_current_proposal(self):
        p = self.current_proposal
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Phiếu", p.get("code"), "Trạng thái", p.get("status_label"), "Ngày tạo", p.get("created")])
        w.writerow([])
        w.writerow(["Nguyên liệu", "Nhà cung cấp", "Số lượng", "Đơn giá", "Thành tiền", "Lý do"])
        for l in self.current_lines:
            w.writerow([l["ten"], l["ncc"], l["so_luong"], l["don_gia"], l["thanh_tien"], l["ly_do"]])
        w.writerow([])
        w.writerow(["Tổng tiền dự kiến", p.get("total_fmt")])
        return rx.download(data="﻿" + buf.getvalue(), filename=f"phieu_{p.get('code', 'de_xuat')}.csv")

    # ==========================================
    # LỊCH SỬ DUYỆT
    # ==========================================

    def set_history_search(self, val: str):
        self.history_search = val
        self.history_page = 1

    def set_history_action_filter(self, val: str):
        self.history_action_filter = val
        self.history_page = 1

    def prev_history_page(self):
        self.history_page = max(1, self.history_page - 1)

    def next_history_page(self):
        self.history_page = min(self.history_total_pages, self.history_page + 1)

    @rx.var
    def history_rows(self) -> list[Row]:
        rows = []
        for p in self.proposals:
            code = proposal_code(p)
            for h in p.get("approval_history", []) or []:
                label, tone = ACTION_LABELS.get(h.get("hanh_dong", ""), (h.get("hanh_dong", ""), "neutral"))
                rows.append({
                    "time": fmt_dt(h.get("thoi_gian_duyet")),
                    "time_raw": str(h.get("thoi_gian_duyet") or ""),
                    "who": h.get("nguoi_duyet", ""),
                    "code": code,
                    "pid": int(p.get("ma_phieu_de_xuat", 0)),
                    "action": h.get("hanh_dong", ""),
                    "label": label,
                    "tone": tone,
                    "comment": h.get("y_kien") or "—",
                })
        rows.sort(key=lambda r: r["time_raw"], reverse=True)
        return rows

    @rx.var
    def history_counts(self) -> dict[str, int]:
        c = {"APPROVE": 0, "MODIFY": 0, "REJECT": 0}
        for r in self.history_rows:
            if r["action"] in c:
                c[r["action"]] += 1
        return c

    @rx.var
    def filtered_history(self) -> list[Row]:
        q = self.history_search.strip().lower()
        return [
            r for r in self.history_rows
            if (self.history_action_filter == "ALL" or r["action"] == self.history_action_filter)
            and (not q or q in r["code"].lower() or q in r["who"].lower())
        ]

    @rx.var
    def history_total_pages(self) -> int:
        return max(1, math.ceil(len(self.filtered_history) / PAGE_SIZE_HISTORY))

    @rx.var
    def history_page_rows(self) -> list[Row]:
        start = (self.history_page - 1) * PAGE_SIZE_HISTORY
        return self.filtered_history[start:start + PAGE_SIZE_HISTORY]

    @rx.var
    def history_page_label(self) -> str:
        n = len(self.filtered_history)
        return f"Hiển thị {len(self.history_page_rows)} / {n} hoạt động" if n else "Chưa có hoạt động phê duyệt"

    @rx.var
    def history_period(self) -> str:
        times = [_parse_dt(r["time_raw"]) for r in self.history_rows]
        times = [d for d in times if d]
        if not times:
            return "Chưa có dữ liệu"
        return f"{min(times):%d/%m} – {max(times):%d/%m/%Y}"

    def export_history(self):
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Thời gian duyệt", "Người duyệt", "Mã phiếu", "Hành động", "Ý kiến"])
        for r in self.filtered_history:
            w.writerow([r["time"], r["who"], r["code"], r["label"], r["comment"]])
        return rx.download(data="﻿" + buf.getvalue(), filename="lich_su_duyet.csv")
