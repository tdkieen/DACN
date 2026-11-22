"""
Dịch vụ Huấn luyện, Đánh giá Mô hình & Dự báo Nhu cầu Nguyên liệu AI (Tuần 6)
Phụ trách: Ngô Kế Nhật Trường - 2380602390 (Kỹ sư Dữ liệu & Trí tuệ nhân tạo)

Quy trình chuẩn Học máy Chuỗi thời gian (Time-Series ML Pipeline):
1. Đọc chuỗi thời gian tiêu hao nguyên liệu 12 tháng từ bảng `tieu_hao_nguyen_lieu_ngay` (Tuần 5).
2. Chẩn đoán chuỗi thời gian: kiểm tra khuyết thiếu, tự tương quan (ACF lag 1, lag 7),
   tính mùa vụ cuối tuần/tháng và kiểm định tính dừng.
3. Chia tập dữ liệu nghiêm ngặt theo thứ tự thời gian (Chronological Split):
   - Tập Huấn luyện (Train): ~75% (275 ngày đầu)
   - Tập Kiểm định (Validation): ~12.5% (45 ngày kế tiếp) -> tinh chỉnh siêu tham số & chọn mô hình
   - Tập Kiểm thử Độc lập (Holdout Test): ~12.5% (45 ngày cuối) -> đánh giá khách quan không thiên lệch
4. Đánh giá công bằng 5 mô hình theo cơ chế Rolling-Origin 7-Day Horizon (dự báo 7 ngày liên tiếp
   tại mỗi mốc mà tuyệt đối không rò rỉ dữ liệu tương lai):
   - Baseline_MA7: Trung bình trượt 7 ngày (Baseline bắt buộc)
   - Seasonal_Naive_7D: Giá trị cùng thứ tuần trước (Seasonal Baseline)
   - HoltWinters_Seasonal: San bằng mũ bậc 3 Holt-Winters chu kỳ tuần nhân (m=7) + xu hướng giảm chấn
   - Fourier_Ridge_ML: Hồi quy Ridge L2 kết hợp đặc trưng xu hướng, mùa vụ tuần, sóng Fourier năm & biến trễ
   - Ensemble_HW_Ridge: Tổ hợp có trọng số tối ưu giữa Holt-Winters và Fourier Ridge
5. Chọn mô hình tốt nhất trên Validation, đối sánh MAE/RMSE/MAPE/sMAPE/R2 + khoảng tin cậy Bootstrap 95%
   + phân tích lát cắt Ngày thường vs Cuối tuần trên tập Test.
6. Huấn luyện lại mô hình thắng cuộc trên 100% dữ liệu 365 ngày để sinh dự báo 7 ngày tới
   (kèm khoảng tin cậy 95%) cho toàn bộ 15/15 nguyên liệu, nạp vào bảng `du_bao_nhu_cau` và xuất báo cáo CSV/JSON.
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
import statistics
import time
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.forecast import DemandForecast, KetQuaDanhGiaMoHinh, LanChayMoHinh
from app.models.ingredient import Ingredient
from app.models.recipe import TieuHaoNguyenLieuNgay
from app.schemas.du_bao_ai import (
    BaoCaoTongQuanDuBaoAIOut,
    ChanDoanChuoiThoiGianOut,
    ChiTietDuBaoNguyenLieuOut,
    DiemDuBaoChiTietOut,
    DiemKiemThuThucTeVsDuBaoOut,
    DuBao7NgayNguyenLieuOut,
    KetQuaSoSanhMoHinhOut,
    LanChayMoHinhOut,
    TongHopMoHinhToanCucOut,
)
from app.services.dich_vu_dinh_muc_bom import chay_quy_trinh_boc_tach_bom

THU_MUC_DU_BAO_AI = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "du_lieu",
    "du_bao_ai",
)
FILE_DU_BAO_7_NGAY = os.path.join(THU_MUC_DU_BAO_AI, "du_bao_nhu_cau_7_ngay.csv")
FILE_SO_SANH_MO_HINH = os.path.join(THU_MUC_DU_BAO_AI, "bang_so_sanh_mo_hinh_tuan6.csv")
FILE_BAO_CAO_JSON = os.path.join(THU_MUC_DU_BAO_AI, "bao_cao_huan_luyen_tuan6.json")

NHAN_THU_VN = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]

THU_TU_MO_HINH = [
    ("Baseline_MA7", "BASELINE"),
    ("Seasonal_Naive_7D", "BASELINE"),
    ("HoltWinters_Seasonal", "ML"),
    ("Fourier_Ridge_ML", "ML"),
    ("Ensemble_HW_Ridge", "ML"),
]


def _dam_bao_thu_muc_du_bao() -> None:
    os.makedirs(THU_MUC_DU_BAO_AI, exist_ok=True)


# ==============================================================================
# 1. CÁC HÀM TOÁN HỌC, ĐẠI SỐ TUYẾN TÍNH & ĐỘ ĐO SAI SỐ (KHÔNG PHỤ THUỘC THƯ VIỆN C)
# ==============================================================================

def _giai_he_phuong_trinh_tuyen_tinh(A: List[List[float]], b: List[float]) -> List[float]:
    """Giải hệ phương trình tuyến tính Ax = b bằng khử Gauss có chọn phần tử trụ (Partial Pivoting)."""
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]

    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[pivot_row][col]) < 1e-12:
            M[col][col] = 1e-8
            continue
        if pivot_row != col:
            M[col], M[pivot_row] = M[pivot_row], M[col]

        pivot_val = M[col][col]
        for j in range(col, n + 1):
            M[col][j] /= pivot_val

        for r in range(col + 1, n):
            factor = M[r][col]
            if factor == 0.0:
                continue
            for j in range(col, n + 1):
                M[r][j] -= factor * M[col][j]

    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = M[i][n]
        for j in range(i + 1, n):
            s -= M[i][j] * x[j]
        x[i] = s
    return x


def _tinh_tu_tuong_quan(values: List[float], lag: int) -> float:
    """Tính hệ số tự tương quan Pearson tại độ trễ `lag` (ACF)."""
    n = len(values)
    if n <= lag + 2:
        return 0.0
    mean_v = sum(values) / n
    denom = sum((v - mean_v) ** 2 for v in values)
    if denom <= 1e-12:
        return 0.0
    num = sum((values[i] - mean_v) * (values[i - lag] - mean_v) for i in range(lag, n))
    return round(num / denom, 4)


def _tinh_chi_so_sai_so(
    actuals: List[float],
    preds: List[float],
    dows: Optional[List[int]] = None,
) -> Dict[str, float]:
    """Tính MAE, RMSE, MAPE (%), sMAPE (%), R², độ lệch chuẩn phần dư và lát cắt Ngày thường/Cuối tuần."""
    n = len(actuals)
    if n == 0:
        return {
            "mae": 0.0,
            "rmse": 0.0,
            "mape": 0.0,
            "smape": 0.0,
            "r2": 0.0,
            "residual_std": 0.0,
            "mape_ngay_thuong": 0.0,
            "mape_cuoi_tuan": 0.0,
        }

    abs_errs: List[float] = []
    sq_errs: List[float] = []
    pct_errs: List[float] = []
    smape_errs: List[float] = []
    residuals: List[float] = []
    wd_pct: List[float] = []
    we_pct: List[float] = []

    for i, (y, yhat) in enumerate(zip(actuals, preds)):
        err = y - yhat
        ae = abs(err)
        abs_errs.append(ae)
        sq_errs.append(err * err)
        residuals.append(err)

        denom = max(abs(y), 1e-6)
        ape = (ae / denom) * 100.0
        pct_errs.append(ape)
        smape_denom = max((abs(y) + abs(yhat)) / 2.0, 1e-6)
        smape_errs.append((ae / smape_denom) * 100.0)

        if dows is not None:
            if dows[i] >= 5:
                we_pct.append(ape)
            else:
                wd_pct.append(ape)

    mean_y = sum(actuals) / n
    ss_tot = sum((y - mean_y) ** 2 for y in actuals)
    ss_res = sum(sq_errs)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0
    res_std = statistics.stdev(residuals) if n > 1 else 0.0

    return {
        "mae": round(sum(abs_errs) / n, 4),
        "rmse": round(math.sqrt(ss_res / n), 4),
        "mape": round(sum(pct_errs) / n, 2),
        "smape": round(sum(smape_errs) / n, 2),
        "r2": round(r2, 4),
        "residual_std": round(res_std, 4),
        "mape_ngay_thuong": round(sum(wd_pct) / len(wd_pct), 2) if wd_pct else 0.0,
        "mape_cuoi_tuan": round(sum(we_pct) / len(we_pct), 2) if we_pct else 0.0,
    }


def _tinh_bootstrap_ci_95(values: List[float], n_boot: int = 200, seed: int = 42) -> List[float]:
    """Tính khoảng tin cậy 95% bằng phương pháp Bootstrap lặp lại có hoàn lại."""
    if not values:
        return [0.0, 0.0]
    if len(values) == 1:
        v = round(values[0], 2)
        return [v, v]
    rng = random.Random(seed)
    n = len(values)
    means: List[float] = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    low_idx = max(0, int(0.025 * n_boot))
    high_idx = min(n_boot - 1, int(0.975 * n_boot))
    return [round(means[low_idx], 2), round(means[high_idx], 2)]


# ==============================================================================
# 2. CHẨN ĐOÁN CHUỖI THỜI GIAN & CHUẨN HÓA DỮ LIỆU ĐẦU VÀO
# ==============================================================================

def _chuan_hoa_chuoi_nguyen_lieu(
    records: List[TieuHaoNguyenLieuNgay],
) -> Tuple[List[date], List[float], int]:
    """
    Sắp xếp chuỗi thời gian liên tục theo ngày và xử lý mọi ngày khuyết thiếu (nếu có)
    bằng trung vị cùng thứ trong tuần của dữ liệu lịch sử.
    """
    if not records:
        return [], [], 0

    records_sorted = sorted(records, key=lambda r: r.ngay)
    date_map: Dict[date, float] = {}
    missing_count = 0
    for r in records_sorted:
        if r.so_luong_tieu_hao is None or r.so_luong_tieu_hao < 0:
            missing_count += 1
            continue
        date_map[r.ngay] = float(r.so_luong_tieu_hao)

    if not date_map:
        return [], [], missing_count

    start_d = min(date_map.keys())
    end_d = max(date_map.keys())
    total_days = (end_d - start_d).days + 1

    # Tính trung vị theo thứ trong tuần để điền khuyết (nếu có ngày bị thiếu)
    by_dow: Dict[int, List[float]] = defaultdict(list)
    for d, v in date_map.items():
        by_dow[d.weekday()].append(v)
    global_med = statistics.median(date_map.values())
    dow_med = {
        k: (statistics.median(v) if v else global_med)
        for k, v in by_dow.items()
    }

    dates: List[date] = []
    values: List[float] = []
    for offset in range(total_days):
        cur_d = start_d + timedelta(days=offset)
        dates.append(cur_d)
        if cur_d in date_map:
            values.append(date_map[cur_d])
        else:
            missing_count += 1
            values.append(round(dow_med.get(cur_d.weekday(), global_med), 3))

    return dates, values, missing_count


def _chan_doan_chuoi_thoi_gian(
    dates: List[date],
    values: List[float],
    missing_count: int,
) -> ChanDoanChuoiThoiGianOut:
    """Phân tích thống kê mô tả, tính dừng, tự tương quan và tính mùa vụ của chuỗi tiêu hao."""
    n = len(values)
    mean_v = statistics.mean(values)
    std_v = statistics.stdev(values) if n > 1 else 0.0
    acf1 = _tinh_tu_tuong_quan(values, 1)
    acf7 = _tinh_tu_tuong_quan(values, 7)

    wd_vals = [v for d, v in zip(dates, values) if d.weekday() < 5]
    we_vals = [v for d, v in zip(dates, values) if d.weekday() >= 5]
    wd_mean = statistics.mean(wd_vals) if wd_vals else mean_v
    we_mean = statistics.mean(we_vals) if we_vals else mean_v
    lift_pct = ((we_mean - wd_mean) / wd_mean * 100.0) if wd_mean > 0 else 0.0

    half = n // 2
    mean_h1 = statistics.mean(values[:half]) if half > 0 else mean_v
    mean_h2 = statistics.mean(values[half:]) if half > 0 else mean_v
    drift_pct = abs(mean_h2 - mean_h1) / max(mean_h1, 1e-6) * 100.0

    if drift_pct <= 8.0:
        danh_gia_dung = "Ổn định tương đối (Chênh lệch trung bình 2 nửa chuỗi ≤ 8%)"
    elif drift_pct <= 18.0:
        danh_gia_dung = "Biến động nhẹ theo mùa vụ năm (Cần mô hình hóa chu kỳ năm & xu hướng)"
    else:
        danh_gia_dung = "Không dừng rõ rệt (Có dịch chuyển mức tiêu thụ mạnh giữa các giai đoạn)"

    if acf7 >= 0.45 and lift_pct >= 20.0:
        danh_gia_mua_vu = f"Mùa vụ tuần RẤT MẠNH (ACF lag-7 = {acf7:.2f}, cuối tuần tăng +{lift_pct:.1f}%)"
    elif acf7 >= 0.25:
        danh_gia_mua_vu = f"Có mùa vụ tuần rõ ràng (ACF lag-7 = {acf7:.2f}, cuối tuần tăng +{lift_pct:.1f}%)"
    else:
        danh_gia_mua_vu = f"Mùa vụ tuần nhẹ (ACF lag-7 = {acf7:.2f})"

    return ChanDoanChuoiThoiGianOut(
        so_ngay_quan_sat=n,
        so_gia_tri_khuyet_thieu=missing_count,
        trung_binh_ngay=round(mean_v, 3),
        do_lech_chuan=round(std_v, 3),
        gia_tri_nho_nhat=round(min(values), 3),
        gia_tri_lon_nhat=round(max(values), 3),
        tu_tuong_quan_lag_1=acf1,
        tu_tuong_quan_lag_7=acf7,
        trung_binh_ngay_thuong=round(wd_mean, 3),
        trung_binh_cuoi_tuan=round(we_mean, 3),
        ty_le_tang_cuoi_tuan_pct=round(lift_pct, 2),
        chenh_lech_trung_binh_hai_nua_pct=round(drift_pct, 2),
        danh_gia_tinh_dung=danh_gia_dung,
        danh_gia_mua_vu=danh_gia_mua_vu,
    )


# ==============================================================================
# 3. CÁC MÔ HÌNH DỰ BÁO CHUỖI THỜI GIAN (2 BASELINE + 3 ML)
# ==============================================================================

def _du_bao_baseline_ma7(history_values: List[float], horizon: int = 7) -> List[float]:
    """Baseline 1: Trung bình trượt 7 ngày gần nhất (Moving Average 7D)."""
    window = history_values[-7:] if len(history_values) >= 7 else history_values
    avg = sum(window) / len(window) if window else 0.0
    return [max(0.0, avg) for _ in range(horizon)]


def _du_bao_seasonal_naive_7d(history_values: List[float], horizon: int = 7) -> List[float]:
    """Baseline 2: Seasonal Naive — lấy đúng giá trị tiêu hao cùng thứ tuần trước."""
    n = len(history_values)
    preds: List[float] = []
    for h in range(1, horizon + 1):
        idx = n - 7 + ((h - 1) % 7)
        val = history_values[idx] if 0 <= idx < n else history_values[-1]
        preds.append(max(0.0, val))
    return preds


def _du_bao_holt_winters_seasonal(
    history_values: List[float],
    horizon: int = 7,
    alpha: float = 0.25,
    beta: float = 0.05,
    gamma: float = 0.25,
    phi: float = 0.90,
    season_len: int = 7,
) -> List[float]:
    """
    Model 1 (ML/Time-Series): Holt-Winters Triple Exponential Smoothing (Multiplicative Seasonality, m=7)
    có hệ số giảm chấn xu hướng (Damped Trend phi) để tránh ngoại suy quá đà.
    """
    n = len(history_values)
    if n < season_len * 2:
        return _du_bao_seasonal_naive_7d(history_values, horizon)

    # Khởi tạo Level, Trend và Hệ số Mùa vụ từ 4 tuần đầu tiên (chỉ dùng dữ liệu đầu chuỗi)
    n_init_seasons = min(4, n // season_len)
    init_block = history_values[: n_init_seasons * season_len]
    season_avgs = [
        max(sum(init_block[s * season_len : (s + 1) * season_len]) / season_len, 1e-6)
        for s in range(n_init_seasons)
    ]
    level = season_avgs[0]
    if n_init_seasons >= 2:
        trend = (season_avgs[-1] - season_avgs[0]) / ((n_init_seasons - 1) * season_len)
    else:
        trend = 0.0

    seasonals = [1.0] * season_len
    for j in range(season_len):
        ratios = [
            init_block[s * season_len + j] / season_avgs[s]
            for s in range(n_init_seasons)
        ]
        seasonals[j] = max(sum(ratios) / len(ratios), 0.1)
    # Chuẩn hóa để tổng hệ số mùa vụ 7 ngày = 7.0
    s_mean = sum(seasonals) / season_len
    seasonals = [s / s_mean for s in seasonals]

    # Cập nhật đệ quy qua toàn bộ lịch sử
    for t in range(n):
        y_t = max(history_values[t], 1e-6)
        s_idx = t % season_len
        s_prev = max(seasonals[s_idx], 0.1)
        level_prev = level
        trend_prev = trend

        level = alpha * (y_t / s_prev) + (1.0 - alpha) * (level_prev + phi * trend_prev)
        level = max(level, 1e-6)
        trend = beta * (level - level_prev) + (1.0 - beta) * phi * trend_prev
        seasonals[s_idx] = max(gamma * (y_t / level) + (1.0 - gamma) * s_prev, 0.1)

    # Dự báo đa bước h = 1..horizon
    preds: List[float] = []
    phi_sum = 0.0
    for h in range(1, horizon + 1):
        phi_sum += phi ** h
        s_idx = (n + h - 1) % season_len
        yhat = (level + phi_sum * trend) * seasonals[s_idx]
        preds.append(max(0.0, yhat))
    return preds


def _tao_vector_dac_trung_ridge(
    idx: int,
    d: date,
    lag7_val: float,
    lag14_val: float,
    roll7_val: float,
    origin_scale_n: int,
) -> List[float]:
    """
    Tạo vector đặc trưng chuẩn Prophet-style + Autoregressive (14 đặc trưng chưa tính hệ số chặn):
    - Xu hướng thời gian chuẩn hóa (t / N)
    - 6 biến giả thứ trong tuần (T3..CN, lấy T2 làm chuẩn) -> bắt chính xác hình dạng mùa vụ tuần
    - 4 thành phần Fourier chu kỳ năm (k=1, 2 với P=365.25) -> bắt sóng mùa vụ theo tháng/mùa
    - 3 đặc trưng trễ nhân quả (lag_7, lag_14, rolling_mean_7) -> nắm bắt động lượng gần nhất
    """
    t_norm = idx / max(origin_scale_n, 1)
    dow = d.weekday()
    dow_ohe = [1.0 if dow == k else 0.0 for k in range(1, 7)]

    doy = d.timetuple().tm_yday
    ang1 = 2.0 * math.pi * doy / 365.25
    ang2 = 4.0 * math.pi * doy / 365.25
    fourier_year = [
        math.sin(ang1),
        math.cos(ang1),
        math.sin(ang2),
        math.cos(ang2),
    ]

    return [t_norm] + dow_ohe + fourier_year + [lag7_val, lag14_val, roll7_val]


def _huan_luyen_va_du_bao_fourier_ridge(
    history_dates: List[date],
    history_values: List[float],
    horizon: int = 7,
    l2_lambda: float = 5.0,
) -> List[float]:
    """
    Model 2 (ML): Hồi quy Ridge (L2 Regularized Linear Regression) với đặc trưng
    Fourier mùa vụ năm + One-Hot thứ trong tuần + Biến trễ nhân quả (Lag-7, Lag-14, Rolling-7).

    Tuân thủ nghiêm ngặt Strict Featurization Ordering:
    - Bộ chuẩn hóa (mean, std) được fit DUY NHẤT trên tập lịch sử `history_values`.
    - Khi dự báo đa bước h=1..7, chỉ dùng dữ liệu <= t_0 và cập nhật đệ quy `rolling_mean_7`.
    """
    n = len(history_values)
    if n < 28:
        return _du_bao_seasonal_naive_7d(history_values, horizon)

    # 1. Xây dựng ma trận huấn luyện từ t = 14 .. n-1 (đảm bảo có đủ lag_14)
    X_raw: List[List[float]] = []
    y_train: List[float] = []
    for t in range(14, n):
        lag7 = history_values[t - 7]
        lag14 = history_values[t - 14]
        roll7 = sum(history_values[t - 7 : t]) / 7.0
        X_raw.append(_tao_vector_dac_trung_ridge(t, history_dates[t], lag7, lag14, roll7, 365))
        y_train.append(history_values[t])

    m = len(X_raw)
    p = len(X_raw[0])

    # 2. Fit StandardScaler chặt chẽ trên tập huấn luyện
    means = [sum(X_raw[i][j] for i in range(m)) / m for j in range(p)]
    stds: List[float] = []
    for j in range(p):
        var = sum((X_raw[i][j] - means[j]) ** 2 for i in range(m)) / m
        s = math.sqrt(var)
        stds.append(s if s > 1e-8 else 1.0)

    # Thêm cột hệ số chặn (intercept = 1.0 ở vị trí 0)
    d_dim = p + 1
    XtX = [[0.0] * d_dim for _ in range(d_dim)]
    Xty = [0.0] * d_dim

    for i in range(m):
        row = [1.0] + [(X_raw[i][j] - means[j]) / stds[j] for j in range(p)]
        yi = y_train[i]
        for a in range(d_dim):
            ra = row[a]
            Xty[a] += ra * yi
            for b in range(a, d_dim):
                XtX[a][b] += ra * row[b]

    for a in range(d_dim):
        for b in range(a):
            XtX[a][b] = XtX[b][a]
        # Không phạt L2 lên hệ số chặn (a == 0)
        if a > 0:
            XtX[a][a] += l2_lambda

    weights = _giai_he_phuong_trinh_tuyen_tinh(XtX, Xty)

    # 3. Dự báo đa bước h = 1..horizon theo cơ chế nhân quả (rolling recursive cho roll7)
    ext_values = history_values[:]
    last_date = history_dates[-1]
    preds: List[float] = []

    for h in range(1, horizon + 1):
        t_cur = n + h - 1
        d_cur = last_date + timedelta(days=h)
        lag7 = ext_values[t_cur - 7]
        lag14 = ext_values[t_cur - 14]
        roll7 = sum(ext_values[t_cur - 7 : t_cur]) / 7.0
        feat_raw = _tao_vector_dac_trung_ridge(t_cur, d_cur, lag7, lag14, roll7, 365)
        feat_std = [1.0] + [(feat_raw[j] - means[j]) / stds[j] for j in range(p)]
        yhat = sum(w * x for w, x in zip(weights, feat_std))
        yhat = max(0.0, yhat)
        preds.append(yhat)
        ext_values.append(yhat)

    return preds


# ==============================================================================
# 4. ĐÁNH GIÁ ROLLING-ORIGIN 7 NGÀY & TINH CHỈNH SIÊU THAM SỐ (ZERO LEAKAGE)
# ==============================================================================

def _chay_danh_gia_rolling_7_ngay(
    dates: List[date],
    values: List[float],
    start_idx: int,
    end_idx: int,
    du_bao_fn,
) -> Tuple[List[date], List[float], List[float], List[int]]:
    """
    Đánh giá Rolling-Origin chân trời 7 ngày trên đoạn [start_idx, end_idx).
    Tại mỗi bước nhảy 7 ngày (origin = t0), mô hình CHỈ nhìn thấy dữ liệu [:origin]
    và phải dự báo đồng thời 7 ngày [origin .. origin+6].
    """
    eval_dates: List[date] = []
    actuals: List[float] = []
    preds: List[float] = []
    dows: List[int] = []

    origin = start_idx
    while origin < end_idx:
        step_h = min(7, end_idx - origin)
        hist_d = dates[:origin]
        hist_v = values[:origin]
        step_preds = du_bao_fn(hist_d, hist_v, step_h)
        for k in range(step_h):
            idx = origin + k
            eval_dates.append(dates[idx])
            actuals.append(values[idx])
            preds.append(step_preds[k])
            dows.append(dates[idx].weekday())
        origin += 7

    return eval_dates, actuals, preds, dows


def _huan_luyen_va_danh_gia_mot_nguyen_lieu(
    ing: Ingredient,
    dates: List[date],
    values: List[float],
    missing_count: int,
    horizon: int = 7,
    start_forecast_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Chạy đầy đủ quy trình Train / Validation / Test cho 1 nguyên liệu:
    - Chẩn đoán chuỗi
    - Tinh chỉnh siêu tham số Holt-Winters, Fourier Ridge, Ensemble trên Validation
    - Đánh giá cả 5 mô hình trên Validation và Holdout Test
    - Chọn mô hình tốt nhất theo Validation MAPE
    - Huấn luyện lại trên 100% dữ liệu 365 ngày để sinh dự báo 7 ngày tới
    """
    n = len(values)
    n_test = min(45, max(14, int(n * 0.125)))
    n_val = min(45, max(14, int(n * 0.125)))
    n_train = n - n_val - n_test

    val_start, val_end = n_train, n_train + n_val
    test_start, test_end = n_train + n_val, n

    chan_doan = _chan_doan_chuoi_thoi_gian(dates, values, missing_count)

    # --- 1. Baseline_MA7 ---
    _, val_y, val_ma7, val_dows = _chay_danh_gia_rolling_7_ngay(
        dates, values, val_start, val_end,
        lambda hd, hv, h: _du_bao_baseline_ma7(hv, h),
    )
    test_dates, test_y, test_ma7, test_dows = _chay_danh_gia_rolling_7_ngay(
        dates, values, test_start, test_end,
        lambda hd, hv, h: _du_bao_baseline_ma7(hv, h),
    )

    # --- 2. Seasonal_Naive_7D ---
    _, _, val_snaive, _ = _chay_danh_gia_rolling_7_ngay(
        dates, values, val_start, val_end,
        lambda hd, hv, h: _du_bao_seasonal_naive_7d(hv, h),
    )
    _, _, test_snaive, _ = _chay_danh_gia_rolling_7_ngay(
        dates, values, test_start, test_end,
        lambda hd, hv, h: _du_bao_seasonal_naive_7d(hv, h),
    )

    # --- 3. HoltWinters_Seasonal (Grid Search trên Validation) ---
    hw_grid = [
        (0.15, 0.02, 0.15, 0.85),
        (0.20, 0.03, 0.25, 0.90),
        (0.30, 0.05, 0.20, 0.90),
        (0.35, 0.02, 0.30, 0.85),
        (0.15, 0.05, 0.35, 0.90),
    ]
    best_hw_params = hw_grid[0]
    best_hw_val_mape = float("inf")
    val_hw_best: List[float] = []

    for alpha, beta, gamma, phi in hw_grid:
        _, _, preds_v, _ = _chay_danh_gia_rolling_7_ngay(
            dates, values, val_start, val_end,
            lambda hd, hv, h, a=alpha, b=beta, g=gamma, p=phi: _du_bao_holt_winters_seasonal(
                hv, h, alpha=a, beta=b, gamma=g, phi=p
            ),
        )
        m_v = _tinh_chi_so_sai_so(val_y, preds_v, val_dows)
        if m_v["mape"] < best_hw_val_mape:
            best_hw_val_mape = m_v["mape"]
            best_hw_params = (alpha, beta, gamma, phi)
            val_hw_best = preds_v

    a_opt, b_opt, g_opt, p_opt = best_hw_params
    _, _, test_hw, _ = _chay_danh_gia_rolling_7_ngay(
        dates, values, test_start, test_end,
        lambda hd, hv, h: _du_bao_holt_winters_seasonal(
            hv, h, alpha=a_opt, beta=b_opt, gamma=g_opt, phi=p_opt
        ),
    )

    # --- 4. Fourier_Ridge_ML (Tinh chỉnh hệ số L2 lambda trên Validation) ---
    ridge_grid = [0.5, 2.0, 5.0, 15.0, 40.0]
    best_lambda = 5.0
    best_ridge_val_mape = float("inf")
    val_ridge_best: List[float] = []

    for lam in ridge_grid:
        _, _, preds_v, _ = _chay_danh_gia_rolling_7_ngay(
            dates, values, val_start, val_end,
            lambda hd, hv, h, l2=lam: _huan_luyen_va_du_bao_fourier_ridge(hd, hv, h, l2_lambda=l2),
        )
        m_v = _tinh_chi_so_sai_so(val_y, preds_v, val_dows)
        if m_v["mape"] < best_ridge_val_mape:
            best_ridge_val_mape = m_v["mape"]
            best_lambda = lam
            val_ridge_best = preds_v

    _, _, test_ridge, _ = _chay_danh_gia_rolling_7_ngay(
        dates, values, test_start, test_end,
        lambda hd, hv, h: _huan_luyen_va_du_bao_fourier_ridge(hd, hv, h, l2_lambda=best_lambda),
    )

    # --- 5. Ensemble_HW_Ridge (Tối ưu trọng số w trên Validation) ---
    weight_grid = [0.20, 0.35, 0.50, 0.65, 0.80]
    best_w = 0.50
    best_ens_val_mape = float("inf")
    val_ens_best: List[float] = []

    for w in weight_grid:
        preds_v = [w * a + (1.0 - w) * b for a, b in zip(val_hw_best, val_ridge_best)]
        m_v = _tinh_chi_so_sai_so(val_y, preds_v, val_dows)
        if m_v["mape"] < best_ens_val_mape:
            best_ens_val_mape = m_v["mape"]
            best_w = w
            val_ens_best = preds_v

    test_ens = [best_w * a + (1.0 - best_w) * b for a, b in zip(test_hw, test_ridge)]

    # Tổng hợp kết quả đánh giá của cả 5 mô hình
    model_preds = {
        "Baseline_MA7": (
            "BASELINE",
            val_ma7,
            test_ma7,
            {"window": 7},
        ),
        "Seasonal_Naive_7D": (
            "BASELINE",
            val_snaive,
            test_snaive,
            {"season_lag": 7},
        ),
        "HoltWinters_Seasonal": (
            "ML",
            val_hw_best,
            test_hw,
            {"alpha": a_opt, "beta": b_opt, "gamma": g_opt, "phi": p_opt, "season_len": 7},
        ),
        "Fourier_Ridge_ML": (
            "ML",
            val_ridge_best,
            test_ridge,
            {"l2_lambda": best_lambda, "fourier_orders": 2, "lags": [7, 14, "roll_7"]},
        ),
        "Ensemble_HW_Ridge": (
            "ML",
            val_ens_best,
            test_ens,
            {
                "weight_hw": best_w,
                "weight_ridge": round(1.0 - best_w, 2),
                "hw": {"alpha": a_opt, "beta": b_opt, "gamma": g_opt, "phi": p_opt},
                "ridge_lambda": best_lambda,
            },
        ),
    }

    baseline_test_metrics = _tinh_chi_so_sai_so(test_y, test_ma7, test_dows)
    baseline_test_mape = max(baseline_test_metrics["mape"], 1e-6)

    evaluations: Dict[str, Dict[str, Any]] = {}
    for model_name, (group, vp, tp, params) in model_preds.items():
        val_m = _tinh_chi_so_sai_so(val_y, vp, val_dows)
        test_m = _tinh_chi_so_sai_so(test_y, tp, test_dows)
        improv = round(((baseline_test_mape - test_m["mape"]) / baseline_test_mape) * 100.0, 2)
        evaluations[model_name] = {
            "ten_mo_hinh": model_name,
            "nhom_mo_hinh": group,
            "val": val_m,
            "test": test_m,
            "test_preds": tp,
            "cai_thien_pct": improv,
            "params": params,
        }

    # Chọn mô hình ML tốt nhất CHỈ dựa trên tập Validation (tránh gian lận nhìn tập Test)
    ml_candidates = [m for m, info in evaluations.items() if info["nhom_mo_hinh"] == "ML"]
    best_model_name = min(
        ml_candidates,
        key=lambda m: (evaluations[m]["val"]["mape"], evaluations[m]["val"]["mae"]),
    )

    # Retrain mô hình tốt nhất trên 100% dữ liệu 365 ngày để sinh dự báo 7 ngày tới
    full_hw = _du_bao_holt_winters_seasonal(
        values, horizon=horizon, alpha=a_opt, beta=b_opt, gamma=g_opt, phi=p_opt
    )
    full_ridge = _huan_luyen_va_du_bao_fourier_ridge(
        dates, values, horizon=horizon, l2_lambda=best_lambda
    )
    if best_model_name == "HoltWinters_Seasonal":
        future_preds = full_hw
    elif best_model_name == "Fourier_Ridge_ML":
        future_preds = full_ridge
    else:
        future_preds = [best_w * a + (1.0 - best_w) * b for a, b in zip(full_hw, full_ridge)]

    # Khởi tạo mốc ngày dự báo T+1 .. T+7 (luôn bắt đầu từ ngày mai để Dashboard/ROP dùng trực tiếp)
    base_start = start_forecast_date or (date.today() + timedelta(days=1))
    # Căn chỉnh đúng thứ trong tuần nếu ngày cuối lịch sử khác hôm nay
    last_hist_date = dates[-1]
    if base_start != last_hist_date + timedelta(days=1):
        # Đảm bảo mỗi ngày dự báo khớp đúng thứ trong tuần với hệ số mùa vụ đã học
        pred_by_dow: Dict[int, float] = {}
        for h_idx, val in enumerate(future_preds):
            d_sim = last_hist_date + timedelta(days=h_idx + 1)
            pred_by_dow[d_sim.weekday()] = val
        aligned_preds = [
            pred_by_dow.get((base_start + timedelta(days=h_idx)).weekday(), future_preds[h_idx])
            for h_idx in range(horizon)
        ]
        future_preds = aligned_preds

    best_test_info = evaluations[best_model_name]["test"]
    res_std = best_test_info["residual_std"]
    test_mape = best_test_info["mape"]

    # Làm tròn phù hợp với đơn vị tính ('cái' làm tròn số nguyên, còn lại 2 chữ số thập phân)
    la_don_vi_nguyen = (ing.don_vi_tinh or "").strip().lower() in ("cái", "ly", "chiếc")
    precision = 0 if la_don_vi_nguyen else 2

    du_bao_7_ngay: List[DiemDuBaoChiTietOut] = []
    for h in range(horizon):
        target_d = base_start + timedelta(days=h)
        raw_pred = max(0.0, future_preds[h])
        # Độ rộng khoảng tin cậy 95% mở rộng nhẹ theo chân trời h
        margin_95 = 1.96 * res_std * math.sqrt(1.0 + 0.05 * h)
        pred_val = round(raw_pred, precision)
        low_95 = round(max(0.0, raw_pred - margin_95), precision)
        high_95 = round(raw_pred + margin_95, precision)
        # Độ tin cậy thống kê dựa trên (1 - MAPE) suy giảm nhẹ theo bước h
        conf = round(min(0.98, max(0.70, 1.0 - (test_mape / 100.0) - 0.004 * h)), 3)

        du_bao_7_ngay.append(
            DiemDuBaoChiTietOut(
                ngay_du_bao=target_d,
                thu_trong_tuan=target_d.weekday(),
                nhan_thu=NHAN_THU_VN[target_d.weekday()],
                la_cuoi_tuan=target_d.weekday() >= 5,
                so_luong_du_bao=float(pred_val),
                can_duoi_95=float(low_95),
                can_tren_95=float(high_95),
                do_tin_cay=conf,
                phuong_phap=best_model_name,
            )
        )

    # Chuỗi kiểm thử Actual vs Predicted trên tập Holdout Test (cho biểu đồ đánh giá)
    best_test_preds = evaluations[best_model_name]["test_preds"]
    kiem_thu_series: List[DiemKiemThuThucTeVsDuBaoOut] = []
    for td, ty, t_ml, t_base in zip(test_dates, test_y, best_test_preds, test_ma7):
        ae = abs(ty - t_ml)
        ape = (ae / max(ty, 1e-6)) * 100.0
        kiem_thu_series.append(
            DiemKiemThuThucTeVsDuBaoOut(
                ngay=td,
                thu_trong_tuan=td.weekday(),
                la_cuoi_tuan=td.weekday() >= 5,
                thuc_te=round(ty, 3),
                du_bao_ml=round(t_ml, 3),
                du_bao_baseline=round(t_base, 3),
                sai_so_tuyet_doi=round(ae, 3),
                sai_so_phan_tram=round(ape, 2),
            )
        )

    return {
        "ingredient": ing,
        "split": {"n_total": n, "n_train": n_train, "n_val": n_val, "n_test": n_test},
        "chan_doan": chan_doan,
        "evaluations": evaluations,
        "best_model_name": best_model_name,
        "best_params": evaluations[best_model_name]["params"],
        "du_bao_7_ngay": du_bao_7_ngay,
        "kiem_thu_series": kiem_thu_series,
    }


# ==============================================================================
# 5. QUY TRÌNH HUẤN LUYỆN TOÀN HỆ THỐNG, LƯU CSDL & XUẤT HIỆN VẬT BÁO CÁO
# ==============================================================================

def _xuat_tep_ket_qua_tuan_6(
    lan_chay: LanChayMoHinh,
    bang_xep_hang: List[TongHopMoHinhToanCucOut],
    danh_sach_du_bao: List[DuBao7NgayNguyenLieuOut],
    tat_ca_danh_gia: List[KetQuaSoSanhMoHinhOut],
) -> Tuple[str, str, str]:
    """Xuất 3 tệp dữ liệu kết quả Tuần 6 (CSV dự báo, CSV so sánh mô hình, JSON tổng hợp)."""
    _dam_bao_thu_muc_du_bao()

    # 1. File CSV Dự báo 7 ngày (105 dòng = 15 nguyên liệu x 7 ngày)
    with open(FILE_DU_BAO_7_NGAY, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ma_nguyen_lieu",
            "ten_nguyen_lieu",
            "don_vi_tinh",
            "ngay_du_bao",
            "nhan_thu",
            "la_cuoi_tuan",
            "so_luong_du_bao",
            "can_duoi_95",
            "can_tren_95",
            "do_tin_cay",
            "phuong_phap",
        ])
        for item in danh_sach_du_bao:
            for d in item.du_bao_chi_tiet:
                writer.writerow([
                    item.ma_nguyen_lieu,
                    item.ten_nguyen_lieu,
                    item.don_vi_tinh,
                    d.ngay_du_bao.isoformat(),
                    d.nhan_thu,
                    int(d.la_cuoi_tuan),
                    d.so_luong_du_bao,
                    d.can_duoi_95,
                    d.can_tren_95,
                    d.do_tin_cay,
                    d.phuong_phap,
                ])

    # 2. File CSV Bảng so sánh 5 mô hình trên 15 nguyên liệu (75 dòng)
    with open(FILE_SO_SANH_MO_HINH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ma_nguyen_lieu",
            "ten_nguyen_lieu",
            "don_vi_tinh",
            "ten_mo_hinh",
            "nhom_mo_hinh",
            "val_mae",
            "val_rmse",
            "val_mape",
            "test_mae",
            "test_rmse",
            "test_mape",
            "test_smape",
            "test_r2",
            "mape_ngay_thuong",
            "mape_cuoi_tuan",
            "cai_thien_so_voi_baseline_pct",
            "la_mo_hinh_tot_nhat",
        ])
        for ev in tat_ca_danh_gia:
            writer.writerow([
                ev.ma_nguyen_lieu,
                ev.ten_nguyen_lieu,
                ev.don_vi_tinh,
                ev.ten_mo_hinh,
                ev.nhom_mo_hinh,
                ev.val_mae,
                ev.val_rmse,
                ev.val_mape,
                ev.test_mae,
                ev.test_rmse,
                ev.test_mape,
                ev.test_smape,
                ev.test_r2,
                ev.mape_ngay_thuong,
                ev.mape_cuoi_tuan,
                ev.cai_thien_so_voi_baseline_pct,
                int(ev.la_mo_hinh_tot_nhat),
            ])

    # 3. File JSON Báo cáo Tổng hợp
    payload = {
        "lan_huan_luyen": LanChayMoHinhOut.model_validate(lan_chay).model_dump(mode="json"),
        "bang_xep_hang_mo_hinh": [x.model_dump(mode="json") for x in bang_xep_hang],
        "danh_sach_du_bao_7_ngay": [x.model_dump(mode="json") for x in danh_sach_du_bao],
    }
    with open(FILE_BAO_CAO_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return FILE_DU_BAO_7_NGAY, FILE_SO_SANH_MO_HINH, FILE_BAO_CAO_JSON


def _tong_hop_bang_xep_hang_mo_hinh(
    eval_rows: List[KetQuaDanhGiaMoHinh],
) -> List[TongHopMoHinhToanCucOut]:
    """Tổng hợp chỉ số trung bình toàn cục và khoảng tin cậy Bootstrap 95% cho 5 mô hình."""
    by_model: Dict[str, List[KetQuaDanhGiaMoHinh]] = defaultdict(list)
    for r in eval_rows:
        by_model[r.ten_mo_hinh].append(r)

    base_rows = by_model.get("Baseline_MA7", [])
    base_mape_tb = statistics.mean([r.test_mape for r in base_rows]) if base_rows else 1.0

    results: List[TongHopMoHinhToanCucOut] = []
    for model_name, group in THU_TU_MO_HINH:
        rows = by_model.get(model_name, [])
        if not rows:
            continue
        test_mapes = [r.test_mape for r in rows]
        test_mape_tb = statistics.mean(test_mapes)
        improv = round(((base_mape_tb - test_mape_tb) / max(base_mape_tb, 1e-6)) * 100.0, 2)
        results.append(
            TongHopMoHinhToanCucOut(
                ten_mo_hinh=model_name,
                nhom_mo_hinh=group,
                so_nguyen_lieu_thang=sum(1 for r in rows if r.la_mo_hinh_tot_nhat),
                val_mape_tb=round(statistics.mean([r.val_mape for r in rows]), 2),
                test_mape_tb=round(test_mape_tb, 2),
                test_smape_tb=round(statistics.mean([r.test_smape for r in rows]), 2),
                test_mae_tb=round(statistics.mean([r.test_mae for r in rows]), 4),
                test_rmse_tb=round(statistics.mean([r.test_rmse for r in rows]), 4),
                test_r2_tb=round(statistics.mean([r.test_r2 for r in rows]), 4),
                mape_ngay_thuong_tb=round(statistics.mean([r.mape_ngay_thuong for r in rows]), 2),
                mape_cuoi_tuan_tb=round(statistics.mean([r.mape_cuoi_tuan for r in rows]), 2),
                cai_thien_mape_so_voi_baseline_pct=improv,
                khoang_tin_cay_bootstrap_95_mape=_tinh_bootstrap_ci_95(test_mapes),
            )
        )

    results.sort(key=lambda x: x.test_mape_tb)
    return results


def chay_huan_luyen_va_du_bao_ai(
    db: Session,
    chan_troi_du_bao: int = 7,
) -> BaoCaoTongQuanDuBaoAIOut:
    """
    Thực thi trọn gói Quy trình Tuần 6:
    1. Đảm bảo dữ liệu chuỗi thời gian Tuần 5 đã sẵn sàng.
    2. Huấn luyện, tinh chỉnh và so sánh 5 mô hình cho toàn bộ 15 nguyên liệu.
    3. Lưu nhật ký `lan_chay_mo_hinh`, chi tiết `ket_qua_danh_gia_mo_hinh`.
    4. Cập nhật 105 dòng dự báo 7 ngày tới trong `du_bao_nhu_cau` (thay thế hoàn toàn dữ liệu seed cũ).
    5. Xuất báo cáo CSV và JSON ra `backend/du_lieu/du_bao_ai/`.
    """
    t0 = time.perf_counter()

    # 1. Đảm bảo dữ liệu chuỗi thời gian Tuần 5 đã tồn tại
    count_ts = db.query(TieuHaoNguyenLieuNgay).count()
    if count_ts == 0:
        chay_quy_trinh_boc_tach_bom(db, so_ngay=365)

    ingredients = (
        db.query(Ingredient)
        .filter(Ingredient.trang_thai == True)
        .order_by(Ingredient.ma_nguyen_lieu.asc())
        .all()
    )
    if not ingredients:
        raise ValueError("Chưa có dữ liệu nguyên liệu trong cơ sở dữ liệu.")

    ts_all = (
        db.query(TieuHaoNguyenLieuNgay)
        .order_by(TieuHaoNguyenLieuNgay.ma_nguyen_lieu.asc(), TieuHaoNguyenLieuNgay.ngay.asc())
        .all()
    )
    ts_by_ing: Dict[int, List[TieuHaoNguyenLieuNgay]] = defaultdict(list)
    for row in ts_all:
        ts_by_ing[row.ma_nguyen_lieu].append(row)

    start_forecast_date = date.today() + timedelta(days=1)

    # 2. Huấn luyện từng nguyên liệu
    ket_qua_tung_nl: List[Dict[str, Any]] = []
    for ing in ingredients:
        records = ts_by_ing.get(ing.ma_nguyen_lieu, [])
        dates, values, missing_cnt = _chuan_hoa_chuoi_nguyen_lieu(records)
        if len(values) < 42:
            continue
        res = _huan_luyen_va_danh_gia_mot_nguyen_lieu(
            ing=ing,
            dates=dates,
            values=values,
            missing_count=missing_cnt,
            horizon=chan_troi_du_bao,
            start_forecast_date=start_forecast_date,
        )
        ket_qua_tung_nl.append(res)

    if not ket_qua_tung_nl:
        raise ValueError("Không đủ dữ liệu chuỗi thời gian để huấn luyện mô hình dự báo.")

    # 3. Tính các chỉ số tổng hợp toàn cục
    baseline_mapes = [r["evaluations"]["Baseline_MA7"]["test"]["mape"] for r in ket_qua_tung_nl]
    baseline_maes = [r["evaluations"]["Baseline_MA7"]["test"]["mae"] for r in ket_qua_tung_nl]
    baseline_rmses = [r["evaluations"]["Baseline_MA7"]["test"]["rmse"] for r in ket_qua_tung_nl]

    ml_mapes = [r["evaluations"][r["best_model_name"]]["test"]["mape"] for r in ket_qua_tung_nl]
    ml_maes = [r["evaluations"][r["best_model_name"]]["test"]["mae"] for r in ket_qua_tung_nl]
    ml_rmses = [r["evaluations"][r["best_model_name"]]["test"]["rmse"] for r in ket_qua_tung_nl]

    base_mape_tb = round(statistics.mean(baseline_mapes), 2)
    ml_mape_tb = round(statistics.mean(ml_mapes), 2)
    giam_sai_so_pct = round(((base_mape_tb - ml_mape_tb) / max(base_mape_tb, 1e-6)) * 100.0, 2)

    winner_counter = Counter(r["best_model_name"] for r in ket_qua_tung_nl)
    most_common_model = winner_counter.most_common(1)[0][0]
    sample_split = ket_qua_tung_nl[0]["split"]
    elapsed = round(time.perf_counter() - t0, 3)

    # 4. Lưu nhật ký lần chạy mô hình vào CSDL
    lan_chay = LanChayMoHinh(
        ten_phien_ban="DU_BAO_NHU_CAU_AI_TUAN6_V1",
        so_nguyen_lieu=len(ket_qua_tung_nl),
        so_ngay_lich_su=sample_split["n_total"],
        so_ngay_train=sample_split["n_train"],
        so_ngay_val=sample_split["n_val"],
        so_ngay_test=sample_split["n_test"],
        chan_troi_du_bao=chan_troi_du_bao,
        mo_hinh_tot_nhat_pho_bien=most_common_model,
        baseline_mape_tb=base_mape_tb,
        ml_mape_tb=ml_mape_tb,
        baseline_mae_tb=round(statistics.mean(baseline_maes), 4),
        ml_mae_tb=round(statistics.mean(ml_maes), 4),
        baseline_rmse_tb=round(statistics.mean(baseline_rmses), 4),
        ml_rmse_tb=round(statistics.mean(ml_rmses), 4),
        muc_giam_sai_so_mape_pct=giam_sai_so_pct,
        thoi_gian_xu_ly_giay=elapsed,
        trang_thai="THANH_CONG",
        ghi_chu=(
            f"Huấn luyện & kiểm thử Rolling 7 ngày trên {len(ket_qua_tung_nl)} nguyên liệu "
            f"(Train={sample_split['n_train']}d / Val={sample_split['n_val']}d / Test={sample_split['n_test']}d). "
            f"MAPE giảm từ {base_mape_tb}% (Baseline_MA7) xuống {ml_mape_tb}% (-{giam_sai_so_pct}%)."
        ),
    )
    db.add(lan_chay)
    db.flush()

    # 5. Lưu bảng chi tiết đánh giá mô hình (`ket_qua_danh_gia_mo_hinh`)
    orm_eval_rows: List[KetQuaDanhGiaMoHinh] = []
    out_eval_rows: List[KetQuaSoSanhMoHinhOut] = []

    for r in ket_qua_tung_nl:
        ing: Ingredient = r["ingredient"]
        best_m = r["best_model_name"]
        for model_name, _ in THU_TU_MO_HINH:
            ev = r["evaluations"][model_name]
            row_orm = KetQuaDanhGiaMoHinh(
                ma_lan_huan_luyen=lan_chay.ma_lan_huan_luyen,
                ma_nguyen_lieu=ing.ma_nguyen_lieu,
                ten_mo_hinh=model_name,
                nhom_mo_hinh=ev["nhom_mo_hinh"],
                val_mae=ev["val"]["mae"],
                val_rmse=ev["val"]["rmse"],
                val_mape=ev["val"]["mape"],
                test_mae=ev["test"]["mae"],
                test_rmse=ev["test"]["rmse"],
                test_mape=ev["test"]["mape"],
                test_smape=ev["test"]["smape"],
                test_r2=ev["test"]["r2"],
                mape_ngay_thuong=ev["test"]["mape_ngay_thuong"],
                mape_cuoi_tuan=ev["test"]["mape_cuoi_tuan"],
                do_lech_chuan_phan_du=ev["test"]["residual_std"],
                cai_thien_so_voi_baseline_pct=ev["cai_thien_pct"],
                la_mo_hinh_tot_nhat=(model_name == best_m),
                tham_so_toi_uu=json.dumps(ev["params"], ensure_ascii=False),
            )
            orm_eval_rows.append(row_orm)

    db.add_all(orm_eval_rows)
    db.flush()

    # 6. Cập nhật bảng `du_bao_nhu_cau` cho toàn bộ 15 nguyên liệu (T+1 .. T+7)
    db.query(DemandForecast).delete(synchronize_session=False)
    forecast_orms: List[DemandForecast] = []
    danh_sach_du_bao_out: List[DuBao7NgayNguyenLieuOut] = []

    for r in ket_qua_tung_nl:
        ing: Ingredient = r["ingredient"]
        best_m = r["best_model_name"]
        best_ev = r["evaluations"][best_m]
        points: List[DiemDuBaoChiTietOut] = r["du_bao_7_ngay"]

        for pt in points:
            forecast_orms.append(
                DemandForecast(
                    ma_nguyen_lieu=ing.ma_nguyen_lieu,
                    ngay_du_bao=pt.ngay_du_bao,
                    so_luong_du_bao=pt.so_luong_du_bao,
                    do_tin_cay=pt.do_tin_cay,
                    phuong_phap=pt.phuong_phap,
                )
            )

        tong_7d = round(sum(p.so_luong_du_bao for p in points), 2)
        tb_ngay = round(tong_7d / len(points), 2) if points else 0.0
        peak_pt = max(points, key=lambda p: p.so_luong_du_bao)
        ngay_cao_diem = f"{peak_pt.nhan_thu} ({peak_pt.ngay_du_bao.strftime('%d/%m')})"

        danh_sach_du_bao_out.append(
            DuBao7NgayNguyenLieuOut(
                ma_nguyen_lieu=ing.ma_nguyen_lieu,
                ten_nguyen_lieu=ing.ten_nguyen_lieu,
                danh_muc=ing.danh_muc,
                don_vi_tinh=ing.don_vi_tinh,
                ton_kho_hien_tai=ing.ton_kho_hien_tai,
                muc_ton_an_toan=ing.muc_ton_an_toan,
                mo_hinh_duoc_chon=best_m,
                test_mape=best_ev["test"]["mape"],
                test_mae=best_ev["test"]["mae"],
                cai_thien_so_voi_baseline_pct=best_ev["cai_thien_pct"],
                tong_du_bao_7_ngay=tong_7d,
                trung_binh_du_bao_ngay=tb_ngay,
                ngay_cao_diem=ngay_cao_diem,
                du_bao_chi_tiet=points,
            )
        )

    db.add_all(forecast_orms)
    db.commit()
    db.refresh(lan_chay)

    ing_map = {i.ma_nguyen_lieu: i for i in ingredients}
    for row_orm in orm_eval_rows:
        ing = ing_map[row_orm.ma_nguyen_lieu]
        out_eval_rows.append(
            KetQuaSoSanhMoHinhOut(
                ma_danh_gia=row_orm.ma_danh_gia,
                ma_nguyen_lieu=row_orm.ma_nguyen_lieu,
                ten_nguyen_lieu=ing.ten_nguyen_lieu,
                don_vi_tinh=ing.don_vi_tinh,
                ten_mo_hinh=row_orm.ten_mo_hinh,
                nhom_mo_hinh=row_orm.nhom_mo_hinh,
                val_mae=row_orm.val_mae,
                val_rmse=row_orm.val_rmse,
                val_mape=row_orm.val_mape,
                test_mae=row_orm.test_mae,
                test_rmse=row_orm.test_rmse,
                test_mape=row_orm.test_mape,
                test_smape=row_orm.test_smape,
                test_r2=row_orm.test_r2,
                mape_ngay_thuong=row_orm.mape_ngay_thuong,
                mape_cuoi_tuan=row_orm.mape_cuoi_tuan,
                do_lech_chuan_phan_du=row_orm.do_lech_chuan_phan_du,
                cai_thien_so_voi_baseline_pct=row_orm.cai_thien_so_voi_baseline_pct,
                la_mo_hinh_tot_nhat=row_orm.la_mo_hinh_tot_nhat,
                tham_so_toi_uu=row_orm.tham_so_toi_uu,
            )
        )

    bang_xep_hang = _tong_hop_bang_xep_hang_mo_hinh(orm_eval_rows)
    f_du_bao, f_so_sanh, f_json = _xuat_tep_ket_qua_tuan_6(
        lan_chay=lan_chay,
        bang_xep_hang=bang_xep_hang,
        danh_sach_du_bao=danh_sach_du_bao_out,
        tat_ca_danh_gia=out_eval_rows,
    )

    return BaoCaoTongQuanDuBaoAIOut(
        lan_huan_luyen=LanChayMoHinhOut.model_validate(lan_chay),
        bang_xep_hang_mo_hinh=bang_xep_hang,
        danh_sach_du_bao_7_ngay=danh_sach_du_bao_out,
        duong_dan_file_du_bao=f_du_bao,
        duong_dan_file_so_sanh=f_so_sanh,
        duong_dan_file_bao_cao_json=f_json,
    )


# ==============================================================================
# 6. CÁC HÀM TRUY VẤN PHỤC VỤ API ENDPOINTS TUẦN 6
# ==============================================================================

def _dam_bao_da_huan_luyen(db: Session) -> LanChayMoHinh:
    """Đảm bảo đã có ít nhất 1 lần chạy huấn luyện Tuần 6 trong CSDL."""
    latest = (
        db.query(LanChayMoHinh)
        .order_by(LanChayMoHinh.ma_lan_huan_luyen.desc())
        .first()
    )
    if not latest:
        chay_huan_luyen_va_du_bao_ai(db, chan_troi_du_bao=7)
        latest = (
            db.query(LanChayMoHinh)
            .order_by(LanChayMoHinh.ma_lan_huan_luyen.desc())
            .first()
        )
    return latest


def lay_tong_quan_du_bao_ai(db: Session) -> BaoCaoTongQuanDuBaoAIOut:
    """Lấy báo cáo tổng quan lần huấn luyện AI mới nhất (xếp hạng mô hình + dự báo 15 nguyên liệu)."""
    latest = _dam_bao_da_huan_luyen(db)
    eval_rows = (
        db.query(KetQuaDanhGiaMoHinh)
        .filter(KetQuaDanhGiaMoHinh.ma_lan_huan_luyen == latest.ma_lan_huan_luyen)
        .all()
    )
    bang_xep_hang = _tong_hop_bang_xep_hang_mo_hinh(eval_rows)
    danh_sach_du_bao = lay_du_bao_7_ngay_tat_ca(db)

    return BaoCaoTongQuanDuBaoAIOut(
        lan_huan_luyen=LanChayMoHinhOut.model_validate(latest),
        bang_xep_hang_mo_hinh=bang_xep_hang,
        danh_sach_du_bao_7_ngay=danh_sach_du_bao,
        duong_dan_file_du_bao=FILE_DU_BAO_7_NGAY if os.path.exists(FILE_DU_BAO_7_NGAY) else None,
        duong_dan_file_so_sanh=FILE_SO_SANH_MO_HINH if os.path.exists(FILE_SO_SANH_MO_HINH) else None,
        duong_dan_file_bao_cao_json=FILE_BAO_CAO_JSON if os.path.exists(FILE_BAO_CAO_JSON) else None,
    )


def lay_bang_so_sanh_mo_hinh(
    db: Session,
    ma_nguyen_lieu: Optional[int] = None,
    chi_lay_tot_nhat: bool = False,
) -> List[KetQuaSoSanhMoHinhOut]:
    """Lấy bảng so sánh chi tiết MAE / RMSE / MAPE / R2 giữa các mô hình."""
    latest = _dam_bao_da_huan_luyen(db)
    query = (
        db.query(KetQuaDanhGiaMoHinh)
        .filter(KetQuaDanhGiaMoHinh.ma_lan_huan_luyen == latest.ma_lan_huan_luyen)
    )
    if ma_nguyen_lieu is not None:
        query = query.filter(KetQuaDanhGiaMoHinh.ma_nguyen_lieu == ma_nguyen_lieu)
    if chi_lay_tot_nhat:
        query = query.filter(KetQuaDanhGiaMoHinh.la_mo_hinh_tot_nhat == True)

    rows = query.order_by(
        KetQuaDanhGiaMoHinh.ma_nguyen_lieu.asc(),
        KetQuaDanhGiaMoHinh.test_mape.asc(),
    ).all()

    ingredients = {i.ma_nguyen_lieu: i for i in db.query(Ingredient).all()}
    results: List[KetQuaSoSanhMoHinhOut] = []
    for r in rows:
        ing = ingredients.get(r.ma_nguyen_lieu)
        results.append(
            KetQuaSoSanhMoHinhOut(
                ma_danh_gia=r.ma_danh_gia,
                ma_nguyen_lieu=r.ma_nguyen_lieu,
                ten_nguyen_lieu=ing.ten_nguyen_lieu if ing else f"Nguyên liệu #{r.ma_nguyen_lieu}",
                don_vi_tinh=ing.don_vi_tinh if ing else "",
                ten_mo_hinh=r.ten_mo_hinh,
                nhom_mo_hinh=r.nhom_mo_hinh,
                val_mae=r.val_mae,
                val_rmse=r.val_rmse,
                val_mape=r.val_mape,
                test_mae=r.test_mae,
                test_rmse=r.test_rmse,
                test_mape=r.test_mape,
                test_smape=r.test_smape,
                test_r2=r.test_r2,
                mape_ngay_thuong=r.mape_ngay_thuong,
                mape_cuoi_tuan=r.mape_cuoi_tuan,
                do_lech_chuan_phan_du=r.do_lech_chuan_phan_du,
                cai_thien_so_voi_baseline_pct=r.cai_thien_so_voi_baseline_pct,
                la_mo_hinh_tot_nhat=r.la_mo_hinh_tot_nhat,
                tham_so_toi_uu=r.tham_so_toi_uu,
            )
        )
    return results


def lay_du_bao_7_ngay_tat_ca(
    db: Session,
    danh_muc: Optional[str] = None,
) -> List[DuBao7NgayNguyenLieuOut]:
    """Lấy kết quả dự báo 7 ngày tới kèm khoảng tin cậy 95% cho toàn bộ 15 nguyên liệu."""
    latest = _dam_bao_da_huan_luyen(db)

    query = db.query(Ingredient).filter(Ingredient.trang_thai == True)
    if danh_muc:
        query = query.filter(Ingredient.danh_muc == danh_muc)
    ingredients = query.order_by(Ingredient.ma_nguyen_lieu.asc()).all()

    best_evals = {
        r.ma_nguyen_lieu: r
        for r in db.query(KetQuaDanhGiaMoHinh)
        .filter(
            KetQuaDanhGiaMoHinh.ma_lan_huan_luyen == latest.ma_lan_huan_luyen,
            KetQuaDanhGiaMoHinh.la_mo_hinh_tot_nhat == True,
        )
        .all()
    }

    today = date.today()
    results: List[DuBao7NgayNguyenLieuOut] = []
    for ing in ingredients:
        f_rows = (
            db.query(DemandForecast)
            .filter(
                DemandForecast.ma_nguyen_lieu == ing.ma_nguyen_lieu,
                DemandForecast.ngay_du_bao >= today,
            )
            .order_by(DemandForecast.ngay_du_bao.asc())
            .limit(7)
            .all()
        )
        if not f_rows:
            continue

        ev = best_evals.get(ing.ma_nguyen_lieu)
        res_std = ev.do_lech_chuan_phan_du if ev else 0.0
        la_don_vi_nguyen = (ing.don_vi_tinh or "").strip().lower() in ("cái", "ly", "chiếc")
        precision = 0 if la_don_vi_nguyen else 2

        points: List[DiemDuBaoChiTietOut] = []
        for idx, f in enumerate(f_rows):
            margin = 1.96 * res_std * math.sqrt(1.0 + 0.05 * idx)
            points.append(
                DiemDuBaoChiTietOut(
                    ngay_du_bao=f.ngay_du_bao,
                    thu_trong_tuan=f.ngay_du_bao.weekday(),
                    nhan_thu=NHAN_THU_VN[f.ngay_du_bao.weekday()],
                    la_cuoi_tuan=f.ngay_du_bao.weekday() >= 5,
                    so_luong_du_bao=float(round(f.so_luong_du_bao, precision)),
                    can_duoi_95=float(round(max(0.0, f.so_luong_du_bao - margin), precision)),
                    can_tren_95=float(round(f.so_luong_du_bao + margin, precision)),
                    do_tin_cay=round(f.do_tin_cay or 0.9, 3),
                    phuong_phap=f.phuong_phap or (ev.ten_mo_hinh if ev else "Ensemble_HW_Ridge"),
                )
            )

        tong_7d = round(sum(p.so_luong_du_bao for p in points), 2)
        tb_ngay = round(tong_7d / len(points), 2) if points else 0.0
        peak_pt = max(points, key=lambda p: p.so_luong_du_bao)

        results.append(
            DuBao7NgayNguyenLieuOut(
                ma_nguyen_lieu=ing.ma_nguyen_lieu,
                ten_nguyen_lieu=ing.ten_nguyen_lieu,
                danh_muc=ing.danh_muc,
                don_vi_tinh=ing.don_vi_tinh,
                ton_kho_hien_tai=ing.ton_kho_hien_tai,
                muc_ton_an_toan=ing.muc_ton_an_toan,
                mo_hinh_duoc_chon=ev.ten_mo_hinh if ev else points[0].phuong_phap,
                test_mape=ev.test_mape if ev else 0.0,
                test_mae=ev.test_mae if ev else 0.0,
                cai_thien_so_voi_baseline_pct=ev.cai_thien_so_voi_baseline_pct if ev else 0.0,
                tong_du_bao_7_ngay=tong_7d,
                trung_binh_du_bao_ngay=tb_ngay,
                ngay_cao_diem=f"{peak_pt.nhan_thu} ({peak_pt.ngay_du_bao.strftime('%d/%m')})",
                du_bao_chi_tiet=points,
            )
        )

    return results


def lay_chi_tiet_du_bao_nguyen_lieu(
    db: Session,
    ma_nguyen_lieu: int,
) -> ChiTietDuBaoNguyenLieuOut:
    """
    Lấy phân tích chuyên sâu cho 1 nguyên liệu:
    chẩn đoán chuỗi thời gian, so sánh 5 mô hình, biểu đồ Actual vs Predicted trên tập Holdout Test,
    và dự báo 7 ngày tới kèm khoảng tin cậy 95%.
    """
    _dam_bao_da_huan_luyen(db)
    ing = db.query(Ingredient).filter(Ingredient.ma_nguyen_lieu == ma_nguyen_lieu).first()
    if not ing:
        raise ValueError(f"Không tìm thấy nguyên liệu mã {ma_nguyen_lieu}")

    records = (
        db.query(TieuHaoNguyenLieuNgay)
        .filter(TieuHaoNguyenLieuNgay.ma_nguyen_lieu == ma_nguyen_lieu)
        .order_by(TieuHaoNguyenLieuNgay.ngay.asc())
        .all()
    )
    dates, values, missing_cnt = _chuan_hoa_chuoi_nguyen_lieu(records)
    if len(values) < 42:
        raise ValueError(f"Chưa đủ dữ liệu lịch sử cho nguyên liệu mã {ma_nguyen_lieu}")

    res = _huan_luyen_va_danh_gia_mot_nguyen_lieu(
        ing=ing,
        dates=dates,
        values=values,
        missing_count=missing_cnt,
        horizon=7,
        start_forecast_date=date.today() + timedelta(days=1),
    )

    so_sanh = lay_bang_so_sanh_mo_hinh(db, ma_nguyen_lieu=ma_nguyen_lieu)
    tong_7d = round(sum(p.so_luong_du_bao for p in res["du_bao_7_ngay"]), 2)

    return ChiTietDuBaoNguyenLieuOut(
        ma_nguyen_lieu=ing.ma_nguyen_lieu,
        ten_nguyen_lieu=ing.ten_nguyen_lieu,
        danh_muc=ing.danh_muc,
        don_vi_tinh=ing.don_vi_tinh,
        mo_hinh_duoc_chon=res["best_model_name"],
        tham_so_toi_uu=res["best_params"],
        chan_doan_chuoi=res["chan_doan"],
        so_sanh_cac_mo_hinh=so_sanh,
        kiem_thu_thuc_te_vs_du_bao=res["kiem_thu_series"],
        du_bao_7_ngay_toi=res["du_bao_7_ngay"],
        tong_du_bao_7_ngay=tong_7d,
    )


def lay_lich_su_huan_luyen(db: Session, gioi_han: int = 20) -> List[LanChayMoHinhOut]:
    """Lấy lịch sử các lần huấn luyện mô hình dự báo AI."""
    rows = (
        db.query(LanChayMoHinh)
        .order_by(LanChayMoHinh.ma_lan_huan_luyen.desc())
        .limit(gioi_han)
        .all()
    )
    return [LanChayMoHinhOut.model_validate(r) for r in rows]
