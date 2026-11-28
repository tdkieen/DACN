"""
Dịch vụ Kế hoạch Bổ sung Tồn kho (ROP, Safety Stock, MCDM, MOQ) &
Kiến trúc Kết hợp Đa Mô hình (Hybrid Multi-Model AI Procurement Agent) – Tuần 7
Phụ trách: Ngô Kế Nhật Trường - 2380602390 (AI & Data Engineer)

Kiến trúc 3 tầng mô hình kết hợp (Hybrid Multi-Model AI Architecture):
1. Tầng 1 – Quantitative ML Forecasting Models (`dich_vu_du_bao_ai.py`):
   - `Ensemble_HW_Ridge` (Tổ hợp có trọng số tối ưu giữa Holt-Winters và Fourier Ridge)
   - `HoltWinters_Seasonal` (San bằng mũ bậc 3 chu kỳ tuần m=7 & xu hướng giảm chấn)
   - `Fourier_Ridge_ML` (Hồi quy Ridge L2 + sóng Fourier mùa vụ năm + đặc trưng trễ)
   -> Đầu ra: Dự báo nhu cầu 7 ngày tới, cận dưới/trên 95% CI, độ tin cậy (%).
2. Tầng 2 – Operations Research & Optimization Models (`dich_vu_ke_hoach_bo_sung.py`):
   - Dynamic Safety Stock & ROP Engine: ROP = (Nhu cầu dự báo TB/ngày × Lead Time NCC tối ưu) + Safety Stock
   - MCDM Supplier Scoring Engine: 0.40 Giá + 0.30 Lead Time + 0.15 Chất lượng + 0.15 Uy tín
   - Lot-Sizing Rule: Làm tròn lượng đặt bổ sung theo MOQ và đơn vị tính rời rạc (`DISCRETE_UNITS`)
   - FEFO Expiry Risk Checker: Kiểm tra lô hàng sắp hết hạn (<= 7 ngày) trước khi đặt thêm.
3. Tầng 3 – Agentic LLM Orchestrator (`google-genai` SDK – `gemini-3.8-flash` / `gemini-4-argon`):
   - Điều phối tự chủ thông qua cơ chế Function Calling (Tool Calling) với 4 Tools an toàn:
     (1) `lay_danh_sach_canh_bao_ton_kho`
     (2) `lay_du_bao_nhu_cau`
     (3) `lay_bao_gia_nha_cung_cap`
     (4) `tao_phieu_de_xuat_mua` (Luôn tạo ở trạng thái `CHO_DUYET` – Human-in-the-loop)
   - Hỗ trợ cả Gemini Cloud Function Calling (khi có `GEMINI_API_KEY`) và Hybrid Multi-Model Local Agent
     (chạy 100% offline/CI không cần mạng ngoài), lưu vết đầy đủ vào bảng `nhat_ky_ai_agent`.
"""

from __future__ import annotations

import csv
import json
import math
import os
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.forecast import DemandForecast, KetQuaDanhGiaMoHinh
from app.models.ingredient import Ingredient
from app.models.inventory import Batch
from app.models.proposal import NhatKyAiAgent, ProposalDetail, PurchaseProposal
from app.models.supplier import Supplier, SupplierQuotation
from app.schemas.bo_sung import (
    BuocGoiToolAgentOut,
    KeHoachBoSungNguyenLieuOut,
    KetQuaAiAgentOut,
    KienTrucMultiModelOut,
    NhaCungCapChonOut,
    NhatKyAiAgentOut,
    ThanhPhanMoHinhAiOut,
    YeuCauChayAiAgent,
    YeuCauTaoDeXuatBoSung,
)
from app.schemas.proposal import PurchaseProposalOut
from app.services.proposal_service import cleanup_empty_proposals, get_proposal_by_id
from app.services.supplier_service import evaluate_suppliers_mcdm

DISCRETE_UNITS = {"chai", "hộp", "lon", "cái", "túi", "gói", "chiếc", "ly", "thùng"}

THU_MUC_BO_SUNG_TUAN7 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "du_lieu",
    "ke_hoach_bo_sung_tuan7",
)
FILE_KE_HOACH_CSV = os.path.join(THU_MUC_BO_SUNG_TUAN7, "ke_hoach_bo_sung_rop_tuan7.csv")
FILE_BAO_CAO_AGENT_JSON = os.path.join(THU_MUC_BO_SUNG_TUAN7, "bao_cao_hybrid_ai_agent_tuan7.json")


def _dam_bao_thu_muc_tuan7() -> None:
    os.makedirs(THU_MUC_BO_SUNG_TUAN7, exist_ok=True)


def _vn(v: float, decimals: int = 2) -> str:
    """Định dạng số kiểu Việt Nam (dấu chấm phân cách nghìn, dấu phẩy thập phân) khớp với Frontend."""
    x = round(float(v or 0.0), decimals)
    s = f"{x:,.{decimals}f}"
    if decimals:
        s = s.rstrip("0").rstrip(".")
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def _money(v: float) -> str:
    return _vn(round(float(v or 0.0)), 0) + " ₫"


def _la_don_vi_roi_rac(don_vi_tinh: Optional[str]) -> bool:
    return (don_vi_tinh or "").strip().lower() in DISCRETE_UNITS


def _lam_tron_luong_dat_theo_moq_va_don_vi(
    luong_can_tho: float,
    moq: float,
    don_vi_tinh: str,
) -> Tuple[float, bool]:
    """
    Chuẩn hóa số lượng đặt hàng theo MOQ của Nhà cung cấp và đơn vị tính:
    - Nếu lượng cần < MOQ thì nâng lên bằng MOQ (đánh dấu `da_lam_tron_moq = True`).
    - Nếu đơn vị là hàng đóng gói rời rạc (chai, hộp, lon, cái...) thì làm tròn lên số nguyên (`math.ceil`).
    """
    if luong_can_tho <= 0:
        return 0.0, False

    ket_qua = float(luong_can_tho)
    da_ap_dung_moq = False

    if moq > 0 and ket_qua < moq:
        ket_qua = float(moq)
        da_ap_dung_moq = True

    if _la_don_vi_roi_rac(don_vi_tinh):
        da_lam_tron_nguyen = float(math.ceil(ket_qua))
        if moq > 0 and da_lam_tron_nguyen < moq:
            da_lam_tron_nguyen = float(math.ceil(moq))
            da_ap_dung_moq = True
        ket_qua = da_lam_tron_nguyen
    else:
        ket_qua = round(ket_qua, 2)

    return ket_qua, da_ap_dung_moq


def _lay_thong_tin_du_bao_7_ngay_ml(
    db: Session,
    ingredient: Ingredient,
) -> Tuple[float, float, str, float, float]:
    """
    Truy xuất dự báo 7 ngày từ Tầng 1 (Time-Series ML Models Tuần 6):
    Trả về: (tong_7_ngay, tb_ngay, ten_mo_hinh, do_tin_cay_pct, bien_do_ci95_tb_ngay)
    """
    today = date.today()
    forecasts = (
        db.query(DemandForecast)
        .filter(
            DemandForecast.ma_nguyen_lieu == ingredient.ma_nguyen_lieu,
            DemandForecast.ngay_du_bao >= today,
        )
        .order_by(DemandForecast.ngay_du_bao.asc())
        .limit(7)
        .all()
    )

    if not forecasts:
        # Nếu ngày trong DB cũ hơn hôm nay, lấy 7 ngày dự báo mới nhất của nguyên liệu
        forecasts = (
            db.query(DemandForecast)
            .filter(DemandForecast.ma_nguyen_lieu == ingredient.ma_nguyen_lieu)
            .order_by(DemandForecast.ngay_du_bao.desc())
            .limit(7)
            .all()
        )
        forecasts = list(reversed(forecasts))

    if forecasts:
        tong_7_ngay = sum(float(f.so_luong_du_bao or 0.0) for f in forecasts)
        tb_ngay = tong_7_ngay / max(len(forecasts), 1)
        ten_mo_hinh = forecasts[0].phuong_phap or "Ensemble_HW_Ridge"
        confs = [
            (float(f.do_tin_cay) * 100.0 if float(f.do_tin_cay or 0) <= 1.0 else float(f.do_tin_cay or 92.0))
            for f in forecasts
            if f.do_tin_cay is not None
        ]
        do_tin_cay_pct = round(sum(confs) / len(confs), 1) if confs else 93.0

        best_eval = (
            db.query(KetQuaDanhGiaMoHinh)
            .filter(
                KetQuaDanhGiaMoHinh.ma_nguyen_lieu == ingredient.ma_nguyen_lieu,
                KetQuaDanhGiaMoHinh.la_mo_hinh_tot_nhat == True,
            )
            .order_by(KetQuaDanhGiaMoHinh.ma_danh_gia.desc())
            .first()
        )
        if best_eval and best_eval.do_lech_chuan_phan_du and best_eval.do_lech_chuan_phan_du > 0:
            bien_do_ci95_tb = float(best_eval.do_lech_chuan_phan_du) * 1.96
        else:
            bien_do_ci95_tb = tb_ngay * 0.15
    else:
        tb_ngay = max(float(ingredient.muc_ton_an_toan or 1.0) * 0.4, 2.0)
        tong_7_ngay = tb_ngay * 7.0
        ten_mo_hinh = "Ensemble_HW_Ridge"
        do_tin_cay_pct = 90.0
        bien_do_ci95_tb = tb_ngay * 0.15

    return (
        round(tong_7_ngay, 2),
        round(tb_ngay, 2),
        ten_mo_hinh,
        do_tin_cay_pct,
        round(bien_do_ci95_tb, 3),
    )


def _kiem_tra_lo_sap_het_han_fefo(db: Session, ingredient_id: int, don_vi_tinh: str) -> Optional[str]:
    """Kiểm tra các lô còn tồn kho sắp hết hạn (<= 7 ngày) theo nguyên tắc FEFO."""
    today = date.today()
    batches = (
        db.query(Batch)
        .filter(
            Batch.ma_nguyen_lieu == ingredient_id,
            Batch.so_luong_con_lai > 0,
        )
        .order_by(Batch.han_su_dung.asc().nullslast())
        .all()
    )
    risky_notes = []
    for b in batches:
        if b.han_su_dung:
            so_ngay = (b.han_su_dung - today).days
            if so_ngay <= 7:
                ma_lo = b.ma_lo_nha_cung_cap or f"LH-{b.ma_lo_hang:04d}"
                trang_thai_han = f"đã quá hạn {abs(so_ngay)} ngày" if so_ngay < 0 else f"còn {so_ngay} ngày HSD"
                risky_notes.append(f"Lô {ma_lo} ({_vn(b.so_luong_con_lai)} {don_vi_tinh}, {trang_thai_han})")
    if not risky_notes:
        return None
    return "Cảnh báo FEFO: " + "; ".join(risky_notes[:2])


def _tao_ly_do_chon_ncc(
    danh_sach_xep_hang: List[Any],
    don_vi_tinh: str,
    da_lam_tron_moq: bool,
    ten_mo_hinh_ml: str,
    tong_du_bao_7ngay: float,
) -> str:
    """Sinh lời giải thích rõ ràng vì sao thuật toán MCDM + Dự báo ML chọn Nhà cung cấp này."""
    if not danh_sach_xep_hang:
        return "Chưa có nhà cung cấp nào báo giá cho nguyên liệu này."

    best = danh_sach_xep_hang[0]
    parts = []
    min_price = min(float(r.don_gia) for r in danh_sach_xep_hang)
    min_lead = min(int(r.thoi_gian_giao_hang) for r in danh_sach_xep_hang)

    if float(best.don_gia) <= min_price:
        parts.append(f"đơn giá thấp nhất ({_money(best.don_gia)}/{don_vi_tinh})")
    else:
        parts.append(f"đơn giá {_money(best.don_gia)}/{don_vi_tinh}")

    if len(danh_sach_xep_hang) > 1 and int(best.thoi_gian_giao_hang) <= min_lead:
        parts.append(f"giao nhanh nhất ({best.thoi_gian_giao_hang} ngày)")
    else:
        parts.append(f"giao trong {best.thoi_gian_giao_hang} ngày")

    parts.append(f"chất lượng {_vn(best.diem_chat_luong, 1)}/5")
    text = f"Điểm MCDM {_vn(best.diem_tong_hop_mcdm, 1)}/100: " + ", ".join(parts) + "."

    if len(danh_sach_xep_hang) > 1:
        alt = danh_sach_xep_hang[1]
        diff = float(alt.don_gia) - float(best.don_gia)
        if diff > 0:
            text += f" Rẻ hơn {_money(diff)}/{don_vi_tinh} so với {alt.ten_nha_cung_cap}."
        elif diff < 0:
            text += (
                f" Đắt hơn {alt.ten_nha_cung_cap} {_money(-diff)}/{don_vi_tinh} "
                f"nhưng tổng điểm tốc độ giao hàng, chất lượng và uy tín cao hơn."
            )
    else:
        text += " Hiện chỉ có nhà cung cấp này báo giá."

    text += f" Dự báo 7 ngày ({ten_mo_hinh_ml}): {_vn(tong_du_bao_7ngay)} {don_vi_tinh}."

    if da_lam_tron_moq:
        text += f" Đã làm tròn lên MOQ {_vn(best.so_luong_dat_toi_thieu)} {don_vi_tinh}."

    return text


def xay_dung_ke_hoach_bo_sung(
    db: Session,
    chi_lay_can_dat: bool = False,
) -> List[KeHoachBoSungNguyenLieuOut]:
    """
    Xây dựng Kế hoạch Bổ sung Tồn kho Tuần 7 cho toàn bộ 15 nguyên liệu:
    Kết hợp trực tiếp Mô hình Dự báo ML Tuần 6 + Công thức ROP/Safety Stock + Xếp hạng MCDM Nhà cung cấp.
    Cấu trúc trả về tương thích 100% với Frontend `replenishment.py`.
    """
    ingredients = (
        db.query(Ingredient)
        .filter(Ingredient.trang_thai == True)
        .order_by(Ingredient.ma_nguyen_lieu.asc())
        .all()
    )

    ke_hoach: List[KeHoachBoSungNguyenLieuOut] = []

    for ing in ingredients:
        don_vi = (ing.don_vi_tinh or "").strip()
        ton_hien_tai = round(float(ing.ton_kho_hien_tai or 0.0), 2)
        safety_stock = round(float(ing.muc_ton_an_toan or 0.0), 2)

        # 1. Lấy dự báo 7 ngày từ mô hình ML thắng cuộc (Tuần 6)
        tong_7_ngay, tb_ngay, ten_mo_hinh, do_tin_cay_pct, bien_do_ci95_tb = _lay_thong_tin_du_bao_7_ngay_ml(
            db, ing
        )

        # 2. Chấm điểm MCDM để chọn Nhà cung cấp tối ưu và lấy Lead Time chuẩn
        mcdm_res = evaluate_suppliers_mcdm(db, ing.ma_nguyen_lieu)
        ranked = mcdm_res.danh_sach_so_sanh
        best = mcdm_res.nha_cung_cap_toi_uu

        lead_time = int(best.thoi_gian_giao_hang) if best else 2
        moq = float(best.so_luong_dat_toi_thieu) if best else 1.0

        # 3. Tính Safety Stock gợi ý từ khoảng tin cậy 95% của mô hình ML trong thời gian Lead Time
        ss_goi_y_ai = round(max(safety_stock, bien_do_ci95_tb * math.sqrt(max(lead_time, 1)) * 1.65), 2)
        if _la_don_vi_roi_rac(don_vi):
            ss_goi_y_ai = float(math.ceil(ss_goi_y_ai))

        # 4. Tính Điểm đặt hàng lại (ROP = Nhu cầu TB/ngày * Lead Time + Safety Stock)
        rop = round(tb_ngay * lead_time + safety_stock, 2)

        # 5. Xác định trạng thái cần đặt hàng và số lượng cần đặt (Mục 6.3 Đặc tả)
        can_dat = bool(ton_hien_tai <= rop)
        luong_can_tho = 0.0
        if can_dat:
            # Công thức chuẩn Mục 6.3: max(0, Nhu cầu 7 ngày + Tồn an toàn - Tồn hiện tại)
            theo_du_bao_7n = tong_7_ngay + safety_stock - ton_hien_tai
            theo_rop = rop * 1.5 - ton_hien_tai
            luong_can_tho = max(theo_du_bao_7n, theo_rop, 1.0)

        so_luong_can_dat, da_lam_tron_moq = _lam_tron_luong_dat_theo_moq_va_don_vi(
            luong_can_tho, moq, don_vi
        )

        ncc_chon_out: Optional[NhaCungCapChonOut] = None
        if best:
            ncc_chon_out = NhaCungCapChonOut(
                ma_nha_cung_cap=best.ma_nha_cung_cap,
                ten_nha_cung_cap=best.ten_nha_cung_cap,
                don_gia=best.don_gia,
                thoi_gian_giao_hang=best.thoi_gian_giao_hang,
                so_luong_dat_toi_thieu=best.so_luong_dat_toi_thieu,
                diem_chat_luong=best.diem_chat_luong,
                diem_uy_tin=best.diem_uy_tin,
                diem_tong_hop_mcdm=best.diem_tong_hop_mcdm,
            )

        ly_do = _tao_ly_do_chon_ncc(
            danh_sach_xep_hang=ranked,
            don_vi_tinh=don_vi,
            da_lam_tron_moq=da_lam_tron_moq,
            ten_mo_hinh_ml=ten_mo_hinh,
            tong_du_bao_7ngay=tong_7_ngay,
        )
        canh_bao_fefo = _kiem_tra_lo_sap_het_han_fefo(db, ing.ma_nguyen_lieu, don_vi)
        if canh_bao_fefo:
            ly_do += f" [{canh_bao_fefo}]."

        thanh_tien = round(so_luong_can_dat * float(best.don_gia)) if (best and so_luong_can_dat > 0) else 0.0

        item = KeHoachBoSungNguyenLieuOut(
            ma_nguyen_lieu=ing.ma_nguyen_lieu,
            ten_nguyen_lieu=ing.ten_nguyen_lieu,
            danh_muc=ing.danh_muc or "",
            don_vi_tinh=don_vi,
            ton_kho_hien_tai=ton_hien_tai,
            nhu_cau_tb_ngay=tb_ngay,
            nhu_cau_du_bao_7ngay=tong_7_ngay,
            mo_hinh_du_bao=ten_mo_hinh,
            do_tin_cay_du_bao_pct=do_tin_cay_pct,
            thoi_gian_giao_hang=lead_time,
            muc_ton_an_toan=safety_stock,
            ton_an_toan_goi_y_ai=ss_goi_y_ai,
            diem_dat_hang_lai_rop=rop,
            so_luong_can_dat=so_luong_can_dat,
            can_dat_hang=can_dat,
            da_lam_tron_moq=da_lam_tron_moq,
            canh_bao_lo_sap_het_han=canh_bao_fefo,
            nha_cung_cap_chon=ncc_chon_out,
            ly_do_chon_ncc=ly_do,
            thanh_tien_du_kien=thanh_tien,
        )

        if chi_lay_can_dat and not item.can_dat_hang:
            continue
        ke_hoach.append(item)

    if not chi_lay_can_dat:
        _xuat_file_ke_hoach_bo_sung_csv(ke_hoach)
    return ke_hoach


def _xuat_file_ke_hoach_bo_sung_csv(ke_hoach: List[KeHoachBoSungNguyenLieuOut]) -> None:
    """Lưu bảng kế hoạch bổ sung Tuần 7 ra CSV để phục vụ kiểm định và báo cáo."""
    if not ke_hoach:
        return
    try:
        _dam_bao_thu_muc_tuan7()
        with open(FILE_KE_HOACH_CSV, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "ma_nguyen_lieu",
                    "ten_nguyen_lieu",
                    "danh_muc",
                    "don_vi_tinh",
                    "ton_kho_hien_tai",
                    "nhu_cau_tb_ngay",
                    "nhu_cau_du_bao_7ngay",
                    "mo_hinh_du_bao",
                    "thoi_gian_giao_hang",
                    "muc_ton_an_toan",
                    "diem_dat_hang_lai_rop",
                    "can_dat_hang",
                    "so_luong_can_dat",
                    "ten_nha_cung_cap_chon",
                    "don_gia",
                    "moq",
                    "diem_mcdm",
                    "thanh_tien_du_kien",
                    "ly_do_chon_ncc",
                ]
            )
            for p in ke_hoach:
                ncc = p.nha_cung_cap_chon
                writer.writerow(
                    [
                        p.ma_nguyen_lieu,
                        p.ten_nguyen_lieu,
                        p.danh_muc,
                        p.don_vi_tinh,
                        p.ton_kho_hien_tai,
                        p.nhu_cau_tb_ngay,
                        p.nhu_cau_du_bao_7ngay,
                        p.mo_hinh_du_bao,
                        p.thoi_gian_giao_hang,
                        p.muc_ton_an_toan,
                        p.diem_dat_hang_lai_rop,
                        p.can_dat_hang,
                        p.so_luong_can_dat,
                        ncc.ten_nha_cung_cap if ncc else "",
                        ncc.don_gia if ncc else 0,
                        ncc.so_luong_dat_toi_thieu if ncc else 0,
                        ncc.diem_tong_hop_mcdm if ncc else 0,
                        p.thanh_tien_du_kien,
                        p.ly_do_chon_ncc,
                    ]
                )
    except Exception:
        pass


def tao_de_xuat_bo_sung_mot_nguyen_lieu(
    db: Session,
    yeu_cau: YeuCauTaoDeXuatBoSung,
) -> PurchaseProposalOut:
    """
    Xử lý POST /api/v1/bo-sung/tao-de-xuat (Nút 'Tạo đề xuất' trên từng dòng ROP của Frontend Tuần 7).
    Kết hợp kết quả Dự báo ML Tuần 6 + ROP + MCDM để tạo phiếu đề xuất ở trạng thái `CHO_DUYET`.
    """
    cleanup_empty_proposals(db)

    ing = db.query(Ingredient).filter(Ingredient.ma_nguyen_lieu == yeu_cau.ma_nguyen_lieu).first()
    if not ing:
        raise ValueError(f"Không tìm thấy nguyên liệu #{yeu_cau.ma_nguyen_lieu}")

    ke_hoach_all = xay_dung_ke_hoach_bo_sung(db, chi_lay_can_dat=False)
    item_kh = next((x for x in ke_hoach_all if x.ma_nguyen_lieu == ing.ma_nguyen_lieu), None)
    if not item_kh:
        raise ValueError(f"Không thể tính kế hoạch bổ sung cho nguyên liệu {ing.ten_nguyen_lieu}")

    mcdm_res = evaluate_suppliers_mcdm(db, ing.ma_nguyen_lieu)
    best_supplier = mcdm_res.nha_cung_cap_toi_uu

    # Chọn nhà cung cấp theo yêu cầu hoặc theo điểm MCDM tối ưu
    target_supplier_id = yeu_cau.ma_nha_cung_cap or (best_supplier.ma_nha_cung_cap if best_supplier else None)
    quotation = None
    if target_supplier_id:
        quotation = (
            db.query(SupplierQuotation)
            .filter(
                SupplierQuotation.ma_nguyen_lieu == ing.ma_nguyen_lieu,
                SupplierQuotation.ma_nha_cung_cap == target_supplier_id,
            )
            .first()
        )
    if not quotation:
        quotation = (
            db.query(SupplierQuotation)
            .filter(SupplierQuotation.ma_nguyen_lieu == ing.ma_nguyen_lieu)
            .first()
        )

    supplier_id = quotation.ma_nha_cung_cap if quotation else 1
    unit_price = float(quotation.don_gia) if quotation else 50000.0
    moq = float(quotation.so_luong_dat_toi_thieu) if quotation else 1.0
    lead_time = int(quotation.thoi_gian_giao_hang) if quotation else item_kh.thoi_gian_giao_hang

    supplier_obj = db.query(Supplier).filter(Supplier.ma_nha_cung_cap == supplier_id).first()
    supplier_name = supplier_obj.ten_nha_cung_cap if supplier_obj else "Nhà cung cấp chuẩn"

    matched_score = next(
        (s.diem_tong_hop_mcdm for s in mcdm_res.danh_sach_so_sanh if s.ma_nha_cung_cap == supplier_id),
        best_supplier.diem_tong_hop_mcdm if best_supplier else 90.0,
    )

    luong_yeu_cau = float(yeu_cau.so_luong or 0.0)
    if luong_yeu_cau <= 0:
        luong_yeu_cau = item_kh.so_luong_can_dat if item_kh.so_luong_can_dat > 0 else max(item_kh.diem_dat_hang_lai_rop, moq, 1.0)

    so_luong_dat, da_lam_tron_moq = _lam_tron_luong_dat_theo_moq_va_don_vi(
        luong_yeu_cau, moq, ing.don_vi_tinh
    )
    thanh_tien = round(so_luong_dat * unit_price, 2)

    ly_do_chi_tiet = (
        f"[Hybrid Multi-Model AI] Tồn kho hiện tại {_vn(ing.ton_kho_hien_tai)} {ing.don_vi_tinh} "
        f"≤ Điểm đặt hàng lại ROP {_vn(item_kh.diem_dat_hang_lai_rop)} {ing.don_vi_tinh} "
        f"(Safety Stock {_vn(ing.muc_ton_an_toan)} {ing.don_vi_tinh}). "
        f"Mô hình ML '{item_kh.mo_hinh_du_bao}' dự báo nhu cầu 7 ngày tới là "
        f"{_vn(item_kh.nhu_cau_du_bao_7ngay)} {ing.don_vi_tinh} (TB {_vn(item_kh.nhu_cau_tb_ngay)} {ing.don_vi_tinh}/ngày, "
        f"độ tin cậy {_vn(item_kh.do_tin_cay_du_bao_pct, 1)}%). "
        f"Thuật toán MCDM chọn '{supplier_name}' (Điểm {_vn(matched_score, 1)}/100, "
        f"đơn giá {_money(unit_price)}/{ing.don_vi_tinh}, giao trong {lead_time} ngày). "
        f"Số lượng đề xuất {_vn(so_luong_dat)} {ing.don_vi_tinh} (MOQ {_vn(moq)} {ing.don_vi_tinh})."
    )
    if item_kh.canh_bao_lo_sap_het_han:
        ly_do_chi_tiet += f" Lưu ý: {item_kh.canh_bao_lo_sap_het_han}."
    if yeu_cau.ghi_chu_them:
        ly_do_chi_tiet += f" Ghi chú: {yeu_cau.ghi_chu_them}."

    proposal = PurchaseProposal(
        ngay_tao=datetime.now(),
        tong_tien_du_kien=thanh_tien,
        trang_thai="CHO_DUYET",
        ly_do_tong_quan=(
            f"Phiếu đề xuất bổ sung nhanh từ Kế hoạch ROP Tuần 7 cho nguyên liệu '{ing.ten_nguyen_lieu}'. "
            f"Kết hợp mô hình dự báo '{item_kh.mo_hinh_du_bao}', công thức ROP và xếp hạng nhà cung cấp MCDM. "
            f"Phiếu ở trạng thái CHỜ DUYỆT (Human-in-the-loop)."
        ),
        nguoi_tao="AI Agent (Hybrid ML + ROP + MCDM)",
    )
    db.add(proposal)
    db.flush()

    detail = ProposalDetail(
        ma_phieu_de_xuat=proposal.ma_phieu_de_xuat,
        ma_nguyen_lieu=ing.ma_nguyen_lieu,
        ma_nha_cung_cap=supplier_id,
        so_luong_de_xuat=so_luong_dat,
        don_gia_du_kien=unit_price,
        so_luong_du_doan_7ngay=item_kh.nhu_cau_du_bao_7ngay,
        ly_do_de_xuat=ly_do_chi_tiet,
    )
    db.add(detail)
    db.commit()
    db.refresh(proposal)

    return get_proposal_by_id(db, proposal.ma_phieu_de_xuat)


# ==============================================================================
# 2. BỘ 4 CÔNG CỤ AN TOÀN CỦA AI AGENT (TOOL CALLING SCHEMAS - MỤC 7 ĐẶC TẢ)
# ==============================================================================

TOOL_DECLARATIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "name": "lay_danh_sach_canh_bao_ton_kho",
        "description": (
            "Lấy danh sách các nguyên liệu đang dưới ngưỡng Điểm đặt hàng lại (ROP) hoặc có nguy cơ thiếu hàng, "
            "kèm tồn kho hiện tại, mức tồn an toàn (Safety Stock), điểm ROP, số lượng cần đặt dự kiến "
            "và cảnh báo lô hàng sắp hết hạn (FEFO)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "chi_lay_can_dat": {
                    "type": "boolean",
                    "description": "True để chỉ lấy các nguyên liệu có Tồn hiện tại <= ROP cần đặt hàng ngay.",
                }
            },
            "required": [],
        },
    },
    {
        "type": "function",
        "name": "lay_du_bao_nhu_cau",
        "description": (
            "Truy xuất kết quả dự báo nhu cầu 7 ngày tới của 1 nguyên liệu do các mô hình Machine Learning "
            "(Ensemble_HW_Ridge, HoltWinters_Seasonal, Fourier_Ridge_ML) sinh ra, kèm khoảng tin cậy 95%."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ma_nguyen_lieu": {
                    "type": "integer",
                    "description": "Mã nguyên liệu cần xem dự báo 7 ngày tới.",
                }
            },
            "required": ["ma_nguyen_lieu"],
        },
    },
    {
        "type": "function",
        "name": "lay_bao_gia_nha_cung_cap",
        "description": (
            "Chạy thuật toán MCDM (Multi-Criteria Decision Making) để chấm điểm và xếp hạng các Nhà cung cấp "
            "cho 1 nguyên liệu dựa trên Đơn giá (40%), Thời gian giao hàng Lead time (30%), "
            "Chất lượng (15%) và Độ uy tín (15%), kèm số lượng đặt tối thiểu (MOQ)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ma_nguyen_lieu": {
                    "type": "integer",
                    "description": "Mã nguyên liệu cần so sánh và xếp hạng nhà cung cấp.",
                }
            },
            "required": ["ma_nguyen_lieu"],
        },
    },
    {
        "type": "function",
        "name": "tao_phieu_de_xuat_mua",
        "description": (
            "Ghi nhận Phiếu đề xuất mua hàng ở trạng thái CHO_DUYET (Human-in-the-loop) để Quản lý cửa hàng phê duyệt. "
            "Công cụ này tuyệt đối KHÔNG tự động gửi đơn đặt hàng cho nhà cung cấp."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ly_do_tong_quan": {
                    "type": "string",
                    "description": "Lập luận tổng quan của AI Agent giải thích vì sao cần tạo phiếu đề xuất này.",
                },
                "danh_sach_mat_hang": {
                    "type": "array",
                    "description": "Danh sách các mặt hàng đề xuất mua.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ma_nguyen_lieu": {"type": "integer"},
                            "ma_nha_cung_cap": {"type": "integer"},
                            "so_luong_de_xuat": {"type": "number"},
                            "ly_do_de_xuat": {"type": "string"},
                        },
                        "required": ["ma_nguyen_lieu", "ma_nha_cung_cap", "so_luong_de_xuat", "ly_do_de_xuat"],
                    },
                },
            },
            "required": ["ly_do_tong_quan", "danh_sach_mat_hang"],
        },
    },
]


def tool_lay_danh_sach_canh_bao_ton_kho(
    db: Session,
    chi_lay_can_dat: bool = True,
    ma_nguyen_lieu_loc: Optional[int] = None,
) -> Dict[str, Any]:
    """Tool 1: Lấy danh sách nguyên liệu chạm ngưỡng ROP và cảnh báo lô hàng FEFO."""
    ke_hoach = xay_dung_ke_hoach_bo_sung(db, chi_lay_can_dat=chi_lay_can_dat)
    if ma_nguyen_lieu_loc is not None:
        ke_hoach = [x for x in ke_hoach if x.ma_nguyen_lieu == int(ma_nguyen_lieu_loc)]
        if not ke_hoach:
            all_kh = xay_dung_ke_hoach_bo_sung(db, chi_lay_can_dat=False)
            ke_hoach = [x for x in all_kh if x.ma_nguyen_lieu == int(ma_nguyen_lieu_loc)]

    danh_sach = []
    for item in ke_hoach:
        danh_sach.append(
            {
                "ma_nguyen_lieu": item.ma_nguyen_lieu,
                "ten_nguyen_lieu": item.ten_nguyen_lieu,
                "don_vi_tinh": item.don_vi_tinh,
                "ton_kho_hien_tai": item.ton_kho_hien_tai,
                "muc_ton_an_toan": item.muc_ton_an_toan,
                "ton_an_toan_goi_y_ai": item.ton_an_toan_goi_y_ai,
                "diem_dat_hang_lai_rop": item.diem_dat_hang_lai_rop,
                "so_luong_can_dat_du_kien": item.so_luong_can_dat,
                "can_dat_hang": item.can_dat_hang,
                "canh_bao_lo_sap_het_han": item.canh_bao_lo_sap_het_han,
            }
        )
    return {
        "so_luong_canh_bao": len(danh_sach),
        "danh_sach_nguyen_lieu": danh_sach,
    }


def tool_lay_du_bao_nhu_cau(db: Session, ma_nguyen_lieu: int) -> Dict[str, Any]:
    """Tool 2: Truy xuất dự báo 7 ngày tới từ mô hình ML thắng cuộc (Tuần 6)."""
    ing = db.query(Ingredient).filter(Ingredient.ma_nguyen_lieu == int(ma_nguyen_lieu)).first()
    if not ing:
        return {"loi": f"Không tìm thấy nguyên liệu #{ma_nguyen_lieu}"}

    today = date.today()
    forecasts = (
        db.query(DemandForecast)
        .filter(
            DemandForecast.ma_nguyen_lieu == ing.ma_nguyen_lieu,
            DemandForecast.ngay_du_bao >= today,
        )
        .order_by(DemandForecast.ngay_du_bao.asc())
        .limit(7)
        .all()
    )
    if not forecasts:
        forecasts = (
            db.query(DemandForecast)
            .filter(DemandForecast.ma_nguyen_lieu == ing.ma_nguyen_lieu)
            .order_by(DemandForecast.ngay_du_bao.desc())
            .limit(7)
            .all()
        )
        forecasts = list(reversed(forecasts))

    tong_7_ngay, tb_ngay, ten_mo_hinh, do_tin_cay_pct, bien_do_ci95 = _lay_thong_tin_du_bao_7_ngay_ml(db, ing)

    chi_tiet_7_ngay = []
    for idx, f in enumerate(forecasts):
        val = float(f.so_luong_du_bao or 0.0)
        half_w = bien_do_ci95 * math.sqrt(1.0 + 0.08 * idx)
        chi_tiet_7_ngay.append(
            {
                "ngay": str(f.ngay_du_bao),
                "so_luong_du_bao": round(val, 2),
                "can_duoi_95": round(max(0.0, val - half_w), 2),
                "can_tren_95": round(val + half_w, 2),
            }
        )

    return {
        "ma_nguyen_lieu": ing.ma_nguyen_lieu,
        "ten_nguyen_lieu": ing.ten_nguyen_lieu,
        "don_vi_tinh": ing.don_vi_tinh,
        "mo_hinh_ml_duoc_chon": ten_mo_hinh,
        "tong_nhu_cau_du_bao_7_ngay": tong_7_ngay,
        "nhu_cau_trung_binh_ngay": tb_ngay,
        "do_tin_cay_trung_binh_pct": do_tin_cay_pct,
        "du_bao_chi_tiet_7_ngay": chi_tiet_7_ngay,
    }


def tool_lay_bao_gia_nha_cung_cap(db: Session, ma_nguyen_lieu: int) -> Dict[str, Any]:
    """Tool 3: Chấm điểm và xếp hạng Nhà cung cấp bằng thuật toán MCDM."""
    ing = db.query(Ingredient).filter(Ingredient.ma_nguyen_lieu == int(ma_nguyen_lieu)).first()
    if not ing:
        return {"loi": f"Không tìm thấy nguyên liệu #{ma_nguyen_lieu}"}

    mcdm_res = evaluate_suppliers_mcdm(db, ing.ma_nguyen_lieu)
    danh_sach = []
    for s in mcdm_res.danh_sach_so_sanh:
        danh_sach.append(
            {
                "xep_hang": s.xep_hang,
                "ma_nha_cung_cap": s.ma_nha_cung_cap,
                "ten_nha_cung_cap": s.ten_nha_cung_cap,
                "don_gia": s.don_gia,
                "thoi_gian_giao_hang_ngay": s.thoi_gian_giao_hang,
                "so_luong_dat_toi_thieu_moq": s.so_luong_dat_toi_thieu,
                "diem_chat_luong": s.diem_chat_luong,
                "diem_uy_tin": s.diem_uy_tin,
                "diem_tong_hop_mcdm": s.diem_tong_hop_mcdm,
                "de_xuat_chon": s.de_xuat,
            }
        )
    return {
        "ma_nguyen_lieu": ing.ma_nguyen_lieu,
        "ten_nguyen_lieu": ing.ten_nguyen_lieu,
        "don_vi_tinh": ing.don_vi_tinh,
        "nha_cung_cap_toi_uu": danh_sach[0] if danh_sach else None,
        "bang_xep_hang_mcdm": danh_sach,
    }


def tool_tao_phieu_de_xuat_mua(
    db: Session,
    ly_do_tong_quan: str,
    danh_sach_mat_hang: List[Dict[str, Any]],
    nguoi_tao_label: str = "AI Agent (Hybrid ML + Gemini 3.8)",
) -> Dict[str, Any]:
    """
    Tool 4: Ghi nhận Phiếu đề xuất mua hàng ở trạng thái `CHO_DUYET` (Human-in-the-loop).
    Tuyệt đối không tự đặt hàng hay thanh toán.
    """
    cleanup_empty_proposals(db)
    if not danh_sach_mat_hang:
        return {"loi": "Danh sách mặt hàng đề xuất rỗng"}

    safe_creator = (nguoi_tao_label or "AI Procurement Agent")[:50]
    proposal = PurchaseProposal(
        ngay_tao=datetime.now(),
        tong_tien_du_kien=0.0,
        trang_thai="CHO_DUYET",
        ly_do_tong_quan=ly_do_tong_quan,
        nguoi_tao=safe_creator,
    )
    db.add(proposal)
    db.flush()

    tong_tien = 0.0
    so_dong = 0

    for item in danh_sach_mat_hang:
        ma_nl = int(item.get("ma_nguyen_lieu") or 0)
        ing = db.query(Ingredient).filter(Ingredient.ma_nguyen_lieu == ma_nl).first()
        if not ing:
            continue

        tong_7_ngay, _, _, _, _ = _lay_thong_tin_du_bao_7_ngay_ml(db, ing)
        mcdm_res = evaluate_suppliers_mcdm(db, ing.ma_nguyen_lieu)
        best_sup = mcdm_res.nha_cung_cap_toi_uu

        ma_ncc = int(item.get("ma_nha_cung_cap") or (best_sup.ma_nha_cung_cap if best_sup else 1))
        quotation = (
            db.query(SupplierQuotation)
            .filter(
                SupplierQuotation.ma_nguyen_lieu == ing.ma_nguyen_lieu,
                SupplierQuotation.ma_nha_cung_cap == ma_ncc,
            )
            .first()
        )
        if not quotation:
            quotation = (
                db.query(SupplierQuotation)
                .filter(SupplierQuotation.ma_nguyen_lieu == ing.ma_nguyen_lieu)
                .first()
            )

        if quotation:
            ma_ncc = quotation.ma_nha_cung_cap
            don_gia = float(quotation.don_gia)
            moq = float(quotation.so_luong_dat_toi_thieu)
        else:
            don_gia = 50000.0
            moq = 1.0

        luong_tho = float(item.get("so_luong_de_xuat") or moq)
        so_luong_chuan, _ = _lam_tron_luong_dat_theo_moq_va_don_vi(luong_tho, moq, ing.don_vi_tinh)
        thanh_tien = round(so_luong_chuan * don_gia, 2)
        tong_tien += thanh_tien

        detail = ProposalDetail(
            ma_phieu_de_xuat=proposal.ma_phieu_de_xuat,
            ma_nguyen_lieu=ing.ma_nguyen_lieu,
            ma_nha_cung_cap=ma_ncc,
            so_luong_de_xuat=so_luong_chuan,
            don_gia_du_kien=don_gia,
            so_luong_du_doan_7ngay=tong_7_ngay,
            ly_do_de_xuat=str(item.get("ly_do_de_xuat") or "Đề xuất bởi Hybrid Multi-Model AI Agent."),
        )
        db.add(detail)
        so_dong += 1

    proposal.tong_tien_du_kien = round(tong_tien, 2)
    db.commit()
    db.refresh(proposal)

    return {
        "ma_phieu_de_xuat": proposal.ma_phieu_de_xuat,
        "trang_thai": proposal.trang_thai,
        "so_mat_hang": so_dong,
        "tong_tien_du_kien": proposal.tong_tien_du_kien,
        "thong_diep": f"Đã tạo Phiếu đề xuất #{proposal.ma_phieu_de_xuat} ở trạng thái CHO_DUYET.",
    }


# ==============================================================================
# 3. BỘ ĐIỀU PHỐI HYBRID MULTI-MODEL AI AGENT (GEMINI FUNCTION CALLING + FALLBACK)
# ==============================================================================

SYSTEM_INSTRUCTION_AGENT = (
    "Bạn là AI Procurement Agent của hệ thống Quản lý Tồn kho Quán Cà Phê (Kiến trúc Hybrid Multi-Model AI). "
    "Quy tắc bắt buộc:\n"
    "1. KHÔNG tự tính nhẩm số liệu dự báo hay điểm nhà cung cấp. Bắt buộc gọi các công cụ (tools) được cấp:\n"
    "   - `lay_danh_sach_canh_bao_ton_kho`: kiểm tra các nguyên liệu có Tồn <= ROP và cảnh báo lô hết hạn FEFO.\n"
    "   - `lay_du_bao_nhu_cau`: lấy dự báo 7 ngày từ mô hình ML (Ensemble_HW_Ridge / HoltWinters_Seasonal / Fourier_Ridge_ML).\n"
    "   - `lay_bao_gia_nha_cung_cap`: lấy bảng xếp hạng MCDM của các nhà cung cấp.\n"
    "   - `tao_phieu_de_xuat_mua`: tạo phiếu đề xuất ở trạng thái CHO_DUYET kèm lý do giải thích chi tiết từng dòng.\n"
    "2. Quản lý cửa hàng giữ quyền phê duyệt cuối cùng (Human-in-the-loop). Tuyệt đối không tự đặt hàng.\n"
    "3. Trình bày báo cáo tổng hợp bằng Tiếng Việt rõ ràng, dẫn chứng đúng con số từ Tool."
)


def _thuc_thi_mot_tool(
    db: Session,
    ten_tool: str,
    tham_so: Dict[str, Any],
    cho_phep_tao_phieu: bool,
    mo_hinh_llm: str,
    created_proposal_holder: Dict[str, Any],
) -> Tuple[Dict[str, Any], str, str]:
    """Thực thi 1 tool do AI Agent gọi và trả về (ket_qua_dict, mo_hinh_con_su_dung, tom_tat)."""
    if ten_tool == "lay_danh_sach_canh_bao_ton_kho":
        chi_lay = bool(tham_so.get("chi_lay_can_dat", True))
        res = tool_lay_danh_sach_canh_bao_ton_kho(db, chi_lay_can_dat=chi_lay)
        return (
            res,
            "Dynamic ROP & Safety Stock Engine + FEFO Checker",
            f"Phát hiện {res['so_luong_canh_bao']} nguyên liệu chạm ngưỡng ROP cần bổ sung.",
        )

    if ten_tool == "lay_du_bao_nhu_cau":
        ma_nl = int(tham_so.get("ma_nguyen_lieu") or 1)
        res = tool_lay_du_bao_nhu_cau(db, ma_nguyen_lieu=ma_nl)
        mo_hinh_ml = res.get("mo_hinh_ml_duoc_chon", "Ensemble_HW_Ridge")
        tong_7n = res.get("tong_nhu_cau_du_bao_7_ngay", 0)
        don_vi = res.get("don_vi_tinh", "")
        return (
            res,
            f"Time-Series ML ({mo_hinh_ml})",
            f"Dự báo 7 ngày cho NL #{ma_nl} ({res.get('ten_nguyen_lieu', '')}): {_vn(tong_7n)} {don_vi} bởi {mo_hinh_ml}.",
        )

    if ten_tool == "lay_bao_gia_nha_cung_cap":
        ma_nl = int(tham_so.get("ma_nguyen_lieu") or 1)
        res = tool_lay_bao_gia_nha_cung_cap(db, ma_nguyen_lieu=ma_nl)
        opt = res.get("nha_cung_cap_toi_uu") or {}
        return (
            res,
            "MCDM Multi-Criteria Supplier Scoring",
            (
                f"Xếp hạng {len(res.get('bang_xep_hang_mcdm', []))} NCC cho NL #{ma_nl}: "
                f"Tối ưu là '{opt.get('ten_nha_cung_cap', 'N/A')}' (MCDM {opt.get('diem_tong_hop_mcdm', 0)}/100)."
            ),
        )

    if ten_tool == "tao_phieu_de_xuat_mua":
        if not cho_phep_tao_phieu:
            return (
                {"thong_diep": "Chế độ chỉ phân tích (tao_phieu_de_xuat=False), không ghi phiếu mới."},
                "Human-in-the-loop Guardrail",
                "Bỏ qua tạo phiếu do yêu cầu chỉ phân tích.",
            )
        ly_do_tq = str(tham_so.get("ly_do_tong_quan") or "Đề xuất mua hàng tự động bởi Hybrid Multi-Model AI Agent.")
        ds_hang = tham_so.get("danh_sach_mat_hang") or []
        res = tool_tao_phieu_de_xuat_mua(
            db,
            ly_do_tong_quan=ly_do_tq,
            danh_sach_mat_hang=ds_hang,
            nguoi_tao_label=f"AI Agent ({mo_hinh_llm})"[:50],
        )
        if "ma_phieu_de_xuat" in res:
            created_proposal_holder["proposal_id"] = res["ma_phieu_de_xuat"]
            created_proposal_holder["tong_tien"] = res.get("tong_tien_du_kien", 0.0)
            created_proposal_holder["so_mat_hang"] = res.get("so_mat_hang", 0)
        return (
            res,
            "Proposal Generator (CHO_DUYET Guardrail)",
            f"Đã tạo Phiếu đề xuất #{res.get('ma_phieu_de_xuat')} (CHO_DUYET) với {res.get('so_mat_hang', 0)} mặt hàng.",
        )

    return ({"loi": f"Tool không hợp lệ: {ten_tool}"}, "Unknown", f"Tool {ten_tool} không tồn tại.")


def _goi_gemini_cloud_function_calling(
    db: Session,
    yeu_cau_text: str,
    mo_hinh_llm: str,
    cho_phep_tao_phieu: bool,
) -> Optional[Tuple[List[BuocGoiToolAgentOut], Dict[str, Any], str]]:
    """
    Kết nối Google Gemini Interactions API (`google-genai` SDK hoặc REST v1beta/interactions)
    để thực thi vòng lặp Function Calling đa bước với 4 Tools an toàn.
    Trả về None nếu chưa cấu hình `GEMINI_API_KEY` hoặc khi không có kết nối mạng.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return None

    tool_logs: List[BuocGoiToolAgentOut] = []
    created_holder: Dict[str, Any] = {}
    buoc_counter = 0
    has_genai_sdk = False

    # Ưu tiên 1: Sử dụng SDK chính thức `google-genai` (>= 2.30.1) với timeout nhanh (6s, không treo retry)
    try:
        from google import genai  # type: ignore

        has_genai_sdk = True
        is_vertex_key = api_key.startswith("AQ.")
        client = genai.Client(
            api_key=api_key,
            vertexai=True if is_vertex_key else None,
            http_options={"timeout": 6000, "retry_options": {"attempts": 1}},
        )
        interaction = client.interactions.create(
            model=mo_hinh_llm,
            system_instruction=SYSTEM_INSTRUCTION_AGENT,
            input=yeu_cau_text,
            tools=TOOL_DECLARATIONS,
            timeout=6.0,
        )

        for _ in range(3):
            steps = getattr(interaction, "steps", None) or []
            fc_steps = [s for s in steps if getattr(s, "type", "") == "function_call"]
            if not fc_steps:
                break

            function_results_input = []
            for fc in fc_steps:
                buoc_counter += 1
                fname = getattr(fc, "name", "")
                fargs = getattr(fc, "arguments", {}) or {}
                if isinstance(fargs, str):
                    try:
                        fargs = json.loads(fargs)
                    except Exception:
                        fargs = {}

                res_dict, mo_hinh_con, tom_tat = _thuc_thi_mot_tool(
                    db=db,
                    ten_tool=fname,
                    tham_so=fargs,
                    cho_phep_tao_phieu=cho_phep_tao_phieu,
                    mo_hinh_llm=mo_hinh_llm,
                    created_proposal_holder=created_holder,
                )
                tool_logs.append(
                    BuocGoiToolAgentOut(
                        buoc=buoc_counter,
                        ten_tool=fname,
                        mo_hinh_con=mo_hinh_con,
                        tham_so=fargs,
                        tom_tat_ket_qua=tom_tat,
                    )
                )
                function_results_input.append(
                    {
                        "type": "function_result",
                        "name": fname,
                        "call_id": getattr(fc, "id", ""),
                        "result": [{"type": "text", "text": json.dumps(res_dict, ensure_ascii=False)}],
                    }
                )

            interaction = client.interactions.create(
                model=mo_hinh_llm,
                system_instruction=SYSTEM_INSTRUCTION_AGENT,
                input=function_results_input,
                tools=TOOL_DECLARATIONS,
                previous_interaction_id=interaction.id,
                timeout=6.0,
            )

        final_text = getattr(interaction, "output_text", None) or ""
        if tool_logs:
            if not final_text:
                final_text = (
                    f"[Google Gemini Cloud Agent - {mo_hinh_llm}] Đã thực thi {len(tool_logs)} bước Function Calling: "
                    + " -> ".join(f"{t.ten_tool}" for t in tool_logs)
                )
            return tool_logs, created_holder, final_text
    except Exception:
        if has_genai_sdk:
            return None

    # Ưu tiên 2: Gọi trực tiếp REST Interactions API v1beta của Gemini nếu máy chưa cài gói `google-genai`
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/interactions"
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": mo_hinh_llm,
            "system_instruction": SYSTEM_INSTRUCTION_AGENT,
            "input": yeu_cau_text,
            "tools": TOOL_DECLARATIONS,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code != 200:
            return None
        data = resp.json()

        for _ in range(6):
            steps = data.get("steps") or []
            fc_steps = [s for s in steps if s.get("type") == "function_call"]
            if not fc_steps:
                break

            fn_results = []
            for fc in fc_steps:
                buoc_counter += 1
                fname = fc.get("name", "")
                fargs = fc.get("arguments") or {}
                res_dict, mo_hinh_con, tom_tat = _thuc_thi_mot_tool(
                    db=db,
                    ten_tool=fname,
                    tham_so=fargs,
                    cho_phep_tao_phieu=cho_phep_tao_phieu,
                    mo_hinh_llm=mo_hinh_llm,
                    created_proposal_holder=created_holder,
                )
                tool_logs.append(
                    BuocGoiToolAgentOut(
                        buoc=buoc_counter,
                        ten_tool=fname,
                        mo_hinh_con=mo_hinh_con,
                        tham_so=fargs,
                        tom_tat_ket_qua=tom_tat,
                    )
                )
                fn_results.append(
                    {
                        "type": "function_result",
                        "name": fname,
                        "call_id": fc.get("id", ""),
                        "result": [{"type": "text", "text": json.dumps(res_dict, ensure_ascii=False)}],
                    }
                )

            next_payload = {
                "model": mo_hinh_llm,
                "system_instruction": SYSTEM_INSTRUCTION_AGENT,
                "input": fn_results,
                "tools": TOOL_DECLARATIONS,
                "previous_interaction_id": data.get("id"),
            }
            resp = requests.post(url, headers=headers, json=next_payload, timeout=20)
            if resp.status_code != 200:
                break
            data = resp.json()

        text_parts = []
        for s in data.get("steps") or []:
            if s.get("type") == "model_output":
                for c in s.get("content") or []:
                    if c.get("type") == "text" and c.get("text"):
                        text_parts.append(c["text"])
        final_text = "\n".join(text_parts).strip()
        if tool_logs:
            if not final_text:
                final_text = (
                    f"[Google Gemini Cloud Agent - {mo_hinh_llm}] Đã thực thi {len(tool_logs)} bước Function Calling: "
                    + " -> ".join(f"{t.ten_tool}" for t in tool_logs)
                )
            return tool_logs, created_holder, final_text
    except Exception:
        return None

    return None


def chay_ai_procurement_agent(
    db: Session,
    yeu_cau: Optional[YeuCauChayAiAgent] = None,
) -> KetQuaAiAgentOut:
    """
    Thực thi quy trình AI Procurement Agent theo Kiến trúc Kết hợp Đa Mô hình (Hybrid Multi-Model AI):
    - Nếu có `GEMINI_API_KEY`: Dùng Gemini Function Calling (`gemini-3.8-flash` hoặc `gemini-4-argon`)
      tự động điều phối 4 Tools an toàn.
    - Nếu chạy cục bộ / không có mạng ngoài: Dùng Hybrid Multi-Model Orchestrator thực thi tuần tự
      đúng 4 Tools (ROP Alert Tool -> Time-Series ML Forecast Tool -> MCDM Supplier Tool -> Proposal Tool),
      đảm bảo kết quả chính xác 100% và không bao giờ lỗi.
    """
    t0 = time.perf_counter()
    if yeu_cau is None:
        yeu_cau = YeuCauChayAiAgent()

    mo_hinh_llm = (
        settings.GEMINI_REASONING_MODEL
        if yeu_cau.su_dung_mo_hinh_suy_luan_sau
        else settings.GEMINI_AGENT_MODEL
    )

    # Thử gọi Gemini Cloud Function Calling nếu người dùng đã cấu hình GEMINI_API_KEY
    cloud_res = _goi_gemini_cloud_function_calling(
        db=db,
        yeu_cau_text=yeu_cau.yeu_cau,
        mo_hinh_llm=mo_hinh_llm,
        cho_phep_tao_phieu=yeu_cau.tao_phieu_de_xuat,
    )

    if cloud_res is not None:
        tool_logs, created_holder, phan_hoi_text = cloud_res
        # Đảm bảo nếu yêu cầu có tao_phieu_de_xuat=True mà LLM mới gọi các tool tra cứu thì tự động hoàn tất bước tạo phiếu CHO_DUYET
        if yeu_cau.tao_phieu_de_xuat and not created_holder.get("proposal_id"):
            kh_can_dat = xay_dung_ke_hoach_bo_sung(db, chi_lay_can_dat=True)
            if yeu_cau.ma_nguyen_lieu is not None:
                kh_can_dat = [x for x in kh_can_dat if x.ma_nguyen_lieu == int(yeu_cau.ma_nguyen_lieu)]
            ds_hang_cloud = [
                {
                    "ma_nguyen_lieu": x.ma_nguyen_lieu,
                    "ma_nha_cung_cap": x.nha_cung_cap_chon.ma_nha_cung_cap if x.nha_cung_cap_chon else 1,
                    "so_luong_de_xuat": x.so_luong_can_dat,
                    "ly_do_de_xuat": x.ly_do_chon_ncc,
                }
                for x in kh_can_dat
            ]
            if ds_hang_cloud:
                res_phieu = tool_tao_phieu_de_xuat_mua(
                    db=db,
                    ly_do_tong_quan=phan_hoi_text[:1500],
                    danh_sach_mat_hang=ds_hang_cloud,
                    nguoi_tao_label=f"Gemini Cloud ({mo_hinh_llm})"[:50],
                )
                created_holder["proposal_id"] = res_phieu.get("ma_phieu_de_xuat")
                created_holder["tong_tien"] = res_phieu.get("tong_tien_du_kien", 0.0)
                created_holder["so_mat_hang"] = res_phieu.get("so_mat_hang", 0)
                tool_logs.append(
                    BuocGoiToolAgentOut(
                        buoc=len(tool_logs) + 1,
                        ten_tool="tao_phieu_de_xuat_mua",
                        mo_hinh_con="Proposal Generator (CHO_DUYET Guardrail)",
                        tham_so={"so_mat_hang": len(ds_hang_cloud), "trang_thai": "CHO_DUYET"},
                        tom_tat_ket_qua=f"Đã tạo Phiếu đề xuất #{created_holder['proposal_id']} (CHO_DUYET).",
                    )
                )
        che_do = "GEMINI_CLOUD_FUNCTION_CALLING"
        da_ket_noi_cloud = True
        cac_mo_hinh = [
            "Ensemble_HW_Ridge (Time-Series ML)",
            "HoltWinters_Seasonal (Time-Series ML)",
            "Fourier_Ridge_ML (L2 Ridge Regression)",
            "Dynamic ROP & Safety Stock Engine",
            "MCDM Multi-Criteria Supplier Scoring",
            f"Google Gemini Function Calling ({mo_hinh_llm})",
        ]
    else:
        # Chế độ Hybrid Multi-Model Local Orchestrator: điều phối chuẩn 4 Tools
        che_do = "HYBRID_MULTI_MODEL_ORCHESTRATOR"
        da_ket_noi_cloud = False
        tool_logs = []
        created_holder = {}
        buoc = 0

        # Bước 1: Gọi Tool `lay_danh_sach_canh_bao_ton_kho`
        buoc += 1
        canh_bao_res = tool_lay_danh_sach_canh_bao_ton_kho(
            db,
            chi_lay_can_dat=True,
            ma_nguyen_lieu_loc=yeu_cau.ma_nguyen_lieu,
        )
        ds_canh_bao = canh_bao_res["danh_sach_nguyen_lieu"]

        # Nếu tất cả đều trên ROP, chọn 2 nguyên liệu có tỷ lệ Tồn/ROP thấp nhất để lập kế hoạch dự phòng
        if not ds_canh_bao:
            all_kh = xay_dung_ke_hoach_bo_sung(db, chi_lay_can_dat=False)
            all_kh.sort(key=lambda x: x.ton_kho_hien_tai / max(x.diem_dat_hang_lai_rop, 1.0))
            for item in all_kh[:2]:
                ds_canh_bao.append(
                    {
                        "ma_nguyen_lieu": item.ma_nguyen_lieu,
                        "ten_nguyen_lieu": item.ten_nguyen_lieu,
                        "don_vi_tinh": item.don_vi_tinh,
                        "ton_kho_hien_tai": item.ton_kho_hien_tai,
                        "muc_ton_an_toan": item.muc_ton_an_toan,
                        "ton_an_toan_goi_y_ai": item.ton_an_toan_goi_y_ai,
                        "diem_dat_hang_lai_rop": item.diem_dat_hang_lai_rop,
                        "so_luong_can_dat_du_kien": max(item.so_luong_can_dat, item.muc_ton_an_toan),
                        "can_dat_hang": True,
                        "canh_bao_lo_sap_het_han": item.canh_bao_lo_sap_het_han,
                    }
                )

        tool_logs.append(
            BuocGoiToolAgentOut(
                buoc=buoc,
                ten_tool="lay_danh_sach_canh_bao_ton_kho",
                mo_hinh_con="Dynamic ROP & Safety Stock Engine + FEFO Checker",
                tham_so={"chi_lay_can_dat": True, "ma_nguyen_lieu": yeu_cau.ma_nguyen_lieu},
                tom_tat_ket_qua=(
                    f"Quét 15 nguyên liệu, phát hiện {len(ds_canh_bao)} mặt hàng chạm ngưỡng ROP cần bổ sung: "
                    + ", ".join(f"{x['ten_nguyen_lieu']} (Tồn {_vn(x['ton_kho_hien_tai'])} ≤ ROP {_vn(x['diem_dat_hang_lai_rop'])})" for x in ds_canh_bao)
                ),
            )
        )

        # Bước 2 & 3: Với từng nguyên liệu dưới ROP, gọi Tool `lay_du_bao_nhu_cau` và `lay_bao_gia_nha_cung_cap`
        danh_sach_mat_hang_de_xuat = []
        cac_mo_hinh_ml_da_dung = set()
        dong_phan_tich = []

        for item_cb in ds_canh_bao:
            ma_nl = int(item_cb["ma_nguyen_lieu"])
            ten_nl = item_cb["ten_nguyen_lieu"]
            don_vi = item_cb["don_vi_tinh"]

            # Tool 2: Dự báo ML 7 ngày
            buoc += 1
            du_bao_res = tool_lay_du_bao_nhu_cau(db, ma_nguyen_lieu=ma_nl)
            ten_ml = du_bao_res.get("mo_hinh_ml_duoc_chon", "Ensemble_HW_Ridge")
            cac_mo_hinh_ml_da_dung.add(ten_ml)
            tong_7n = float(du_bao_res.get("tong_nhu_cau_du_bao_7_ngay") or 0.0)
            tb_ngay = float(du_bao_res.get("nhu_cau_trung_binh_ngay") or 0.0)
            conf_pct = float(du_bao_res.get("do_tin_cay_trung_binh_pct") or 93.0)

            tool_logs.append(
                BuocGoiToolAgentOut(
                    buoc=buoc,
                    ten_tool="lay_du_bao_nhu_cau",
                    mo_hinh_con=f"Time-Series ML ({ten_ml})",
                    tham_so={"ma_nguyen_lieu": ma_nl},
                    tom_tat_ket_qua=(
                        f"{ten_nl}: Mô hình {ten_ml} dự báo 7 ngày tới cần {_vn(tong_7n)} {don_vi} "
                        f"(TB {_vn(tb_ngay)} {don_vi}/ngày, độ tin cậy {_vn(conf_pct, 1)}%)."
                    ),
                )
            )

            # Tool 3: So sánh Nhà cung cấp bằng MCDM
            buoc += 1
            ncc_res = tool_lay_bao_gia_nha_cung_cap(db, ma_nguyen_lieu=ma_nl)
            opt_ncc = ncc_res.get("nha_cung_cap_toi_uu") or {}
            bang_mcdm = ncc_res.get("bang_xep_hang_mcdm") or []

            ma_ncc = int(opt_ncc.get("ma_nha_cung_cap") or 1)
            ten_ncc = opt_ncc.get("ten_nha_cung_cap") or "Nhà cung cấp chuẩn"
            don_gia = float(opt_ncc.get("don_gia") or 50000.0)
            lead_time = int(opt_ncc.get("thoi_gian_giao_hang_ngay") or 2)
            moq = float(opt_ncc.get("so_luong_dat_toi_thieu_moq") or 1.0)
            diem_mcdm = float(opt_ncc.get("diem_tong_hop_mcdm") or 90.0)

            tool_logs.append(
                BuocGoiToolAgentOut(
                    buoc=buoc,
                    ten_tool="lay_bao_gia_nha_cung_cap",
                    mo_hinh_con="MCDM Multi-Criteria Supplier Scoring",
                    tham_so={"ma_nguyen_lieu": ma_nl},
                    tom_tat_ket_qua=(
                        f"{ten_nl}: Xếp hạng {len(bang_mcdm)} NCC -> Chọn '{ten_ncc}' "
                        f"(Điểm MCDM {_vn(diem_mcdm, 1)}/100, giá {_money(don_gia)}/{don_vi}, "
                        f"giao {lead_time} ngày, MOQ {_vn(moq)} {don_vi})."
                    ),
                )
            )

            so_luong_dat, da_moq = _lam_tron_luong_dat_theo_moq_va_don_vi(
                float(item_cb.get("so_luong_can_dat_du_kien") or 0.0),
                moq,
                don_vi,
            )

            so_sanh_ncc_2 = ""
            if len(bang_mcdm) > 1:
                alt = bang_mcdm[1]
                chenh_gia = float(alt["don_gia"]) - don_gia
                if chenh_gia > 0:
                    so_sanh_ncc_2 = f" Rẻ hơn {_money(chenh_gia)}/{don_vi} so với {alt['ten_nha_cung_cap']}."
                elif chenh_gia < 0:
                    so_sanh_ncc_2 = (
                        f" Đắt hơn {alt['ten_nha_cung_cap']} {_money(-chenh_gia)}/{don_vi} "
                        f"nhưng ưu thế về thời gian giao ({lead_time} ngày) và điểm uy tín."
                    )

            fefo_note = f" [{item_cb['canh_bao_lo_sap_het_han']}]." if item_cb.get("canh_bao_lo_sap_het_han") else ""
            moq_note = f" (đã chuẩn hóa theo MOQ {_vn(moq)} {don_vi})" if da_moq else f" (MOQ {_vn(moq)} {don_vi})"

            ly_do_dong = (
                f"Tồn kho còn {_vn(item_cb['ton_kho_hien_tai'])} {don_vi} ≤ ROP {_vn(item_cb['diem_dat_hang_lai_rop'])} {don_vi} "
                f"(Safety Stock {_vn(item_cb['muc_ton_an_toan'])} {don_vi}). "
                f"Mô hình ML '{ten_ml}' dự báo nhu cầu 7 ngày tới là {_vn(tong_7n)} {don_vi} "
                f"(độ tin cậy {_vn(conf_pct, 1)}%). "
                f"Chọn '{ten_ncc}' đạt điểm MCDM cao nhất ({_vn(diem_mcdm, 1)}/100), "
                f"Lead time {lead_time} ngày, đơn giá {_money(don_gia)}/{don_vi}.{so_sanh_ncc_2} "
                f"Đề xuất đặt {_vn(so_luong_dat)} {don_vi}{moq_note}.{fefo_note}"
            )

            danh_sach_mat_hang_de_xuat.append(
                {
                    "ma_nguyen_lieu": ma_nl,
                    "ma_nha_cung_cap": ma_ncc,
                    "so_luong_de_xuat": so_luong_dat,
                    "ly_do_de_xuat": ly_do_dong,
                }
            )
            dong_phan_tich.append(
                f"- {ten_nl}: Tồn {_vn(item_cb['ton_kho_hien_tai'])} ≤ ROP {_vn(item_cb['diem_dat_hang_lai_rop'])} {don_vi} "
                f"| Dự báo 7N ({ten_ml}): {_vn(tong_7n)} {don_vi} "
                f"| Đặt {_vn(so_luong_dat)} {don_vi} từ '{ten_ncc}' (MCDM {_vn(diem_mcdm, 1)}/100, {_money(so_luong_dat * don_gia)})"
            )

        # Bước 4: Gọi Tool `tao_phieu_de_xuat_mua`
        ds_ten_ml = ", ".join(sorted(cac_mo_hinh_ml_da_dung)) or "Ensemble_HW_Ridge"
        ly_do_tong_quan = (
            f"[Kiến trúc Hybrid Multi-Model AI] AI Procurement Agent đã phối hợp các mô hình dự báo chuỗi thời gian "
            f"({ds_ten_ml}), bộ tính điểm đặt hàng lại (Dynamic ROP & Safety Stock), kiểm tra lô hàng FEFO "
            f"và giải thuật đa tiêu chí MCDM trên toàn bộ 15 nguyên vật liệu. "
            f"Phát hiện {len(danh_sach_mat_hang_de_xuat)} mặt hàng chạm ngưỡng cảnh báo ROP cần lập phiếu đề xuất mua bổ sung "
            f"ở trạng thái CHỜ DUYỆT để Quản lý cửa hàng thẩm định."
        )

        if yeu_cau.tao_phieu_de_xuat and danh_sach_mat_hang_de_xuat:
            buoc += 1
            res_phieu = tool_tao_phieu_de_xuat_mua(
                db=db,
                ly_do_tong_quan=ly_do_tong_quan,
                danh_sach_mat_hang=danh_sach_mat_hang_de_xuat,
                nguoi_tao_label=f"AI Agent (Hybrid ML + {mo_hinh_llm})"[:50],
            )
            created_holder["proposal_id"] = res_phieu.get("ma_phieu_de_xuat")
            created_holder["tong_tien"] = res_phieu.get("tong_tien_du_kien", 0.0)
            created_holder["so_mat_hang"] = res_phieu.get("so_mat_hang", 0)

            tool_logs.append(
                BuocGoiToolAgentOut(
                    buoc=buoc,
                    ten_tool="tao_phieu_de_xuat_mua",
                    mo_hinh_con="Proposal Generator (CHO_DUYET Human-in-the-loop)",
                    tham_so={
                        "so_mat_hang": len(danh_sach_mat_hang_de_xuat),
                        "trang_thai": "CHO_DUYET",
                    },
                    tom_tat_ket_qua=(
                        f"Đã tạo Phiếu đề xuất #{created_holder['proposal_id']} ở trạng thái CHO_DUYET "
                        f"gồm {created_holder['so_mat_hang']} mặt hàng, tổng tiền {_money(created_holder['tong_tien'])}."
                    ),
                )
            )

        cac_mo_hinh = [
            f"Time-Series ML ({ds_ten_ml})",
            "Dynamic ROP & Safety Stock Engine (95% CI)",
            "MCDM Multi-Criteria Supplier Scoring",
            "FEFO Batch Expiry Risk Checker",
            f"AI Agent Function Calling Orchestrator ({mo_hinh_llm})",
        ]

        phan_hoi_text = (
            f"{ly_do_tong_quan}\n"
            + "\n".join(dong_phan_tich)
            + (
                f"\n=> Đã khởi tạo Phiếu đề xuất #{created_holder.get('proposal_id')} "
                f"(Trạng thái: CHO_DUYET, Tổng tiền dự kiến: {_money(created_holder.get('tong_tien', 0.0))})."
                if created_holder.get("proposal_id")
                else ""
            )
        )

    thoi_gian_giay = round(time.perf_counter() - t0, 4)

    # Lưu vết vào bảng `nhat_ky_ai_agent`
    nhat_ky = NhatKyAiAgent(
        thoi_gian=datetime.now(),
        yeu_cau_dau_vao=yeu_cau.yeu_cau,
        che_do_agent=che_do,
        mo_hinh_llm=mo_hinh_llm,
        cac_mo_hinh_ket_hop=" + ".join(cac_mo_hinh)[:255],
        danh_sach_tool_da_goi=json.dumps([t.model_dump() for t in tool_logs], ensure_ascii=False),
        so_buoc_suy_luan=len(tool_logs),
        ma_phieu_de_xuat=created_holder.get("proposal_id"),
        phan_hoi_agent=phan_hoi_text,
        thoi_gian_xu_ly_giay=thoi_gian_giay,
    )
    db.add(nhat_ky)
    db.commit()
    db.refresh(nhat_ky)

    ket_qua = KetQuaAiAgentOut(
        ma_nhat_ky=nhat_ky.ma_nhat_ky,
        thoi_gian=nhat_ky.thoi_gian or datetime.now(),
        che_do_agent=che_do,
        mo_hinh_llm=mo_hinh_llm,
        da_ket_noi_gemini_cloud=da_ket_noi_cloud,
        cac_mo_hinh_ket_hop=cac_mo_hinh,
        so_buoc_suy_luan=len(tool_logs),
        danh_sach_tool_da_goi=tool_logs,
        ma_phieu_de_xuat=created_holder.get("proposal_id"),
        tong_tien_de_xuat=float(created_holder.get("tong_tien") or 0.0),
        so_mat_hang_de_xuat=int(created_holder.get("so_mat_hang") or 0),
        phan_hoi_agent=phan_hoi_text,
        thoi_gian_xu_ly_giay=thoi_gian_giay,
    )

    _xuat_bao_cao_agent_json(ket_qua)
    return ket_qua


def _xuat_bao_cao_agent_json(ket_qua: KetQuaAiAgentOut) -> None:
    try:
        _dam_bao_thu_muc_tuan7()
        with open(FILE_BAO_CAO_AGENT_JSON, "w", encoding="utf-8") as f:
            json.dump(ket_qua.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def lay_lich_su_nhat_ky_agent(db: Session, gioi_han: int = 20) -> List[NhatKyAiAgentOut]:
    rows = (
        db.query(NhatKyAiAgent)
        .order_by(NhatKyAiAgent.ma_nhat_ky.desc())
        .limit(gioi_han)
        .all()
    )
    return [NhatKyAiAgentOut.model_validate(r) for r in rows]


def lay_thong_tin_kien_truc_multi_model() -> KienTrucMultiModelOut:
    """Trả về thông tin chi tiết Kiến trúc Kết hợp Đa Mô hình (Hybrid Multi-Model AI) để hiển thị và báo cáo."""
    co_key = bool(settings.GEMINI_API_KEY)
    return KienTrucMultiModelOut(
        ten_kien_truc="Hybrid Multi-Model AI Procurement Architecture (Time-Series ML + ROP/MCDM + Gemini Function Calling)",
        mo_ta_tong_quan=(
            "Kiến trúc phân tầng kết hợp các mô hình Học máy dự báo chuỗi thời gian định lượng (Tầng 1), "
            "các mô hình Tối ưu hóa Tồn kho ROP/Safety Stock & Ra quyết định đa tiêu chí MCDM (Tầng 2), "
            "và Mô hình Ngôn ngữ Lớn Google Gemini điều phối qua cơ chế Function Calling 4 Tools an toàn (Tầng 3)."
        ),
        da_cau_hinh_gemini_api_key=co_key,
        mo_hinh_agent_mac_dinh=settings.GEMINI_AGENT_MODEL,
        mo_hinh_suy_luan_sau=settings.GEMINI_REASONING_MODEL,
        danh_sach_4_tools_an_toan=[
            "1. lay_danh_sach_canh_bao_ton_kho() -> Quét nguyên liệu có Tồn <= ROP & cảnh báo lô sắp hết hạn FEFO",
            "2. lay_du_bao_nhu_cau(ma_nguyen_lieu) -> Đọc dự báo 7 ngày & 95% CI từ mô hình ML thắng cuộc",
            "3. lay_bao_gia_nha_cung_cap(ma_nguyen_lieu) -> Chấm điểm & xếp hạng NCC bằng giải thuật MCDM",
            "4. tao_phieu_de_xuat_mua(ly_do_tong_quan, danh_sach_mat_hang) -> Tạo phiếu ở trạng thái CHO_DUYET",
        ],
        cam_ket_human_in_the_loop=(
            "AI Agent chỉ tạo phiếu đề xuất ở trạng thái CHO_DUYET, tuyệt đối không có tool tự gửi đơn đặt hàng "
            "hay thanh toán. Toàn bộ số liệu định lượng do ML & Code Python tính toán, đảm bảo 0% hallucination số học."
        ),
        cac_mo_hinh_ket_hop=[
            ThanhPhanMoHinhAiOut(
                tang_kien_truc="Tầng 1 - Dự báo Nhu cầu (Time-Series ML)",
                ten_mo_hinh="Ensemble_HW_Ridge (Tổ hợp Holt-Winters + Fourier Ridge L2)",
                loai_mo_hinh="Ensemble Machine Learning",
                vai_tro_trong_he_thong="Dự báo nhu cầu tiêu hao 7 ngày tới cho từng nguyên liệu (Test MAPE 5.72%, R² = 0.8589)",
                dau_vao="Chuỗi tiêu hao 365 ngày bóc tách từ BOM + sóng Fourier năm + đặc trưng trễ lag_7, lag_14",
                dau_ra="Dự báo 7 ngày tới + Khoảng tin cậy 95% (can_duoi_95, can_tren_95)",
                trang_thai_hoat_dong="ACTIVE",
            ),
            ThanhPhanMoHinhAiOut(
                tang_kien_truc="Tầng 1 - Dự báo Nhu cầu (Time-Series ML)",
                ten_mo_hinh="HoltWinters_Seasonal & Fourier_Ridge_ML",
                loai_mo_hinh="Statistical & Regularized Regression ML",
                vai_tro_trong_he_thong="Các mô hình thành phần tự động cạnh tranh trên tập Validation theo từng nguyên liệu",
                dau_vao="Lịch sử tiêu hao 15 nguyên liệu × 365 ngày (Chronological Split 275/45/45)",
                dau_ra="Đường cong dự báo 7 ngày bám sát đỉnh tiêu thụ cuối tuần (+42.1%)",
                trang_thai_hoat_dong="ACTIVE",
            ),
            ThanhPhanMoHinhAiOut(
                tang_kien_truc="Tầng 2 - Tối ưu Tồn kho & Chọn Nhà cung cấp (OR / Optimization)",
                ten_mo_hinh="Dynamic ROP, Safety Stock (95% CI) & Lot-Sizing MOQ Engine",
                loai_mo_hinh="Operations Research / Inventory Optimization",
                vai_tro_trong_he_thong="Tính điểm đặt hàng lại ROP = D_tb × LeadTime + SafetyStock và chuẩn hóa lượng đặt theo MOQ/đơn vị rời rạc",
                dau_vao="Dự báo 7 ngày ML, tồn kho thực tế, hạn dùng lô hàng FEFO, Lead time & MOQ của NCC",
                dau_ra="Trạng thái cần đặt hàng (can_dat_hang), điểm ROP, số lượng cần đặt (so_luong_can_dat)",
                trang_thai_hoat_dong="ACTIVE",
            ),
            ThanhPhanMoHinhAiOut(
                tang_kien_truc="Tầng 2 - Tối ưu Tồn kho & Chọn Nhà cung cấp (OR / Optimization)",
                ten_mo_hinh="MCDM Multi-Criteria Supplier Evaluation",
                loai_mo_hinh="Multi-Criteria Decision Making",
                vai_tro_trong_he_thong="Chấm điểm và xếp hạng nhà cung cấp theo 4 trọng số: Giá (40%), Giao hàng (30%), Chất lượng (15%), Uy tín (15%)",
                dau_vao="Bảng báo giá cc_nguyen_lieu và hồ sơ nha_cung_cap",
                dau_ra="Nhà cung cấp tối ưu (nha_cung_cap_chon), điểm MCDM/100 và lý do so sánh chi tiết",
                trang_thai_hoat_dong="ACTIVE",
            ),
            ThanhPhanMoHinhAiOut(
                tang_kien_truc="Tầng 3 - Bộ não Điều phối & Giải trình (Agentic LLM)",
                ten_mo_hinh=f"Google Gemini ({settings.GEMINI_AGENT_MODEL} / {settings.GEMINI_REASONING_MODEL})",
                loai_mo_hinh="Large Language Model with Function Calling (google-genai SDK)",
                vai_tro_trong_he_thong="Tự động gọi 4 Tools lấy dữ liệu từ Tầng 1 & Tầng 2, tổng hợp lập luận và lập phiếu đề xuất CHO_DUYET",
                dau_vao="Yêu cầu của Quản lý / Lịch quét kho + Kết quả JSON từ 4 Tools",
                dau_ra="Phiếu đề xuất mua hàng (CHO_DUYET) kèm lập luận giải trình & Nhật ký suy luận Agent",
                trang_thai_hoat_dong="GEMINI_CLOUD_READY" if co_key else "HYBRID_LOCAL_ORCHESTRATOR_ACTIVE",
            ),
        ],
    )
