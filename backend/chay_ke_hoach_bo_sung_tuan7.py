"""
Tệp thực thi độc lập Quy trình Kế hoạch Bổ sung Tồn kho (ROP, Safety Stock, MCDM) &
Kiến trúc Kết hợp Đa Mô hình (Hybrid Multi-Model AI Procurement Agent) – Tuần 7
(Kỹ sư Dữ liệu & AI: Ngô Kế Nhật Trường - 2380602390)

Chức năng:
  1. Đảm bảo dữ liệu dự báo nhu cầu 7 ngày từ 5 mô hình ML Tuần 6 đã sẵn sàng trong CSDL.
  2. Xây dựng Kế hoạch bổ sung Tuần 7 cho toàn bộ 15 nguyên liệu:
     - Tính Điểm đặt hàng lại ROP = (Nhu cầu dự báo TB/ngày × Lead Time NCC tối ưu) + Safety Stock
     - Tính Safety Stock gợi ý AI từ cận trên khoảng tin cậy 95% của mô hình ML
     - Xếp hạng Nhà cung cấp bằng thuật toán đa tiêu chí MCDM (Giá 40%, Giao hàng 30%, Chất lượng 15%, Uy tín 15%)
     - Chuẩn hóa số lượng đặt theo MOQ và đơn vị rời rạc (`DISCRETE_UNITS`) + Kiểm tra lô sắp hết hạn FEFO
  3. Kích hoạt Hybrid Multi-Model AI Procurement Agent (Gemini Function Calling 4 Tools an toàn),
     lưu vết vào bảng `nhat_ky_ai_agent` và sinh phiếu đề xuất ở trạng thái `CHO_DUYET`.
  4. Xuất các tệp dữ liệu Tuần 7 vào `backend/du_lieu/ke_hoach_bo_sung_tuan7/` và đồng bộ DDL vào `database_seed.sql`.
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
from app.services.dich_vu_du_bao_ai import chay_huan_luyen_va_du_bao_ai
from app.services.dich_vu_ke_hoach_bo_sung import (
    FILE_BAO_CAO_AGENT_JSON,
    FILE_KE_HOACH_CSV,
    chay_ai_procurement_agent,
    lay_thong_tin_kien_truc_multi_model,
    xay_dung_ke_hoach_bo_sung,
)


def dong_bo_ddl_tuan_7_vao_sql() -> None:
    """Bổ sung DDL bảng `nhat_ky_ai_agent` (Tuần 7 - Hybrid Multi-Model AI Agent) vào database_seed.sql."""
    thu_muc_goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    duong_dan_sql = os.path.join(thu_muc_goc, "database_seed.sql")
    duong_dan_sql_backend = os.path.join(thu_muc_goc, "backend", "database_seed.sql")
    if not os.path.exists(duong_dan_sql):
        return

    with open(duong_dan_sql, "r", encoding="utf-8") as f:
        sql = f.read().replace("\r\n", "\n")

    if "DROP TABLE IF EXISTS nhat_ky_ai_agent CASCADE;" not in sql:
        sql = sql.replace(
            "DROP TABLE IF EXISTS ket_qua_danh_gia_mo_hinh CASCADE;",
            "DROP TABLE IF EXISTS nhat_ky_ai_agent CASCADE;\n"
            "DROP TABLE IF EXISTS ket_qua_danh_gia_mo_hinh CASCADE;",
        )

    if "CREATE TABLE nhat_ky_ai_agent (" not in sql:
        ddl_tuan_7 = (
            "-- 14. NHAT_KY_AI_AGENT (Tuần 7 - Kiến trúc Kết hợp Đa Mô hình Hybrid Multi-Model AI Agent)\n"
            "CREATE TABLE nhat_ky_ai_agent (\n"
            "    ma_nhat_ky SERIAL PRIMARY KEY,\n"
            "    thoi_gian TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n"
            "    yeu_cau_dau_vao TEXT NOT NULL,\n"
            "    che_do_agent VARCHAR(50) DEFAULT 'HYBRID_MULTI_MODEL_ORCHESTRATOR',\n"
            "    mo_hinh_llm VARCHAR(60) DEFAULT 'gemini-3.8-flash',\n"
            "    cac_mo_hinh_ket_hop VARCHAR(255) NOT NULL,\n"
            "    danh_sach_tool_da_goi TEXT NOT NULL,\n"
            "    so_buoc_suy_luan INTEGER DEFAULT 4,\n"
            "    ma_phieu_de_xuat INTEGER,\n"
            "    phan_hoi_agent TEXT NOT NULL,\n"
            "    thoi_gian_xu_ly_giay FLOAT DEFAULT 0.0\n"
            ");\n\n"
            "-- ============================================================================\n"
        )
        for anchor in ("-- PHẦN 2: CHÈN DỮ LIỆU MẪU", "-- Du lieu cho bang: nguoi_dung"):
            idx = sql.find(anchor)
            if idx != -1:
                sql = sql[:idx] + ddl_tuan_7 + sql[idx:]
                break

    for target_path in (duong_dan_sql, duong_dan_sql_backend):
        if os.path.exists(os.path.dirname(target_path)):
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(sql)


def main() -> None:
    print("=" * 108)
    print("  KE HOACH BO SUNG TON KHO (ROP, MCDM) & HYBRID MULTI-MODEL AI AGENT - TUAN 7 (AI & DATA)")
    print("=" * 108)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        # Đảm bảo dự báo 7 ngày từ 5 mô hình ML Tuần 6 luôn mới nhất
        chay_huan_luyen_va_du_bao_ai(db, chan_troi_du_bao=7)

        kien_truc = lay_thong_tin_kien_truc_multi_model()
        print("\n[1] KIEN TRUC KET HOP DA MO HINH (HYBRID MULTI-MODEL AI ARCHITECTURE)")
        print(f"    - Ten kien truc         : {kien_truc.ten_kien_truc}")
        print(f"    - Model Agent mac dinh  : {kien_truc.mo_hinh_agent_mac_dinh} (Suy luan sau: {kien_truc.mo_hinh_suy_luan_sau})")
        print(f"    - Gemini Cloud API Key  : {'Da cau hinh (Cloud Active)' if kien_truc.da_cau_hinh_gemini_api_key else 'Chua dien key (Hybrid Local Orchestrator Active)'}")
        for comp in kien_truc.cac_mo_hinh_ket_hop:
            print(f"      * [{comp.tang_kien_truc}] {comp.ten_mo_hinh} ({comp.trang_thai_hoat_dong})")

        ke_hoach = xay_dung_ke_hoach_bo_sung(db, chi_lay_can_dat=False)
        so_can_dat = sum(1 for x in ke_hoach if x.can_dat_hang)
        tong_chi_phi = sum(x.thanh_tien_du_kien for x in ke_hoach if x.can_dat_hang)

        print(f"\n[2] BANG KE HOACH BO SUNG TON KHO TUAN 7 ({so_can_dat}/{len(ke_hoach)} NGUYEN LIEU CAN DAT HANG)")
        print(
            f"    {'Ma':<2} | {'Ten nguyen lieu':<34} | {'Ton':>6} | {'SS':>5} | {'ROP':>6} | "
            f"{'7N(ML)':>7} | {'Mo hinh ML':<20} | {'Can dat':>7} | {'DVT':<4} | {'NCC Toi uu (MCDM)':<34} | {'Diem':>5}"
        )
        print("    " + "-" * 150)
        for p in ke_hoach:
            ncc_ten = p.nha_cung_cap_chon.ten_nha_cung_cap[:34] if p.nha_cung_cap_chon else "Chua co bao gia"
            ncc_diem = f"{p.nha_cung_cap_chon.diem_tong_hop_mcdm:>5.1f}" if p.nha_cung_cap_chon else "  N/A"
            flag = "*" if p.can_dat_hang else " "
            print(
                f"   {flag}{p.ma_nguyen_lieu:<2} | {p.ten_nguyen_lieu[:34]:<34} | {p.ton_kho_hien_tai:>6.2f} | "
                f"{p.muc_ton_an_toan:>5.1f} | {p.diem_dat_hang_lai_rop:>6.2f} | {p.nhu_cau_du_bao_7ngay:>7.2f} | "
                f"{p.mo_hinh_du_bao:<20} | {p.so_luong_can_dat:>7.2f} | {p.don_vi_tinh:<4} | {ncc_ten:<34} | {ncc_diem}"
            )
        print(f"    => Tong chi phi du kien cho cac mat hang duoi ROP (*): {tong_chi_phi:,.0f} VND")

        ket_qua_agent = chay_ai_procurement_agent(db)
        print("\n[3] NHAT KY THUC THI FUNCTION CALLING CUA HYBRID MULTI-MODEL AI AGENT")
        print(f"    - Ma nhat ky            : #{ket_qua_agent.ma_nhat_ky} ({ket_qua_agent.che_do_agent})")
        print(f"    - Cac mo hinh ket hop   : {', '.join(ket_qua_agent.cac_mo_hinh_ket_hop)}")
        print(f"    - So buoc goi Tool      : {ket_qua_agent.so_buoc_suy_luan} buoc ({ket_qua_agent.thoi_gian_xu_ly_giay:.3f} giay)")
        print(f"    - Phieu de xuat sinh ra : #{ket_qua_agent.ma_phieu_de_xuat} (CHO_DUYET) - {ket_qua_agent.so_mat_hang_de_xuat} mat hang - {ket_qua_agent.tong_tien_de_xuat:,.0f} VND")
        for b in ket_qua_agent.danh_sach_tool_da_goi:
            print(f"      [Buoc {b.buoc:02d}] Tool `{b.ten_tool}` ({b.mo_hinh_con}) -> {b.tom_tat_ket_qua}")

        dong_bo_ddl_tuan_7_vao_sql()
        print("\n[4] CAC TEP KET QUA TUAN 7 DA XUAT")
        print(f"    - CSV Ke hoach bo sung ROP : {FILE_KE_HOACH_CSV}")
        print(f"    - JSON Bao cao AI Agent    : {FILE_BAO_CAO_AGENT_JSON}")
        print("    - Da dong bo DDL Tuan 7 (`nhat_ky_ai_agent`) vao database_seed.sql.")
        print("\n" + "=" * 108)
    finally:
        db.close()


if __name__ == "__main__":
    main()
