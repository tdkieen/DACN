import os
import typing
import httpx
import reflex as rx

from frontend.permissions import AUTH_ENABLED, CAN_APPROVE, HOME_PAGE, PAGE_ACCESS, ROLE_LABELS

API_BASE = os.getenv("NEXT_PUBLIC_API_URL", os.getenv("API_URL", "http://localhost:8000/api/v1"))


class State(rx.State):
    """Trạng thái ứng dụng Frontend Reflex, đồng bộ dữ liệu với FastAPI Backend."""

    # Trạng thái kết nối & thông báo
    backend_online: bool = True
    error_message: str = ""
    is_loading: bool = False

    # 1. Dashboard
    stats: dict[str, typing.Any] = {
        "tong_nguyen_lieu_dang_dung": 0,
        "nguy_co_thieu_hang": 0,
        "nguy_co_ton_du": 0,
        "phieu_cho_duyet": 0,
        "tong_gia_tri_ton_kho": 0.0,
        "ty_le_an_toan": 100.0,
    }
    alerts: list[dict[str, typing.Any]] = []
    trends: list[dict[str, typing.Any]] = []
    forecast_summary: list[dict[str, typing.Any]] = []
    selected_forecast_id: str = ""

    # 2. Inventory (Tồn kho)
    active_tab_inventory: str = "nguyen-lieu"
    ingredients: list[dict[str, typing.Any]] = []
    ingredient_search: str = ""
    ingredient_status_filter: str = "ALL"
    batches: list[dict[str, typing.Any]] = []
    only_expiring_batches: bool = False

    # 3. Forecast (Dự báo nhu cầu)
    forecast_ingredient_id: str = ""

    # 4. Suppliers (Nhà cung cấp)
    active_tab_suppliers: str = "danh-sach"
    suppliers: list[dict[str, typing.Any]] = []
    supplier_search: str = ""
    compare_ingredient_name: str = "ALL"
    expanded_suppliers: list[int] = []

    # 5. Proposals (Đề xuất mua hàng)
    proposals: list[dict[str, typing.Any]] = []
    proposal_comments: dict[str, str] = {}

    # 6. Đăng nhập & phân quyền (lưu ở trình duyệt để F5 không bị mất phiên)
    token: str = rx.LocalStorage("", name="dacn_token")
    user_name: str = rx.LocalStorage("", name="dacn_user_name")
    user_email: str = rx.LocalStorage("", name="dacn_user_email")
    user_role: str = rx.LocalStorage("", name="dacn_user_role")
    login_email: str = ""
    login_password: str = ""
    login_error: str = ""
    login_loading: bool = False
    session_expired: bool = False
    auth_enabled: bool = AUTH_ENABLED

    # ==========================================
    # ĐĂNG NHẬP / ĐĂNG XUẤT / PHÂN QUYỀN
    # ==========================================

    def _client(self) -> httpx.AsyncClient:
        """HTTP client gửi kèm JWT; nếu Backend trả 401 thì đánh dấu phiên đã hết hạn."""
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        async def _flag_401(response: httpx.Response) -> None:
            if response.status_code == 401:
                self.session_expired = True

        return httpx.AsyncClient(
            base_url=API_BASE,
            timeout=8.0,
            headers=headers,
            event_hooks={"response": [_flag_401]},
        )

    def _allowed(self, path: str) -> bool:
        """Vai trò hiện tại có được mở trang `path` không."""
        if not AUTH_ENABLED:
            return True
        if not self.token:
            return False
        roles = PAGE_ACCESS.get(path)
        return roles is None or self.user_role in roles

    def _force_logout(self):
        """Xóa phiên và quay về trang đăng nhập (dùng khi token hết hạn / bị từ chối)."""
        self.token = ""
        self.user_name = ""
        self.user_email = ""
        self.user_role = ""
        self.session_expired = False
        return [rx.toast.warning("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại."), rx.redirect("/login")]

    def set_login_email(self, val: str):
        self.login_email = val

    def set_login_password(self, val: str):
        self.login_password = val

    def fill_demo_account(self, email: str):
        """Điền nhanh tài khoản mẫu trong README (phục vụ demo)."""
        self.login_email = email
        self.login_password = "admin123"
        self.login_error = ""

    async def handle_login(self, form_data: dict):
        """Gọi POST /auth/login, lưu JWT + thông tin người dùng rồi chuyển tới trang phù hợp vai trò."""
        email = self.login_email.strip()
        if not email or not self.login_password:
            self.login_error = "Vui lòng nhập email và mật khẩu."
            return
        self.login_loading = True
        self.login_error = ""
        try:
            async with httpx.AsyncClient(base_url=API_BASE, timeout=8.0) as client:
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
                return rx.redirect(HOME_PAGE.get(self.user_role, "/inventory"))
            if res.status_code == 401:
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
        path = self.router.page.path or "/"
        if not self._allowed(path):
            return [
                rx.toast.error("Tài khoản của bạn không có quyền truy cập trang này."),
                rx.redirect(HOME_PAGE.get(self.user_role, "/inventory")),
            ]

    def redirect_if_logged_in(self):
        """on_load của trang /login: đã đăng nhập rồi thì vào thẳng trang chính."""
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
            return "Không phân quyền"
        return ROLE_LABELS.get(self.user_role, "Chưa đăng nhập")

    @rx.var
    def user_initials(self) -> str:
        if not AUTH_ENABLED:
            return "QL"
        parts = [w for w in self.user_name.split() if w]
        return (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else (self.user_name[:2].upper() or "?")

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
    # CÁC HÀM TẢI DỮ LIỆU TỪ FASTAPI
    # ==========================================

    async def load_dashboard(self):
        """Tải dữ liệu cho trang Tổng quan."""
        if not self._allowed("/dashboard"):
            return
        self.is_loading = True
        try:
            async with self._client() as client:
                res_stats = await client.get("/dashboard/stats")
                if res_stats.status_code == 200:
                    self.stats = res_stats.json()
                    self.backend_online = True

                res_alerts = await client.get("/dashboard/alerts")
                if res_alerts.status_code == 200:
                    self.alerts = res_alerts.json()

                res_trends = await client.get("/dashboard/trends")
                if res_trends.status_code == 200:
                    data = res_trends.json()
                    for item in data:
                        item["chi_phi_trieu"] = round(item.get("chi_phi_uoc_tinh", 0) / 1_000_000, 2)
                    self.trends = data

                res_fc = await client.get("/dashboard/forecast-summary")
                if res_fc.status_code == 200:
                    self.forecast_summary = res_fc.json()
                    if self.forecast_summary and not self.selected_forecast_id:
                        # Ưu tiên nguyên liệu đã có dự báo thật từ mô hình
                        real = [i for i in self.forecast_summary if not i.get("la_du_lieu_uoc_tinh")]
                        self.selected_forecast_id = str((real or self.forecast_summary)[0].get("ma_nguyen_lieu", ""))

        except Exception as e:
            self.backend_online = False
            self.error_message = f"Không thể kết nối FastAPI backend ({API_BASE}): {str(e)}"
        finally:
            self.is_loading = False
        if self.session_expired:
            return self._force_logout()

    async def load_inventory(self):
        """Tải dữ liệu nguyên liệu và các lô hàng."""
        if not self._allowed("/inventory"):
            return
        self.is_loading = True
        try:
            params = {}
            if self.ingredient_search:
                params["search"] = self.ingredient_search
            if self.ingredient_status_filter != "ALL":
                params["tinh_trang"] = self.ingredient_status_filter

            async with self._client() as client:
                res_ing = await client.get("/ingredients", params=params)
                if res_ing.status_code == 200:
                    self.ingredients = res_ing.json()

                batch_params = {}
                if self.only_expiring_batches:
                    batch_params["canh_bao_het_han"] = "true"

                res_batches = await client.get("/inventory/batches", params=batch_params)
                if res_batches.status_code == 200:
                    self.batches = res_batches.json()

                self.backend_online = True
        except Exception as e:
            self.backend_online = False
            self.error_message = f"Lỗi tải tồn kho: {str(e)}"
        finally:
            self.is_loading = False
        if self.session_expired:
            return self._force_logout()

    async def load_suppliers(self):
        """Tải danh sách nhà cung cấp & bảng báo giá."""
        if not self._allowed("/suppliers"):
            return
        self.is_loading = True
        try:
            params = {}
            if self.supplier_search:
                params["search"] = self.supplier_search

            async with self._client() as client:
                res = await client.get("/suppliers", params=params)
                if res.status_code == 200:
                    self.suppliers = res.json()
                    self.backend_online = True
        except Exception as e:
            self.backend_online = False
            self.error_message = f"Lỗi tải nhà cung cấp: {str(e)}"
        finally:
            self.is_loading = False
        if self.session_expired:
            return self._force_logout()

    async def load_proposals(self):
        """Tải danh sách phiếu đề xuất mua hàng do AI Agent tạo."""
        if not self._allowed("/proposals"):
            return
        self.is_loading = True
        try:
            async with self._client() as client:
                res = await client.get("/proposals")
                if res.status_code == 200:
                    self.proposals = res.json()
                    self.backend_online = True

                # Tải kèm stats để cập nhật số lượng phiếu chờ duyệt trên sidebar
                res_stats = await client.get("/dashboard/stats")
                if res_stats.status_code == 200:
                    self.stats = res_stats.json()
        except Exception as e:
            self.backend_online = False
            self.error_message = f"Lỗi tải đề xuất mua hàng: {str(e)}"
        finally:
            self.is_loading = False
        if self.session_expired:
            return self._force_logout()

    # ==========================================
    # CÁC ACTION TƯƠNG TÁC
    # ==========================================

    def set_selected_forecast(self, val: str):
        self.selected_forecast_id = val

    def set_inventory_tab(self, tab: str):
        self.active_tab_inventory = tab

    def set_ingredient_search(self, val: str):
        self.ingredient_search = val

    def set_status_filter(self, val: str):
        self.ingredient_status_filter = val

    def toggle_expiring_batches(self, val: bool):
        self.only_expiring_batches = val

    def set_suppliers_tab(self, tab: str):
        self.active_tab_suppliers = tab

    def set_supplier_search(self, val: str):
        self.supplier_search = val

    def set_compare_ingredient(self, val: str):
        self.compare_ingredient_name = val

    def toggle_supplier_expand(self, supplier_id: int):
        if supplier_id in self.expanded_suppliers:
            self.expanded_suppliers = [sid for sid in self.expanded_suppliers if sid != supplier_id]
        else:
            self.expanded_suppliers = self.expanded_suppliers + [supplier_id]

    def set_proposal_comment(self, pid_str: str, comment: str):
        new_dict = dict(self.proposal_comments)
        new_dict[pid_str] = comment
        self.proposal_comments = new_dict

    async def handle_proposal_action(self, proposal_id: int, action: str):
        """Phê duyệt hoặc Từ chối phiếu đề xuất mua hàng (Human-in-the-loop)."""
        if not self.can_approve:
            yield rx.toast.error("Chỉ Quản lý cửa hàng mới được phê duyệt hoặc từ chối đề xuất.")
            return
        pid_str = str(proposal_id)
        comment = self.proposal_comments.get(pid_str, "Đã duyệt từ Dashboard Reflex Python")
        approver = self.user_name or "Quản lý cửa hàng"
        try:
            async with self._client() as client:
                res = await client.post(
                    f"/proposals/{proposal_id}/action",
                    json={
                        "hanh_dong": action,
                        "nguoi_duyet": approver,
                        "y_kien": comment,
                    },
                )
                if res.status_code == 403:
                    yield rx.toast.error("Bạn không có quyền thực hiện thao tác này.")
                elif res.status_code == 200:
                    yield rx.toast.success(
                        f"Đã {'phê duyệt' if action == 'APPROVE' else 'từ chối'} đề xuất #{proposal_id} thành công!"
                    )
                    await self.load_proposals()
                else:
                    yield rx.toast.error(f"Thao tác thất bại: {res.text}")
        except Exception as e:
            yield rx.toast.error(f"Lỗi gửi yêu cầu: {str(e)}")

    # ==========================================
    # CÁC COMPUTED VARS (DỮ LIỆU ĐƯỢC TÍNH TOÁN)
    # ==========================================

    @rx.var
    def pending_proposals_count(self) -> int:
        return int(self.stats.get("phieu_cho_duyet", 0))

    @rx.var
    def active_forecast_data(self) -> list[dict[str, typing.Any]]:
        """Dữ liệu dự báo của nguyên liệu đang được chọn (kèm độ tin cậy dạng %)."""
        points: list[dict[str, typing.Any]] = []
        if not self.selected_forecast_id and self.forecast_summary:
            points = self.forecast_summary[0].get("du_lieu_7ngay", [])
        else:
            for item in self.forecast_summary:
                if str(item.get("ma_nguyen_lieu")) == str(self.selected_forecast_id):
                    points = item.get("du_lieu_7ngay", [])
                    break
        result = []
        for p in points:
            conf = float(p.get("do_tin_cay", 0) or 0)
            result.append({**p, "do_tin_cay_pct": round(conf * 100 if conf <= 1 else conf)})
        return result

    @rx.var
    def active_forecast_info(self) -> dict[str, typing.Any]:
        """Thông tin tóm tắt của nguyên liệu dự báo đang chọn."""
        if not self.selected_forecast_id and self.forecast_summary:
            return self.forecast_summary[0]
        for item in self.forecast_summary:
            if str(item.get("ma_nguyen_lieu")) == str(self.selected_forecast_id):
                return item
        return {}

    @rx.var
    def active_forecast_unit(self) -> str:
        """Đơn vị tính của nguyên liệu đang chọn (kg, lít, cái...)."""
        return str(self.active_forecast_info.get("don_vi_tinh", ""))

    @rx.var
    def active_forecast_confidence(self) -> str:
        """Độ tin cậy trung bình của 7 ngày dự báo (tính từ dữ liệu, không gán cứng)."""
        vals = [p["do_tin_cay_pct"] for p in self.active_forecast_data]
        return f"{round(sum(vals) / len(vals))}%" if vals else "—"

    @rx.var
    def active_forecast_method(self) -> str:
        """Tên phương pháp dự báo do Backend trả về (Prophet_v1, XGBoost_v1...)."""
        return str(self.active_forecast_info.get("phuong_phap") or "Chưa rõ")

    @rx.var
    def active_forecast_is_estimate(self) -> bool:
        """True nếu nguyên liệu chưa có dự báo từ mô hình, chỉ là số ước tính tạm."""
        return bool(self.active_forecast_info.get("la_du_lieu_uoc_tinh", False))

    @rx.var
    def forecast_options(self) -> list[dict[str, str]]:
        """Danh sách nguyên liệu cho ô chọn (hiện tên thay vì mã số)."""
        return [
            {"value": str(i.get("ma_nguyen_lieu", "")), "label": str(i.get("ten_nguyen_lieu", ""))}
            for i in self.forecast_summary
        ]

    @rx.var
    def price_comparison_rows(self) -> list[dict[str, typing.Any]]:
        """Bảng dữ liệu so sánh báo giá nguyên liệu giữa các NCC."""
        rows = []
        for s in self.suppliers:
            quotations = s.get("quotations", [])
            for q in quotations:
                ing_name = q.get("ten_nguyen_lieu", f"Nguyên liệu #{q.get('ma_nguyen_lieu')}")
                if self.compare_ingredient_name != "ALL" and ing_name != self.compare_ingredient_name:
                    continue
                rows.append({
                    "ten_nha_cung_cap": s.get("ten_nha_cung_cap"),
                    "ten_nguyen_lieu": ing_name,
                    "don_gia": q.get("don_gia", 0),
                    "so_luong_dat_toi_thieu": q.get("so_luong_dat_toi_thieu", 0),
                    "thoi_gian_giao_hang": q.get("thoi_gian_giao_hang", 0),
                    "diem_uy_tin": s.get("diem_uy_tin", 0),
                })
        return rows

    @rx.var
    def supplier_ingredient_options(self) -> list[str]:
        """Danh sách tên nguyên liệu có trong báo giá để lọc so sánh."""
        names = set()
        for s in self.suppliers:
            for q in s.get("quotations", []):
                name = q.get("ten_nguyen_lieu")
                if name:
                    names.add(name)
        return ["ALL"] + sorted(list(names))
