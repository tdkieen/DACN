"""
Tệp thực thi độc lập Quy trình Dữ liệu Tuần 5 (Kỹ sư Dữ liệu & AI: Ngô Kế Nhật Trường - 2380602390)
Chức năng:
  1. Thu thập dữ liệu bán hàng POS thô 12 tháng (365 ngày)
     -> backend/du_lieu/du_lieu_tho/lich_su_ban_hang_tho_12_thang.csv
  2. Làm sạch dữ liệu (Khử trùng lặp, xử lý khuyết thiếu, lọc số âm, cắt ngưỡng ngoại lai bằng khoảng tứ phân vị IQR)
     -> backend/du_lieu/du_lieu_sach/lich_su_ban_hang_sach_12_thang.csv
  3. Bóc tách định mức nguyên liệu theo công thức pha chế BOM (12 món -> 15 nguyên liệu)
  4. Tạo đặc trưng chuỗi thời gian (Tiêu hao hôm trước, Tiêu hao 7 ngày trước, Trung bình trượt 7 ngày, Độ lệch chuẩn 7 ngày)
     -> backend/du_lieu/du_lieu_sach/tieu_hao_nguyen_lieu_ngay_12_thang.csv
  5. Nạp toàn bộ dữ liệu sạch vào CSDL, đồng bộ database_seed.sql và in báo cáo kiểm định chất lượng dữ liệu.
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.core.database import SessionLocal, Base, engine
from app.seed.seed_data import seed_database
from app.services.dich_vu_dinh_muc_bom import (
    DANH_SACH_THUC_DON_CHUAN,
    DANH_SACH_CONG_THUC_BOM_CHUAN,
    chay_quy_trinh_boc_tach_bom,
    lay_thuc_don_kem_dinh_muc_bom,
    lay_chuoi_thoi_gian_tieu_hao,
)


def dong_bo_file_sql_mau(bao_cao) -> None:
    """Đồng bộ cấu trúc bảng Tuần 5 và 12 món + 56 định mức BOM vào file database_seed.sql."""
    thu_muc_goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    duong_dan_sql = os.path.join(thu_muc_goc, "database_seed.sql")
    duong_dan_sql_backend = os.path.join(thu_muc_goc, "backend", "database_seed.sql")
    if not os.path.exists(duong_dan_sql):
        return

    with open(duong_dan_sql, "r", encoding="utf-8") as f:
        sql = f.read().replace("\r\n", "\n")

    # Chuẩn hóa lệnh xóa bảng cũ
    sql = sql.replace(
        "DROP TABLE IF EXISTS nhat_ky_etl_pipeline CASCADE;\n",
        "DROP TABLE IF EXISTS nhat_ky_xu_ly_du_lieu CASCADE;\n",
    )
    if "DROP TABLE IF EXISTS nhat_ky_xu_ly_du_lieu CASCADE;" not in sql:
        sql = sql.replace(
            "DROP TABLE IF EXISTS recipes_bom CASCADE;",
            "DROP TABLE IF EXISTS nhat_ky_xu_ly_du_lieu CASCADE;\n"
            "DROP TABLE IF EXISTS tieu_hao_nguyen_lieu_ngay CASCADE;\n"
            "DROP TABLE IF EXISTS lich_su_ban_hang CASCADE;\n"
            "DROP TABLE IF EXISTS recipes_bom CASCADE;",
        )

    # Thay thế phần định nghĩa bảng Tuần 5 bằng tên cột 100% tiếng Việt
    vi_tri_recipes_bom = sql.find("CREATE TABLE recipes_bom (")
    vi_tri_insert_start = sql.find("-- PHẦN 2: CHÈN DỮ LIỆU MẪU")
    if vi_tri_recipes_bom != -1 and vi_tri_insert_start != -1:
        ddl_tuan_5 = (
            "CREATE TABLE recipes_bom (\n"
            "    ma_dinh_muc SERIAL PRIMARY KEY,\n"
            "    ma_mon INTEGER REFERENCES menu_items(ma_mon) ON DELETE CASCADE,\n"
            "    ma_nguyen_lieu INTEGER REFERENCES nguyen_lieu(ma_nguyen_lieu) ON DELETE CASCADE,\n"
            "    so_luong_tieu_hao FLOAT NOT NULL,\n"
            "    ghi_chu VARCHAR(100)\n"
            ");\n\n"
            "-- 12. LICH_SU_BAN_HANG, TIEU_HAO_NGUYEN_LIEU_NGAY & NHAT_KY_XU_LY_DU_LIEU (Tuần 5)\n"
            "CREATE TABLE lich_su_ban_hang (\n"
            "    ma_ban_hang SERIAL PRIMARY KEY,\n"
            "    ma_hoa_don_pos VARCHAR(50) NOT NULL,\n"
            "    ngay_ban DATE NOT NULL,\n"
            "    ca_ban VARCHAR(20) DEFAULT 'SANG',\n"
            "    ma_mon INTEGER REFERENCES menu_items(ma_mon) ON DELETE CASCADE,\n"
            "    so_luong_ly FLOAT NOT NULL,\n"
            "    don_gia_ban FLOAT NOT NULL,\n"
            "    thanh_tien FLOAT NOT NULL,\n"
            "    da_boc_tach_bom BOOLEAN DEFAULT TRUE,\n"
            "    thoi_gian_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
            ");\n\n"
            "CREATE TABLE tieu_hao_nguyen_lieu_ngay (\n"
            "    ma_tieu_hao SERIAL PRIMARY KEY,\n"
            "    ngay DATE NOT NULL,\n"
            "    ma_nguyen_lieu INTEGER REFERENCES nguyen_lieu(ma_nguyen_lieu) ON DELETE CASCADE,\n"
            "    so_luong_tieu_hao FLOAT NOT NULL,\n"
            "    so_ly_lien_quan INTEGER DEFAULT 0,\n"
            "    thu_trong_tuan INTEGER NOT NULL,\n"
            "    la_cuoi_tuan BOOLEAN DEFAULT FALSE,\n"
            "    he_so_mua_vu FLOAT DEFAULT 1.0,\n"
            "    tieu_hao_hom_truoc FLOAT,\n"
            "    tieu_hao_7_ngay_truoc FLOAT,\n"
            "    trung_binh_truot_7_ngay FLOAT,\n"
            "    do_lech_chuan_7_ngay FLOAT,\n"
            "    thoi_gian_cap_nhat TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
            ");\n\n"
            "CREATE TABLE nhat_ky_xu_ly_du_lieu (\n"
            "    ma_lan_chay SERIAL PRIMARY KEY,\n"
            "    ten_quy_trinh VARCHAR(100) DEFAULT 'QUY_TRINH_BOC_TACH_DINH_MUC_V1',\n"
            "    thoi_gian_chay TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n"
            "    tong_dong_tho INTEGER DEFAULT 0,\n"
            "    so_dong_trung_lap INTEGER DEFAULT 0,\n"
            "    so_dong_thieu_du_lieu INTEGER DEFAULT 0,\n"
            "    so_dong_am_hoac_loi INTEGER DEFAULT 0,\n"
            "    so_dong_ngoai_lai_da_xu_ly INTEGER DEFAULT 0,\n"
            "    tong_dong_sach INTEGER DEFAULT 0,\n"
            "    ty_le_du_lieu_sach FLOAT DEFAULT 100.0,\n"
            "    so_ngay_xu_ly INTEGER DEFAULT 365,\n"
            "    tong_ban_ghi_tieu_hao_sinh_ra INTEGER DEFAULT 0,\n"
            "    trang_thai VARCHAR(30) DEFAULT 'THANH_CONG',\n"
            "    ghi_chu VARCHAR(500)\n"
            ");\n\n"
            "-- ============================================================================\n"
        )
        sql = sql[:vi_tri_recipes_bom] + ddl_tuan_5 + sql[vi_tri_insert_start:]

    vi_tri_menu = sql.find("-- Du lieu cho bang: menu_items")
    if vi_tri_menu != -1:
        phan_dau = sql[:vi_tri_menu]
        dong_menu = ["-- Du lieu cho bang: menu_items (12 dong)"]
        for m in DANH_SACH_THUC_DON_CHUAN:
            dong_menu.append(
                f"INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) "
                f"VALUES ({m['ma_mon']}, '{m['ten_mon']}', '{m['danh_muc']}', {m['don_gia_ban']}, TRUE);"
            )

        dong_bom = ["\n-- Du lieu cho bang: recipes_bom (56 dong - phu 100% ca 15 nguyen lieu)"]
        for idx, r in enumerate(DANH_SACH_CONG_THUC_BOM_CHUAN, start=1):
            dong_bom.append(
                f"INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) "
                f"VALUES ({idx}, {r['ma_mon']}, {r['ma_nguyen_lieu']}, {r['so_luong_tieu_hao']}, '{r['ghi_chu']}');"
            )

        dong_nhat_ky = [
            "\n-- Du lieu cho bang: nhat_ky_xu_ly_du_lieu (1 dong)",
            f"INSERT INTO nhat_ky_xu_ly_du_lieu (ma_lan_chay, ten_quy_trinh, tong_dong_tho, so_dong_trung_lap, "
            f"so_dong_thieu_du_lieu, so_dong_am_hoac_loi, so_dong_ngoai_lai_da_xu_ly, tong_dong_sach, "
            f"ty_le_du_lieu_sach, so_ngay_xu_ly, tong_ban_ghi_tieu_hao_sinh_ra, trang_thai, ghi_chu) "
            f"VALUES (1, '{bao_cao.ten_quy_trinh}', {bao_cao.tong_dong_tho}, {bao_cao.so_dong_trung_lap}, "
            f"{bao_cao.so_dong_thieu_du_lieu}, {bao_cao.so_dong_am_hoac_loi}, {bao_cao.so_dong_ngoai_lai_da_xu_ly}, "
            f"{bao_cao.tong_dong_sach}, {bao_cao.ty_le_du_lieu_sach}, {bao_cao.so_ngay_xu_ly}, "
            f"{bao_cao.tong_ban_ghi_tieu_hao_sinh_ra}, '{bao_cao.trang_thai}', '{bao_cao.ghi_chu}');",
        ]

        dong_sequence = [
            "\n-- Cap nhat Sequence ID PostgreSQL sau khi chen ID co dinh",
            "SELECT setval(pg_get_serial_sequence('nguoi_dung', 'ma_nguoi_dung'), COALESCE(MAX(ma_nguoi_dung), 1)) FROM nguoi_dung;",
            "SELECT setval(pg_get_serial_sequence('nha_cung_cap', 'ma_nha_cung_cap'), COALESCE(MAX(ma_nha_cung_cap), 1)) FROM nha_cung_cap;",
            "SELECT setval(pg_get_serial_sequence('nguyen_lieu', 'ma_nguyen_lieu'), COALESCE(MAX(ma_nguyen_lieu), 1)) FROM nguyen_lieu;",
            "SELECT setval(pg_get_serial_sequence('lo_hang', 'ma_lo_hang'), COALESCE(MAX(ma_lo_hang), 1)) FROM lo_hang;",
            "SELECT setval(pg_get_serial_sequence('giao_dich_kho', 'ma_giao_dich'), COALESCE(MAX(ma_giao_dich), 1)) FROM giao_dich_kho;",
            "SELECT setval(pg_get_serial_sequence('du_bao_nhu_cau', 'ma_du_bao'), COALESCE(MAX(ma_du_bao), 1)) FROM du_bao_nhu_cau;",
            "SELECT setval(pg_get_serial_sequence('phieu_de_xuat_mua', 'ma_phieu_de_xuat'), COALESCE(MAX(ma_phieu_de_xuat), 1)) FROM phieu_de_xuat_mua;",
            "SELECT setval(pg_get_serial_sequence('ct_de_xuat_mua', 'ma_chi_tiet'), COALESCE(MAX(ma_chi_tiet), 1)) FROM ct_de_xuat_mua;",
            "SELECT setval(pg_get_serial_sequence('lich_su_duyet', 'ma_lich_su'), COALESCE(MAX(ma_lich_su), 1)) FROM lich_su_duyet;",
            "SELECT setval(pg_get_serial_sequence('menu_items', 'ma_mon'), COALESCE(MAX(ma_mon), 1)) FROM menu_items;",
            "SELECT setval(pg_get_serial_sequence('recipes_bom', 'ma_dinh_muc'), COALESCE(MAX(ma_dinh_muc), 1)) FROM recipes_bom;",
            "SELECT setval(pg_get_serial_sequence('nhat_ky_xu_ly_du_lieu', 'ma_lan_chay'), COALESCE(MAX(ma_lan_chay), 1)) FROM nhat_ky_xu_ly_du_lieu;",
        ]

        toan_bo_sql = phan_dau + "\n".join(dong_menu + dong_bom + dong_nhat_ky + dong_sequence) + "\n"
        for p in (duong_dan_sql, duong_dan_sql_backend):
            with open(p, "w", encoding="utf-8") as out_f:
                out_f.write(toan_bo_sql)


def chay_chuong_trinh_chinh():
    print("=" * 84)
    print("  TUẦN 5 - KỸ SƯ DỮ LIỆU & AI: QUY TRÌNH LÀM SẠCH DỮ LIỆU & BÓC TÁCH ĐỊNH MỨC BOM")
    print("  Sinh viên thực hiện: Ngô Kế Nhật Trường (MSSV: 2380602390)")
    print("=" * 84)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        bao_cao = chay_quy_trinh_boc_tach_bom(db, so_ngay=365)
        dong_bo_file_sql_mau(bao_cao)

        print("\n[1] BÁO CÁO KIỂM ĐỊNH & LÀM SẠCH DỮ LIỆU BÁN HÀNG POS 12 THÁNG:")
        print(f"  - Tổng số bản ghi bán hàng POS thô thu thập : {bao_cao.tong_dong_tho:,} dòng")
        print(f"  - Bản ghi trùng lặp đã loại bỏ              : {bao_cao.so_dong_trung_lap:,} dòng")
        print(f"  - Bản ghi thiếu dữ liệu đã xử lý            : {bao_cao.so_dong_thieu_du_lieu:,} dòng")
        print(f"  - Bản ghi số lượng âm hoặc bằng 0 đã lọc    : {bao_cao.so_dong_am_hoac_loi:,} dòng")
        print(f"  - Ngoại lai xử lý bằng tứ phân vị (IQR)     : {bao_cao.so_dong_ngoai_lai_da_xu_ly:,} dòng")
        print(f"  - Tổng bản ghi bán hàng POS sạch hợp lệ     : {bao_cao.tong_dong_sach:,} dòng ({bao_cao.ty_le_du_lieu_sach}%)")

        danh_sach_mon = lay_thuc_don_kem_dinh_muc_bom(db)
        print(f"\n[2] MA TRẬN ĐỊNH MỨC CÔNG THỨC PHA CHẾ ({len(danh_sach_mon)} MÓN ĐỒ UỐNG):")
        for m in danh_sach_mon:
            chuoi_bom = ", ".join(
                f"{r.ten_nguyen_lieu}: {r.so_luong_tieu_hao} {r.don_vi_tinh}"
                for r in m.cong_thuc_bom
            )
            print(
                f"  - [{m.ma_mon:02d}] {m.ten_mon:<30} | Giá bán: {m.don_gia_ban:>7,.0f}đ "
                f"| Giá vốn BOM: {m.gia_von_nguyen_lieu:>6,.0f}đ (Lãi gộp: {m.ty_suat_loi_nhuan_gop}%)"
            )
            print(f"         -> Định mức: {chuoi_bom}")

        print("\n[3] THỐNG KÊ CHUỖI THỜI GIAN TIÊU HAO 15 NGUYÊN LIỆU (365 NGÀY):")
        print(f"  {'Mã':<4} {'Tên nguyên liệu':<38} {'ĐVT':<6} {'Tổng 365 ngày':>14} {'TB/ngày':>10} {'Tăng cuối tuần':>15}")
        print("  " + "-" * 92)
        for ma_nl in range(1, 16):
            ts = lay_chuoi_thoi_gian_tieu_hao(db, ma_nguyen_lieu=ma_nl, so_ngay=365)
            print(
                f"  #{ts.ma_nguyen_lieu:<3} {ts.ten_nguyen_lieu:<38} {ts.don_vi_tinh:<6} "
                f"{ts.tong_tieu_hao:>14,.2f} {ts.trung_binh_ngay:>10,.3f} "
                f"{ts.ty_le_tang_cuoi_tuan_pct:>+14.1f}%"
            )

        print("\n[4] CÁC TẬP DỮ LIỆU ĐÃ XUẤT (CHUẨN BỊ CHO MÔ HÌNH DỰ BÁO TUẦN 6):")
        print(f"  - Tập dữ liệu bán hàng POS thô (12 tháng)  : {bao_cao.duong_dan_file_tho}")
        print(f"  - Tập dữ liệu bán hàng POS sạch (12 tháng) : {bao_cao.duong_dan_file_sach}")
        print(f"  - Tập chuỗi thời gian tiêu hao nguyên liệu : {bao_cao.duong_dan_file_tieu_hao}")
        print("=" * 84)
        print("[THÀNH CÔNG] HOÀN TẤT 100% QUY TRÌNH DỮ LIỆU TUẦN 5!")
    finally:
        db.close()


if __name__ == "__main__":
    chay_chuong_trinh_chinh()
