"""
Tệp thực thi độc lập Quy trình Huấn luyện & Đánh giá Mô hình Dự báo Nhu cầu AI Tuần 6
(Kỹ sư Dữ liệu & AI: Ngô Kế Nhật Trường - 2380602390)

Chức năng:
  1. Đọc chuỗi thời gian tiêu hao 12 tháng của 15 nguyên liệu từ bảng `tieu_hao_nguyen_lieu_ngay` (Tuần 5).
  2. Thực hiện phân chia nghiêm ngặt theo thời gian: Train (275 ngày) / Validation (45 ngày) / Test (45 ngày).
  3. Huấn luyện & đối sánh công bằng 5 mô hình (Baseline_MA7, Seasonal_Naive_7D,
     HoltWinters_Seasonal, Fourier_Ridge_ML, Ensemble_HW_Ridge) bằng cơ chế Rolling-Origin 7 ngày.
  4. Lưu nhật ký vào `lan_chay_mo_hinh`, chi tiết đánh giá vào `ket_qua_danh_gia_mo_hinh`,
     và cập nhật 105 bản ghi dự báo 7 ngày (15 nguyên liệu x 7 ngày) vào `du_bao_nhu_cau`.
  5. Xuất 3 tệp kết quả vào `backend/du_lieu/du_bao_ai/` và đồng bộ DDL Tuần 6 vào `database_seed.sql`.
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.core.database import Base, SessionLocal, engine
from app.seed.seed_data import seed_database
from app.services.dich_vu_du_bao_ai import (
    chay_huan_luyen_va_du_bao_ai,
    lay_chi_tiet_du_bao_nguyen_lieu,
)


def dong_bo_ddl_tuan_6_vao_sql() -> None:
    """Bổ sung DDL 2 bảng Tuần 6 (`lan_chay_mo_hinh`, `ket_qua_danh_gia_mo_hinh`) vào database_seed.sql."""
    thu_muc_goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    duong_dan_sql = os.path.join(thu_muc_goc, "database_seed.sql")
    duong_dan_sql_backend = os.path.join(thu_muc_goc, "backend", "database_seed.sql")
    if not os.path.exists(duong_dan_sql):
        return

    with open(duong_dan_sql, "r", encoding="utf-8") as f:
        sql = f.read().replace("\r\n", "\n")

    if "DROP TABLE IF EXISTS ket_qua_danh_gia_mo_hinh CASCADE;" not in sql:
        sql = sql.replace(
            "DROP TABLE IF EXISTS nhat_ky_xu_ly_du_lieu CASCADE;",
            "DROP TABLE IF EXISTS ket_qua_danh_gia_mo_hinh CASCADE;\n"
            "DROP TABLE IF EXISTS lan_chay_mo_hinh CASCADE;\n"
            "DROP TABLE IF EXISTS nhat_ky_xu_ly_du_lieu CASCADE;",
        )

    if "CREATE TABLE lan_chay_mo_hinh (" not in sql:
        ddl_tuan_6 = (
            "-- 13. LAN_CHAY_MO_HINH & KET_QUA_DANH_GIA_MO_HINH (Tuần 6 - Dự báo Nhu cầu AI)\n"
            "CREATE TABLE lan_chay_mo_hinh (\n"
            "    ma_lan_huan_luyen SERIAL PRIMARY KEY,\n"
            "    ten_phien_ban VARCHAR(100) DEFAULT 'DU_BAO_NHU_CAU_AI_TUAN6_V1',\n"
            "    thoi_gian_chay TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n"
            "    so_nguyen_lieu INTEGER DEFAULT 15,\n"
            "    so_ngay_lich_su INTEGER DEFAULT 365,\n"
            "    so_ngay_train INTEGER DEFAULT 275,\n"
            "    so_ngay_val INTEGER DEFAULT 45,\n"
            "    so_ngay_test INTEGER DEFAULT 45,\n"
            "    chan_troi_du_bao INTEGER DEFAULT 7,\n"
            "    mo_hinh_tot_nhat_pho_bien VARCHAR(60) DEFAULT 'Ensemble_HW_Ridge',\n"
            "    baseline_mape_tb FLOAT DEFAULT 0.0,\n"
            "    ml_mape_tb FLOAT DEFAULT 0.0,\n"
            "    baseline_mae_tb FLOAT DEFAULT 0.0,\n"
            "    ml_mae_tb FLOAT DEFAULT 0.0,\n"
            "    baseline_rmse_tb FLOAT DEFAULT 0.0,\n"
            "    ml_rmse_tb FLOAT DEFAULT 0.0,\n"
            "    muc_giam_sai_so_mape_pct FLOAT DEFAULT 0.0,\n"
            "    thoi_gian_xu_ly_giay FLOAT DEFAULT 0.0,\n"
            "    trang_thai VARCHAR(30) DEFAULT 'THANH_CONG',\n"
            "    ghi_chu VARCHAR(500)\n"
            ");\n\n"
            "CREATE TABLE ket_qua_danh_gia_mo_hinh (\n"
            "    ma_danh_gia SERIAL PRIMARY KEY,\n"
            "    ma_lan_huan_luyen INTEGER REFERENCES lan_chay_mo_hinh(ma_lan_huan_luyen) ON DELETE CASCADE,\n"
            "    ma_nguyen_lieu INTEGER REFERENCES nguyen_lieu(ma_nguyen_lieu) ON DELETE CASCADE,\n"
            "    ten_mo_hinh VARCHAR(60) NOT NULL,\n"
            "    nhom_mo_hinh VARCHAR(20) NOT NULL,\n"
            "    val_mae FLOAT NOT NULL,\n"
            "    val_rmse FLOAT NOT NULL,\n"
            "    val_mape FLOAT NOT NULL,\n"
            "    test_mae FLOAT NOT NULL,\n"
            "    test_rmse FLOAT NOT NULL,\n"
            "    test_mape FLOAT NOT NULL,\n"
            "    test_smape FLOAT DEFAULT 0.0,\n"
            "    test_r2 FLOAT DEFAULT 0.0,\n"
            "    mape_ngay_thuong FLOAT DEFAULT 0.0,\n"
            "    mape_cuoi_tuan FLOAT DEFAULT 0.0,\n"
            "    do_lech_chuan_phan_du FLOAT DEFAULT 0.0,\n"
            "    cai_thien_so_voi_baseline_pct FLOAT DEFAULT 0.0,\n"
            "    la_mo_hinh_tot_nhat BOOLEAN DEFAULT FALSE,\n"
            "    tham_so_toi_uu TEXT\n"
            ");\n\n"
            "-- ============================================================================\n"
        )
        for anchor in ("-- PHẦN 2: CHÈN DỮ LIỆU MẪU", "-- Du lieu cho bang: nguoi_dung"):
            idx = sql.find(anchor)
            if idx != -1:
                sql = sql[:idx] + ddl_tuan_6 + sql[idx:]
                break

    for target_path in (duong_dan_sql, duong_dan_sql_backend):
        if os.path.exists(os.path.dirname(target_path)):
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(sql)


def main() -> None:
    print("=" * 92)
    print("  QUY TRINH HUAN LUYEN & DANH GIA MO HINH DU BAO NHU CAU AI - TUAN 6 (AI & DATA)")
    print("=" * 92)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        bao_cao = chay_huan_luyen_va_du_bao_ai(db, chan_troi_du_bao=7)
        run = bao_cao.lan_huan_luyen

        print("\n[1] THONG TIN LAN HUAN LUYEN & PHAN CHIA DU LIEU THEO THOI GIAN")
        print(f"    - Ma lan huan luyen           : #{run.ma_lan_huan_luyen} ({run.ten_phien_ban})")
        print(f"    - Pham vi du lieu             : {run.so_nguyen_lieu}/15 nguyen lieu x {run.so_ngay_lich_su} ngay")
        print(f"    - Chia tap Chronological      : Train={run.so_ngay_train}d | Val={run.so_ngay_val}d | Test={run.so_ngay_test}d")
        print(f"    - Chan troi du bao            : {run.chan_troi_du_bao} ngay toi (Rolling-Origin 7-Day Evaluation)")
        print(f"    - Thoi gian thuc thi          : {run.thoi_gian_xu_ly_giay:.3f} giay")
        print(f"    - Baseline_MA7 Test MAPE TB   : {run.baseline_mape_tb:.2f}%")
        print(f"    - Mo hinh ML tot nhat MAPE TB : {run.ml_mape_tb:.2f}% (Giam {run.muc_giam_sai_so_mape_pct:.2f}% sai so so voi Baseline!)")
        print(f"    - Mo hinh thang pho bien nhat : {run.mo_hinh_tot_nhat_pho_bien}")

        print("\n[2] BANG XEP HANG SO SANH 5 MO HINH TREN TAP HOLDOUT TEST (TB 15 NGUYEN LIEU)")
        print(
            f"    {'Mo hinh':<22} | {'Nhom':<8} | {'Val MAPE':>8} | {'Test MAPE':>9} | "
            f"{'95% CI MAPE':>15} | {'Test R2':>7} | {'Thuong':>7} | {'C.Tuan':>7} | {'Giam %':>7} | {'Thang':>5}"
        )
        print("    " + "-" * 116)
        for m in bao_cao.bang_xep_hang_mo_hinh:
            ci_str = f"[{m.khoang_tin_cay_bootstrap_95_mape[0]:.2f}, {m.khoang_tin_cay_bootstrap_95_mape[1]:.2f}]"
            print(
                f"    {m.ten_mo_hinh:<22} | {m.nhom_mo_hinh:<8} | {m.val_mape_tb:>7.2f}% | "
                f"{m.test_mape_tb:>8.2f}% | {ci_str:>15} | {m.test_r2_tb:>7.4f} | "
                f"{m.mape_ngay_thuong_tb:>6.2f}% | {m.mape_cuoi_tuan_tb:>6.2f}% | "
                f"{m.cai_thien_mape_so_voi_baseline_pct:>+6.2f}% | {m.so_nguyen_lieu_thang:>5}"
            )

        print("\n[3] KET QUA DU BAO 7 NGAY TOI CHO TOAN BO 15/15 NGUYEN LIEU")
        print(
            f"    {'Ma':<3} | {'Ten nguyen lieu':<38} | {'Mo hinh chon':<21} | "
            f"{'MAPE':>6} | {'Giam %':>7} | {'Tong 7N':>9} | {'DVT':<5} | {'Cao diem':<12}"
        )
        print("    " + "-" * 116)
        for item in bao_cao.danh_sach_du_bao_7_ngay:
            print(
                f"    {item.ma_nguyen_lieu:<3} | {item.ten_nguyen_lieu[:38]:<38} | {item.mo_hinh_duoc_chon:<21} | "
                f"{item.test_mape:>5.2f}% | {item.cai_thien_so_voi_baseline_pct:>+6.2f}% | "
                f"{item.tong_du_bao_7_ngay:>9.2f} | {item.don_vi_tinh:<5} | {item.ngay_cao_diem:<12}"
            )

        # In mẫu chẩn đoán chuỗi cho Robusta (#1)
        ct1 = lay_chi_tiet_du_bao_nguyen_lieu(db, ma_nguyen_lieu=1)
        cd = ct1.chan_doan_chuoi
        print("\n[4] CHAN DOAN CHUOI THOI GIAN MAU - HAT CA PHE ROBUSTA (#1)")
        print(f"    - Trung binh/ngay: {cd.trung_binh_ngay} kg | Do lech chuan: {cd.do_lech_chuan} kg | Khuyet thieu: {cd.so_gia_tri_khuyet_thieu}")
        print(f"    - Tu tuong quan  : ACF(lag=1) = {cd.tu_tuong_quan_lag_1} | ACF(lag=7) = {cd.tu_tuong_quan_lag_7}")
        print(f"    - Tinh mua vu    : {cd.danh_gia_mua_vu}")
        print(f"    - Tinh dung      : {cd.danh_gia_tinh_dung}")

        dong_bo_ddl_tuan_6_vao_sql()
        print("\n[5] CAC TEP KET QUA DA XUAT")
        print(f"    - CSV Du bao 7 ngay       : {bao_cao.duong_dan_file_du_bao}")
        print(f"    - CSV So sanh 5 mo hinh   : {bao_cao.duong_dan_file_so_sanh}")
        print(f"    - JSON Bao cao tong hop   : {bao_cao.duong_dan_file_bao_cao_json}")
        print("    - Da dong bo DDL Tuan 6 vao database_seed.sql.")
        print("\n" + "=" * 92)
    finally:
        db.close()


if __name__ == "__main__":
    main()
