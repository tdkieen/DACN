"""Tuần 7 · Kế hoạch bổ sung hàng: ROP, Safety Stock, số lượng cần đặt và nhà cung cấp được chọn.

Frontend gọi API dự kiến của Backend (Kiên phụ trách):

    GET  {API_BASE}/bo-sung/ke-hoach      -> danh sách KE_HOACH (mẫu ở MOCK_PLAN bên dưới)
    POST {API_BASE}/bo-sung/tao-de-xuat   -> body {"ma_nguyen_lieu", "so_luong", "ma_nha_cung_cap"}
                                             trả về PurchaseProposalOut (có "ma_phieu_de_xuat")

Khi Backend CHƯA có endpoint (trả 404 Not Found), giao diện tự tính tạm kế hoạch từ
/ingredients (ROP, tồn an toàn, lượng cần bổ sung do Backend đã tính sẵn) và /suppliers
(báo giá, chấm điểm MCDM theo Mục 6.3 đặc tả). Khi Backend tắt hẳn, người dùng có thể
bấm "Xem dữ liệu mẫu" để xem MOCK_PLAN cùng cấu trúc.

Khi Backend làm xong chỉ cần trả đúng cấu trúc một phần tử như MOCK_PLAN, không phải sửa giao diện.
"""

from __future__ import annotations

import math
import os
import typing

Row = dict[str, typing.Any]

PLAN_PATH = os.getenv("ROP_PLAN_PATH", "/bo-sung/ke-hoach")
CREATE_PROPOSAL_PATH = os.getenv("ROP_CREATE_PATH", "/bo-sung/tao-de-xuat")
# Bật để luôn dùng dữ liệu mẫu (demo khi không có Backend): ROP_USE_MOCK=true
FORCE_MOCK = os.getenv("ROP_USE_MOCK", "false").strip().lower() in ("1", "true", "yes", "on")

DISCRETE_UNITS = {"chai", "hộp", "lon", "cái", "túi", "gói", "chiếc", "ly", "thùng"}


def _f(v: typing.Any) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _vn(v: float, decimals: int = 2) -> str:
    x = round(_f(v), decimals)
    s = f"{x:,.{decimals}f}"
    if decimals:
        s = s.rstrip("0").rstrip(".")
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def _money(v: float) -> str:
    return _vn(round(_f(v)), 0) + " ₫"


# ==========================================
# DỮ LIỆU MẪU (CÙNG CẤU TRÚC API DỰ KIẾN)
# ==========================================

MOCK_PLAN: list[Row] = [
    {
        "ma_nguyen_lieu": 1,
        "ten_nguyen_lieu": "Hạt cà phê Robusta Buôn Ma Thuột",
        "danh_muc": "Cà phê",
        "don_vi_tinh": "kg",
        "ton_kho_hien_tai": 4.5,
        "nhu_cau_tb_ngay": 2.6,
        "thoi_gian_giao_hang": 2,
        "muc_ton_an_toan": 5.0,
        "diem_dat_hang_lai_rop": 10.2,
        "so_luong_can_dat": 26.0,
        "can_dat_hang": True,
        "nha_cung_cap_chon": {
            "ma_nha_cung_cap": 1,
            "ten_nha_cung_cap": "Công ty Cà phê Nguyên Chất Đắk Lắk",
            "don_gia": 185000,
            "thoi_gian_giao_hang": 2,
            "so_luong_dat_toi_thieu": 5,
            "diem_tong_hop_mcdm": 92.4,
        },
        "ly_do_chon_ncc": "Điểm MCDM 92,4/100: đơn giá thấp nhất (185.000 ₫/kg), giao trong 2 ngày, chất lượng 4,8/5. Rẻ hơn 15.000 ₫/kg so với lựa chọn kế tiếp.",
        "thanh_tien_du_kien": 4810000,
    },
    {
        "ma_nguyen_lieu": 3,
        "ten_nguyen_lieu": "Sữa tươi tiệt trùng Barista 1L",
        "danh_muc": "Sữa & Kem",
        "don_vi_tinh": "hộp",
        "ton_kho_hien_tai": 14,
        "nhu_cau_tb_ngay": 9.0,
        "thoi_gian_giao_hang": 1,
        "muc_ton_an_toan": 12,
        "diem_dat_hang_lai_rop": 21,
        "so_luong_can_dat": 48,
        "can_dat_hang": True,
        "nha_cung_cap_chon": {
            "ma_nha_cung_cap": 2,
            "ten_nha_cung_cap": "Đại lý Phân phối Sữa Horeca Sài Gòn",
            "don_gia": 32000,
            "thoi_gian_giao_hang": 1,
            "so_luong_dat_toi_thieu": 24,
            "diem_tong_hop_mcdm": 88.1,
        },
        "ly_do_chon_ncc": "Điểm MCDM 88,1/100: giao nhanh nhất (1 ngày), đơn giá 32.000 ₫/hộp, MOQ 24 hộp phù hợp lượng cần đặt.",
        "thanh_tien_du_kien": 1536000,
    },
    {
        "ma_nguyen_lieu": 6,
        "ten_nguyen_lieu": "Siro Đào Monin 700ml",
        "danh_muc": "Siro & Xốt",
        "don_vi_tinh": "chai",
        "ton_kho_hien_tai": 3,
        "nhu_cau_tb_ngay": 0.8,
        "thoi_gian_giao_hang": 3,
        "muc_ton_an_toan": 2,
        "diem_dat_hang_lai_rop": 4.4,
        "so_luong_can_dat": 10,
        "can_dat_hang": True,
        "nha_cung_cap_chon": {
            "ma_nha_cung_cap": 3,
            "ten_nha_cung_cap": "Công ty Nguyên Liệu Pha Chế Vinbar",
            "don_gia": 215000,
            "thoi_gian_giao_hang": 3,
            "so_luong_dat_toi_thieu": 6,
            "diem_tong_hop_mcdm": 81.7,
        },
        "ly_do_chon_ncc": "Điểm MCDM 81,7/100: nhà cung cấp duy nhất có báo giá, uy tín 4,6/5. Áp dụng MOQ 6 chai.",
        "thanh_tien_du_kien": 2150000,
    },
    {
        "ma_nguyen_lieu": 18,
        "ten_nguyen_lieu": "Ly nhựa PET Takeaway 500ml",
        "danh_muc": "Bao bì",
        "don_vi_tinh": "cái",
        "ton_kho_hien_tai": 620,
        "nhu_cau_tb_ngay": 140,
        "thoi_gian_giao_hang": 2,
        "muc_ton_an_toan": 300,
        "diem_dat_hang_lai_rop": 580,
        "so_luong_can_dat": 0,
        "can_dat_hang": False,
        "nha_cung_cap_chon": {
            "ma_nha_cung_cap": 4,
            "ten_nha_cung_cap": "Tổng kho Bao bì Thực phẩm Tân Bình",
            "don_gia": 900,
            "thoi_gian_giao_hang": 2,
            "so_luong_dat_toi_thieu": 1000,
            "diem_tong_hop_mcdm": 90.2,
        },
        "ly_do_chon_ncc": "Điểm MCDM 90,2/100: đơn giá thấp nhất (900 ₫/cái), giao trong 2 ngày.",
        "thanh_tien_du_kien": 0,
    },
    {
        "ma_nguyen_lieu": 16,
        "ten_nguyen_lieu": "Trà Đen Phúc Long Đặc Biệt",
        "danh_muc": "Trà",
        "don_vi_tinh": "kg",
        "ton_kho_hien_tai": 9,
        "nhu_cau_tb_ngay": 0.6,
        "thoi_gian_giao_hang": 3,
        "muc_ton_an_toan": 2,
        "diem_dat_hang_lai_rop": 3.8,
        "so_luong_can_dat": 0,
        "can_dat_hang": False,
        "nha_cung_cap_chon": None,
        "ly_do_chon_ncc": "",
        "thanh_tien_du_kien": 0,
    },
]


# ==========================================
# TÍNH TẠM KHI BACKEND CHƯA CÓ ENDPOINT
# ==========================================

def _rank_suppliers(ingredient_id: int, suppliers: list[Row]) -> list[Row]:
    """Chấm điểm MCDM giống Backend (Mục 6.3): 0.4 giá + 0.3 lead time + 0.15 chất lượng + 0.15 uy tín."""
    quotes = []
    for s in suppliers:
        if not s.get("trang_thai", True):
            continue
        for q in s.get("quotations", []) or []:
            if int(_f(q.get("ma_nguyen_lieu"))) == ingredient_id and _f(q.get("don_gia")) > 0:
                quotes.append((s, q))
    if not quotes:
        return []
    min_price = min(_f(q.get("don_gia")) for _, q in quotes)
    min_lead = min(max(_f(q.get("thoi_gian_giao_hang")), 1) for _, q in quotes)
    ranked = []
    for s, q in quotes:
        price, lead = _f(q.get("don_gia")), max(_f(q.get("thoi_gian_giao_hang")), 1)
        rep = _f(s.get("diem_uy_tin"))
        score = (
            0.40 * (min_price / price)
            + 0.30 * (min_lead / lead)
            + 0.15 * min(max(_f(s.get("diem_chat_luong")) / 5.0, 0), 1)
            + 0.15 * min(max(rep / (5.0 if rep <= 5 else 100.0), 0), 1)
        )
        ranked.append({
            "ma_nha_cung_cap": s.get("ma_nha_cung_cap"),
            "ten_nha_cung_cap": s.get("ten_nha_cung_cap", ""),
            "don_gia": price,
            "thoi_gian_giao_hang": int(lead),
            "so_luong_dat_toi_thieu": _f(q.get("so_luong_dat_toi_thieu")),
            "diem_chat_luong": _f(s.get("diem_chat_luong")),
            "diem_uy_tin": rep,
            "diem_tong_hop_mcdm": round(score * 100, 1),
        })
    ranked.sort(key=lambda x: -x["diem_tong_hop_mcdm"])
    return ranked


def _reason(ranked: list[Row], unit: str, moq_applied: bool) -> str:
    if not ranked:
        return ""
    best = ranked[0]
    parts = []
    if best["don_gia"] <= min(r["don_gia"] for r in ranked):
        parts.append(f"đơn giá thấp nhất ({_money(best['don_gia'])}/{unit})")
    else:
        parts.append(f"đơn giá {_money(best['don_gia'])}/{unit}")
    if len(ranked) > 1 and best["thoi_gian_giao_hang"] <= min(r["thoi_gian_giao_hang"] for r in ranked):
        parts.append(f"giao nhanh nhất ({best['thoi_gian_giao_hang']} ngày)")
    else:
        parts.append(f"giao trong {best['thoi_gian_giao_hang']} ngày")
    parts.append(f"chất lượng {_vn(best['diem_chat_luong'], 1)}/5")
    text = f"Điểm MCDM {_vn(best['diem_tong_hop_mcdm'], 1)}/100: " + ", ".join(parts) + "."
    if len(ranked) > 1:
        alt = ranked[1]
        diff = alt["don_gia"] - best["don_gia"]
        if diff > 0:
            text += f" Rẻ hơn {_money(diff)}/{unit} so với {alt['ten_nha_cung_cap']}."
        elif diff < 0:
            text += f" Đắt hơn {alt['ten_nha_cung_cap']} {_money(-diff)}/{unit} nhưng tổng điểm giao hàng, chất lượng và uy tín cao hơn."
    else:
        text += " Hiện chỉ có nhà cung cấp này báo giá."
    if moq_applied:
        text += f" Đã làm tròn lên MOQ {_vn(best['so_luong_dat_toi_thieu'])} {unit}."
    return text


def build_plan(ingredients: list[Row], suppliers: list[Row]) -> list[Row]:
    """Dựng kế hoạch bổ sung từ dữ liệu Backend hiện có (cùng cấu trúc API dự kiến)."""
    plan = []
    for i in ingredients:
        iid = int(_f(i.get("ma_nguyen_lieu")))
        unit = str(i.get("don_vi_tinh", ""))
        ton = _f(i.get("ton_kho_hien_tai"))
        ss = _f(i.get("muc_ton_an_toan"))
        rop = _f(i.get("diem_dat_hang_lai_rop"))
        avg = _f(i.get("nhu_cau_du_bao_7ngay")) / 7
        ranked = _rank_suppliers(iid, suppliers)
        best = ranked[0] if ranked else None
        lead = round((rop - ss) / avg) if avg > 0 and rop > ss else (best["thoi_gian_giao_hang"] if best else 2)
        can_dat = ton <= rop or i.get("tinh_trang") == "NGUY_CO_THIEU"
        need = _f(i.get("so_luong_can_bo_sung")) if can_dat else 0.0
        if can_dat and need <= 0:
            need = max(rop * 1.5 - ton, 1.0)
        moq_applied = False
        if need > 0 and best and need < best["so_luong_dat_toi_thieu"]:
            need = best["so_luong_dat_toi_thieu"]
            moq_applied = True
        if need > 0 and unit.strip().lower() in DISCRETE_UNITS:
            need = float(math.ceil(need))
        plan.append({
            "ma_nguyen_lieu": iid,
            "ten_nguyen_lieu": i.get("ten_nguyen_lieu", ""),
            "danh_muc": i.get("danh_muc") or "",
            "don_vi_tinh": unit,
            "ton_kho_hien_tai": ton,
            "nhu_cau_tb_ngay": round(avg, 2),
            "thoi_gian_giao_hang": lead,
            "muc_ton_an_toan": ss,
            "diem_dat_hang_lai_rop": rop,
            "so_luong_can_dat": round(need, 2),
            "can_dat_hang": bool(can_dat),
            "nha_cung_cap_chon": best,
            "ly_do_chon_ncc": _reason(ranked, unit, moq_applied),
            "thanh_tien_du_kien": round(need * best["don_gia"]) if best else 0,
        })
    return plan


# ==========================================
# CHUẨN HÓA & ĐỊNH DẠNG CHO GIAO DIỆN
# ==========================================

def normalize(payload: typing.Any) -> list[Row]:
    """Nhận list hoặc {"items": [...]} từ API, trả list phần tử đúng cấu trúc."""
    if isinstance(payload, dict):
        payload = payload.get("items") or payload.get("data") or []
    return [p for p in (payload or []) if isinstance(p, dict)]


def display_row(p: Row) -> Row:
    """Thêm các trường đã định dạng sẵn kiểu Việt Nam để bảng hiển thị."""
    unit = str(p.get("don_vi_tinh", ""))
    ton, rop = _f(p.get("ton_kho_hien_tai")), _f(p.get("diem_dat_hang_lai_rop"))
    need = _f(p.get("so_luong_can_dat"))
    can_dat = bool(p.get("can_dat_hang")) or (rop > 0 and ton <= rop)
    if can_dat:
        status, tone = "Cần đặt ngay", "danger"
    elif rop > 0 and ton <= rop * 1.25:
        status, tone = "Sắp chạm ROP", "warning"
    else:
        status, tone = "Đủ hàng", "primary"
    ncc = p.get("nha_cung_cap_chon") or {}
    return {
        "id": int(_f(p.get("ma_nguyen_lieu"))),
        "ten": str(p.get("ten_nguyen_lieu", "")),
        "danh_muc": str(p.get("danh_muc") or ""),
        "unit": unit,
        "ton": _vn(ton),
        "ss": _vn(p.get("muc_ton_an_toan")),
        "rop": _vn(rop),
        "need": _vn(need) + " " + unit if need > 0 else "—",
        "need_raw": need,
        "meta": f"TB {_vn(p.get('nhu_cau_tb_ngay'))} {unit}/ngày · Lead time {int(_f(p.get('thoi_gian_giao_hang')))} ngày",
        "formula": f"{_vn(p.get('nhu_cau_tb_ngay'))} × {int(_f(p.get('thoi_gian_giao_hang')))} + {_vn(p.get('muc_ton_an_toan'))} = {_vn(rop)}",
        # Vạch tồn kho so với ROP: 100% = gấp đôi ROP
        "bar_pct": f"{min(ton / (rop * 2), 1) * 100:.0f}%" if rop > 0 else "100%",
        "rop_pct": "50%",
        "can_dat": can_dat,
        "status": status,
        "tone": tone,
        "has_ncc": bool(ncc),
        "ncc_id": int(_f(ncc.get("ma_nha_cung_cap"))) if ncc else 0,
        "ncc": str(ncc.get("ten_nha_cung_cap", "")) if ncc else "Chưa có báo giá",
        "ncc_price": f"{_money(ncc.get('don_gia'))}/{unit}" if ncc else "—",
        "ncc_lead": f"{int(_f(ncc.get('thoi_gian_giao_hang')))} ngày" if ncc else "—",
        "ncc_moq": f"{_vn(ncc.get('so_luong_dat_toi_thieu'))} {unit}" if ncc else "—",
        "ncc_score": _vn(ncc.get("diem_tong_hop_mcdm"), 1) if ncc else "—",
        "reason": str(p.get("ly_do_chon_ncc") or "") or "Chưa có nhà cung cấp nào báo giá cho nguyên liệu này.",
        "total": _money(p.get("thanh_tien_du_kien")) if _f(p.get("thanh_tien_du_kien")) > 0 else "—",
        "total_raw": _f(p.get("thanh_tien_du_kien")),
        "urgency": ton / rop if rop > 0 else 99.0,
        # Nhãn ghép sẵn để giao diện không phải nối chuỗi trong foreach
        "ton_unit": f"{_vn(ton)} {unit}",
        "formula_full": "TB/ngày × Lead time + Safety Stock = "
        + f"{_vn(p.get('nhu_cau_tb_ngay'))} × {int(_f(p.get('thoi_gian_giao_hang')))} + {_vn(p.get('muc_ton_an_toan'))} = {_vn(rop)}",
        "stock_line": f"Tồn {_vn(ton)} / ROP {_vn(rop)} {unit}  ·  Cần đặt " + (f"{_vn(need)} {unit}" if need > 0 else "—"),
        "ncc_score_label": f"MCDM {_vn(ncc.get('diem_tong_hop_mcdm'), 1)}/100" if ncc else "",
        "ncc_moq_label": f"MOQ {_vn(ncc.get('so_luong_dat_toi_thieu'))} {unit}" if ncc else "",
    }
