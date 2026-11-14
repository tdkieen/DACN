"""
Mô-đun tự động đồng bộ dữ liệu giữa SQLite cục bộ, các bảng SQLAlchemy chuẩn (chữ thường)
và các bảng viết HOA có dấu ngoặc kép ("PHIEU_DE_XUAT_MUA", "NGUYEN_LIEU", v.v.) trên pgAdmin 4 / PostgreSQL.
"""
import os
import sqlite3
from sqlalchemy import text
from sqlalchemy.engine import Engine

DANH_SACH_BANG_DONG_BO = [
    ("nguoi_dung", "NGUOI_DUNG", "ma_nguoi_dung"),
    ("nha_cung_cap", "NHA_CUNG_CAP", "ma_nha_cung_cap"),
    ("nguyen_lieu", "NGUYEN_LIEU", "ma_nguyen_lieu"),
    ("cc_nguyen_lieu", "CC_NGUYEN_LIEU", None),
    ("lo_hang", "LO_HANG", "ma_lo_hang"),
    ("giao_dich_kho", "GIAO_DICH_KHO", "ma_giao_dich"),
    ("du_bao_nhu_cau", "DU_BAO_NHU_CAU", "ma_du_bao"),
    ("phieu_de_xuat_mua", "PHIEU_DE_XUAT_MUA", "ma_phieu_de_xuat"),
    ("ct_de_xuat_mua", "CT_DE_XUAT_MUA", "ma_chi_tiet"),
    ("lich_su_duyet", "LICH_SU_DUYET", "ma_lich_su"),
]

DANH_SACH_BANG_TUAN_5 = [
    ("menu_items", "ma_mon"),
    ("recipes_bom", "ma_dinh_muc"),
    ("lich_su_ban_hang", "ma_ban_hang"),
    ("tieu_hao_nguyen_lieu_ngay", "ma_tieu_hao"),
    ("nhat_ky_xu_ly_du_lieu", "ma_lan_chay"),
]


def chuyen_du_lieu_sqlite_sang_postgres(pg_engine: Engine) -> None:
    """
    Chuyển toàn bộ dữ liệu đã thao tác trên Web (khi đang ở chế độ dự phòng SQLite)
    vào các bảng PostgreSQL để không bị mất bất kỳ phiếu đề xuất hay giao dịch nào.
    """
    thu_muc_backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    duong_dan_sqlite = os.path.join(thu_muc_backend, "coffee_inventory.db")
    if not os.path.exists(duong_dan_sqlite):
        return

    sl_conn = sqlite3.connect(duong_dan_sqlite)
    sl_conn.row_factory = sqlite3.Row
    sl_cur = sl_conn.cursor()

    tat_ca_bang = [(b_thuong, pk) for b_thuong, _, pk in DANH_SACH_BANG_DONG_BO] + DANH_SACH_BANG_TUAN_5

    try:
        for ten_bang, cot_pk in tat_ca_bang:
            try:
                sl_cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (ten_bang,),
                )
                if not sl_cur.fetchone():
                    continue

                sl_cur.execute(f'SELECT COUNT(*) FROM "{ten_bang}"')
                so_dong_sqlite = sl_cur.fetchone()[0]
                if so_dong_sqlite == 0:
                    continue

                with pg_engine.begin() as pg_conn:
                    so_dong_pg = pg_conn.execute(text(f'SELECT COUNT(*) FROM "{ten_bang}"')).scalar() or 0
                    col_rows = pg_conn.execute(
                        text(
                            """
                            SELECT column_name, data_type
                            FROM information_schema.columns
                            WHERE table_schema = 'public' AND table_name = :tname
                            """
                        ),
                        {"tname": ten_bang},
                    ).fetchall()
                    pg_col_types = {r[0]: r[1] for r in col_rows}
                    if not pg_col_types:
                        continue

                    if so_dong_pg < so_dong_sqlite:
                        sl_cur.execute(f'SELECT * FROM "{ten_bang}"')
                        rows = sl_cur.fetchall()
                        if rows:
                            common_cols = [c for c in rows[0].keys() if c in pg_col_types]
                            if common_cols:
                                col_list_sql = ", ".join(f'"{c}"' for c in common_cols)
                                param_list_sql = ", ".join(f":{c}" for c in common_cols)
                                insert_sql = text(
                                    f'INSERT INTO "{ten_bang}" ({col_list_sql}) VALUES ({param_list_sql}) ON CONFLICT DO NOTHING'
                                )

                                batch_params = []
                                for r in rows:
                                    item = {}
                                    for c in common_cols:
                                        val = r[c]
                                        if pg_col_types[c] == "boolean" and val is not None:
                                            val = bool(val)
                                        item[c] = val
                                    batch_params.append(item)

                                pg_conn.execute(insert_sql, batch_params)

                    # Luôn cập nhật lại sequence cho khóa chính tự tăng
                    if cot_pk and cot_pk in pg_col_types:
                        pg_conn.execute(
                            text(
                                f"""
                                SELECT setval(
                                    pg_get_serial_sequence('"{ten_bang}"', '{cot_pk}'),
                                    COALESCE((SELECT MAX("{cot_pk}") FROM "{ten_bang}"), 1),
                                    true
                                )
                                """
                            )
                        )
            except Exception as e_tbl:
                print(f"[CSDL] Lưu ý bảng {ten_bang}: {e_tbl}")
    finally:
        sl_conn.close()


def dong_bo_bang_chu_hoa_pgadmin(pg_engine: Engine) -> None:
    """
    Đồng bộ dữ liệu từ các bảng chuẩn chữ thường (phieu_de_xuat_mua, nguyen_lieu, ...)
    sang các bảng VIẾT HOA ("PHIEU_DE_XUAT_MUA", "NGUYEN_LIEU", ...) trong pgAdmin 4 nếu tồn tại.
    """
    try:
        # 1. Đảm bảo các kiểu ENUM trong bảng viết HOA có đủ các nhãn trạng thái của Web
        with pg_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as auto_conn:
            for ten_thuong, ten_hoa, _ in DANH_SACH_BANG_DONG_BO:
                enum_cols = auto_conn.execute(
                    text(
                        """
                        SELECT column_name, udt_name
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = :thoa
                          AND data_type = 'USER-DEFINED'
                        """
                    ),
                    {"thoa": ten_hoa},
                ).fetchall()

                for col_name, udt_name in enum_cols:
                    # Kiểm tra cột tương ứng ở bảng chữ thường có các giá trị nào
                    vals = auto_conn.execute(
                        text(f'SELECT DISTINCT "{col_name}" FROM "{ten_thuong}" WHERE "{col_name}" IS NOT NULL')
                    ).fetchall()
                    for (val_str,) in vals:
                        if val_str:
                            safe_val = str(val_str).replace("'", "''")
                            try:
                                auto_conn.execute(
                                    text(f'ALTER TYPE "{udt_name}" ADD VALUE IF NOT EXISTS \'{safe_val}\'')
                                )
                            except Exception:
                                pass

        # 2. Đồng bộ dữ liệu sang các bảng viết HOA theo thứ tự khóa ngoại
        with pg_engine.begin() as conn:
            # Xóa dữ liệu cũ từ bảng con lên bảng cha trước khi nạp mới
            for _, ten_hoa, _ in reversed(DANH_SACH_BANG_DONG_BO):
                ton_tai = conn.execute(
                    text(
                        """
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = :thoa
                        """
                    ),
                    {"thoa": ten_hoa},
                ).fetchone()
                if ton_tai:
                    conn.execute(text(f'DELETE FROM public."{ten_hoa}"'))

            # Nạp dữ liệu từ bảng cha xuống bảng con
            for ten_thuong, ten_hoa, cot_pk in DANH_SACH_BANG_DONG_BO:
                cols_hoa = conn.execute(
                    text(
                        """
                        SELECT column_name, data_type, udt_name, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = :thoa
                        ORDER BY ordinal_position
                        """
                    ),
                    {"thoa": ten_hoa},
                ).fetchall()
                if not cols_hoa:
                    continue

                cols_thuong_rows = conn.execute(
                    text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = :tthuong
                        """
                    ),
                    {"tthuong": ten_thuong},
                ).fetchall()
                set_cols_thuong = {r[0] for r in cols_thuong_rows}

                common_cols = []
                select_exprs = []
                for col_name, data_type, udt_name, is_nullable, col_default in cols_hoa:
                    if col_name in set_cols_thuong:
                        common_cols.append(f'"{col_name}"')
                        if data_type == "USER-DEFINED":
                            select_exprs.append(f'"{col_name}"::text::"{udt_name}"')
                        elif data_type == "integer" and col_name == "nguoi_duyet":
                            select_exprs.append("1")
                        else:
                            select_exprs.append(f'"{col_name}"')

                if not common_cols:
                    continue

                cols_sql = ", ".join(common_cols)
                select_sql = ", ".join(select_exprs)
                conn.execute(
                    text(
                        f'INSERT INTO public."{ten_hoa}" ({cols_sql}) '
                        f'SELECT {select_sql} FROM public."{ten_thuong}"'
                    )
                )

                if cot_pk:
                    try:
                        conn.execute(
                            text(
                                f"""
                                SELECT setval(
                                    pg_get_serial_sequence('public."{ten_hoa}"', '{cot_pk}'),
                                    COALESCE((SELECT MAX("{cot_pk}") FROM public."{ten_hoa}"), 1),
                                    true
                                )
                                """
                            )
                        )
                    except Exception:
                        pass
    except Exception as e:
        print(f"[CSDL] Lưu ý khi đồng bộ bảng chữ HOA pgAdmin: {e}")
