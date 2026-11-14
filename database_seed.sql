-- =================================================================
-- DACN: COFFEE AI PROCUREMENT AGENT - POSTGRESQL INITIAL DATABASE
-- Do an Chuyen nganh - Khoa CNTT - Dai hoc HUTECH
-- File khoi tao Schema & Du lieu mau dung cho pgAdmin / Docker / PostgreSQL
-- =================================================================

-- Xoa bang cu neu da ton tai (chay lai tu dau an toan)
DROP TABLE IF EXISTS nhat_ky_xu_ly_du_lieu CASCADE;
DROP TABLE IF EXISTS tieu_hao_nguyen_lieu_ngay CASCADE;
DROP TABLE IF EXISTS lich_su_ban_hang CASCADE;
DROP TABLE IF EXISTS recipes_bom CASCADE;
DROP TABLE IF EXISTS menu_items CASCADE;
DROP TABLE IF EXISTS lich_su_duyet CASCADE;
DROP TABLE IF EXISTS don_mua_hang CASCADE;
DROP TABLE IF EXISTS ct_de_xuat_mua CASCADE;
DROP TABLE IF EXISTS phieu_de_xuat_mua CASCADE;
DROP TABLE IF EXISTS du_bao_nhu_cau CASCADE;
DROP TABLE IF EXISTS giao_dich_kho CASCADE;
DROP TABLE IF EXISTS lo_hang CASCADE;
DROP TABLE IF EXISTS cc_nguyen_lieu CASCADE;
DROP TABLE IF EXISTS nguyen_lieu CASCADE;
DROP TABLE IF EXISTS nha_cung_cap CASCADE;
DROP TABLE IF EXISTS nguoi_dung CASCADE;

-- 1. NGUOI_DUNG
CREATE TABLE nguoi_dung (
    ma_nguoi_dung SERIAL PRIMARY KEY,
    ten_nguoi_dung VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    mat_khau_hash VARCHAR(255) NOT NULL,
    vai_tro VARCHAR(30) DEFAULT 'QUAN_LY',
    trang_thai BOOLEAN DEFAULT TRUE,
    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 2. NHA_CUNG_CAP
CREATE TABLE nha_cung_cap (
    ma_nha_cung_cap SERIAL PRIMARY KEY,
    ten_nha_cung_cap VARCHAR(150) NOT NULL,
    nguoi_lien_he VARCHAR(100),
    email VARCHAR(100),
    sdt VARCHAR(20),
    dia_chi VARCHAR(255),
    thoi_gian_giao_du_kien INTEGER DEFAULT 2,
    diem_uy_tin FLOAT DEFAULT 4.5,
    diem_chat_luong FLOAT DEFAULT 4.5,
    trang_thai BOOLEAN DEFAULT TRUE,
    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 3. NGUYEN_LIEU
CREATE TABLE nguyen_lieu (
    ma_nguyen_lieu SERIAL PRIMARY KEY,
    ten_nguyen_lieu VARCHAR(100) NOT NULL,
    danh_muc VARCHAR(50),
    don_vi_tinh VARCHAR(20) NOT NULL,
    muc_ton_an_toan FLOAT NOT NULL DEFAULT 10.0,
    ton_kho_hien_tai FLOAT NOT NULL DEFAULT 0.0,
    muc_ton_toi_da FLOAT NOT NULL DEFAULT 100.0,
    trang_thai BOOLEAN DEFAULT TRUE,
    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ngay_cap_nhat TIMESTAMP
);
-- 4. CC_NGUYEN_LIEU
CREATE TABLE cc_nguyen_lieu (
    ma_nha_cung_cap INTEGER REFERENCES nha_cung_cap(ma_nha_cung_cap) ON DELETE CASCADE,
    ma_nguyen_lieu INTEGER REFERENCES nguyen_lieu(ma_nguyen_lieu) ON DELETE CASCADE,
    don_gia FLOAT NOT NULL,
    so_luong_dat_toi_thieu FLOAT DEFAULT 1.0,
    thoi_gian_giao_hang INTEGER DEFAULT 2,
    ngay_cap_nhat_gia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ma_nha_cung_cap, ma_nguyen_lieu)
);
-- 5. LO_HANG
CREATE TABLE lo_hang (
    ma_lo_hang SERIAL PRIMARY KEY,
    ma_nguyen_lieu INTEGER REFERENCES nguyen_lieu(ma_nguyen_lieu) ON DELETE CASCADE,
    ma_lo_nha_cung_cap VARCHAR(50),
    so_luong_nhap FLOAT NOT NULL,
    so_luong_con_lai FLOAT NOT NULL,
    ngay_nhap_kho TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    han_su_dung DATE,
    don_gia_nhap FLOAT NOT NULL
);
-- 6. GIAO_DICH_KHO
CREATE TABLE giao_dich_kho (
    ma_giao_dich SERIAL PRIMARY KEY,
    ma_nguyen_lieu INTEGER REFERENCES nguyen_lieu(ma_nguyen_lieu) ON DELETE CASCADE,
    loai_giao_dich VARCHAR(20) NOT NULL,
    so_luong FLOAT NOT NULL,
    ngay_giao_dich TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ma_tham_chieu VARCHAR(50),
    ghi_chu VARCHAR(255)
);
-- 7. DU_BAO_NHU_CAU
CREATE TABLE du_bao_nhu_cau (
    ma_du_bao SERIAL PRIMARY KEY,
    ma_nguyen_lieu INTEGER REFERENCES nguyen_lieu(ma_nguyen_lieu) ON DELETE CASCADE,
    ngay_du_bao DATE NOT NULL,
    so_luong_du_bao FLOAT NOT NULL,
    do_tin_cay FLOAT DEFAULT 0.95,
    phuong_phap VARCHAR(50) DEFAULT 'Prophet_v1',
    thoi_gian_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 8. PHIEU_DE_XUAT_MUA
CREATE TABLE phieu_de_xuat_mua (
    ma_phieu_de_xuat SERIAL PRIMARY KEY,
    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tong_tien_du_kien FLOAT DEFAULT 0.0,
    trang_thai VARCHAR(30) DEFAULT 'CHO_DUYET',
    ly_do_tong_quan TEXT,
    nguoi_tao VARCHAR(50) DEFAULT 'AI Procurement Agent'
);
-- 9. CT_DE_XUAT_MUA
CREATE TABLE ct_de_xuat_mua (
    ma_chi_tiet SERIAL PRIMARY KEY,
    ma_phieu_de_xuat INTEGER REFERENCES phieu_de_xuat_mua(ma_phieu_de_xuat) ON DELETE CASCADE,
    ma_nguyen_lieu INTEGER REFERENCES nguyen_lieu(ma_nguyen_lieu),
    ma_nha_cung_cap INTEGER REFERENCES nha_cung_cap(ma_nha_cung_cap),
    so_luong_de_xuat FLOAT NOT NULL,
    don_gia_du_kien FLOAT NOT NULL,
    so_luong_du_doan_7ngay FLOAT DEFAULT 0.0,
    ly_do_de_xuat TEXT
);
-- 10. LICH_SU_DUYET
CREATE TABLE lich_su_duyet (
    ma_lich_su SERIAL PRIMARY KEY,
    ma_phieu_de_xuat INTEGER REFERENCES phieu_de_xuat_mua(ma_phieu_de_xuat) ON DELETE CASCADE,
    nguoi_duyet VARCHAR(100) NOT NULL,
    hanh_dong VARCHAR(20) NOT NULL,
    y_kien TEXT,
    thoi_gian_duyet TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- 11. MENU_ITEMS & RECIPES_BOM
CREATE TABLE menu_items (
    ma_mon SERIAL PRIMARY KEY,
    ten_mon VARCHAR(100) NOT NULL,
    danh_muc VARCHAR(50),
    don_gia_ban FLOAT NOT NULL,
    trang_thai BOOLEAN DEFAULT TRUE
);
CREATE TABLE recipes_bom (
    ma_dinh_muc SERIAL PRIMARY KEY,
    ma_mon INTEGER REFERENCES menu_items(ma_mon) ON DELETE CASCADE,
    ma_nguyen_lieu INTEGER REFERENCES nguyen_lieu(ma_nguyen_lieu) ON DELETE CASCADE,
    so_luong_tieu_hao FLOAT NOT NULL,
    ghi_chu VARCHAR(100)
);
-- 12. LICH_SU_BAN_HANG, TIEU_HAO_NGUYEN_LIEU_NGAY & NHAT_KY_ETL_PIPELINE (Tuan 5 - Data/AI Engineer)
CREATE TABLE lich_su_ban_hang (
    ma_ban_hang SERIAL PRIMARY KEY,
    ma_hoa_don_pos VARCHAR(50) NOT NULL,
    ngay_ban DATE NOT NULL,
    ca_ban VARCHAR(20) DEFAULT 'SANG',
    ma_mon INTEGER REFERENCES menu_items(ma_mon) ON DELETE CASCADE,
    so_luong_ly FLOAT NOT NULL,
    don_gia_ban FLOAT NOT NULL,
    thanh_tien FLOAT NOT NULL,
    da_boc_tach_bom BOOLEAN DEFAULT TRUE,
    thoi_gian_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE tieu_hao_nguyen_lieu_ngay (
    id SERIAL PRIMARY KEY,
    ngay DATE NOT NULL,
    ma_nguyen_lieu INTEGER REFERENCES nguyen_lieu(ma_nguyen_lieu) ON DELETE CASCADE,
    so_luong_tieu_hao FLOAT NOT NULL,
    so_ly_lien_quan INTEGER DEFAULT 0,
    thu_trong_tuan INTEGER NOT NULL,
    la_cuoi_tuan BOOLEAN DEFAULT FALSE,
    he_so_mua_vu FLOAT DEFAULT 1.0,
    lag_1_ngay FLOAT,
    lag_7_ngay FLOAT,
    rolling_mean_7d FLOAT,
    rolling_std_7d FLOAT,
    thoi_gian_cap_nhat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE nhat_ky_etl_pipeline (
    ma_lan_chay SERIAL PRIMARY KEY,
    ten_pipeline VARCHAR(100) DEFAULT 'BOM_DECONSTRUCTION_ETL_V1',
    thoi_gian_chay TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tong_dong_raw INTEGER DEFAULT 0,
    so_dong_trung_lap INTEGER DEFAULT 0,
    so_dong_thieu_du_lieu INTEGER DEFAULT 0,
    so_dong_am_hoac_loi INTEGER DEFAULT 0,
    so_dong_ngoai_lai_da_xu_ly INTEGER DEFAULT 0,
    tong_dong_sach INTEGER DEFAULT 0,
    ty_le_du_lieu_sach FLOAT DEFAULT 100.0,
    so_ngay_xu_ly INTEGER DEFAULT 365,
    tong_ban_ghi_tieu_hao_sinh_ra INTEGER DEFAULT 0,
    trang_thai VARCHAR(30) DEFAULT 'SUCCESS',
    ghi_chu VARCHAR(500)
);

-- Du lieu cho bang: nguoi_dung (3 dong)
INSERT INTO nguoi_dung (ma_nguoi_dung, ten_nguoi_dung, email, mat_khau_hash, vai_tro, trang_thai, ngay_tao) VALUES (1, 'Nguyễn Văn Quản Lý', 'quanly@coffee.vn', '$2b$12$I2Q.O.dvOS9YHSD.vDNqNeaz1h2sKaD5RSgXyYGFqtT8yXykm7o/W', 'QUAN_LY', 1, '2026-11-08 04:37:55');
INSERT INTO nguoi_dung (ma_nguoi_dung, ten_nguoi_dung, email, mat_khau_hash, vai_tro, trang_thai, ngay_tao) VALUES (2, 'Trần Thị Thủ Kho', 'kho@coffee.vn', '$2b$12$gg9GMMbmS2E2D4LyRAdA/.LuR7dcqmLL/1LpUB8cK6kqa4VLBu2.y', 'NHAN_VIEN_KHO', 1, '2026-11-08 04:37:55');
INSERT INTO nguoi_dung (ma_nguoi_dung, ten_nguoi_dung, email, mat_khau_hash, vai_tro, trang_thai, ngay_tao) VALUES (3, 'Quản Trị Viên Hệ Thống', 'admin@coffee.vn', '$2b$12$e9I6hSfcGS4HMzokLG7rxuLCKnZPnjv81qUSl9btQW0.ecne24VAi', 'ADMIN', 1, '2026-11-08 04:37:55');

-- Du lieu cho bang: nha_cung_cap (5 dong)
INSERT INTO nha_cung_cap (ma_nha_cung_cap, ten_nha_cung_cap, nguoi_lien_he, email, sdt, dia_chi, thoi_gian_giao_du_kien, diem_uy_tin, diem_chat_luong, trang_thai, ngay_tao) VALUES (1, 'Công ty Cà phê Nguyên Chất Đắk Lắk', 'Lê Hoàng Long', 'daklakcoffee@supply.vn', '0903123456', 'Km 12, Quốc lộ 14, TP. Buôn Ma Thuột, Đắk Lắk', 2, 4.8, 4.9, 1, '2026-11-08 04:37:55');
INSERT INTO nha_cung_cap (ma_nha_cung_cap, ten_nha_cung_cap, nguoi_lien_he, email, sdt, dia_chi, thoi_gian_giao_du_kien, diem_uy_tin, diem_chat_luong, trang_thai, ngay_tao) VALUES (2, 'Đại lý Phân phối Sữa Horeca Sài Gòn', 'Phạm Minh Tuấn', 'horecasg@dairy.vn', '0918765432', 'Số 45 Đường số 7, KDC Trung Sơn, Bình Chánh, TP.HCM', 1, 4.7, 4.8, 1, '2026-11-08 04:37:55');
INSERT INTO nha_cung_cap (ma_nha_cung_cap, ten_nha_cung_cap, nguoi_lien_he, email, sdt, dia_chi, thoi_gian_giao_du_kien, diem_uy_tin, diem_chat_luong, trang_thai, ngay_tao) VALUES (3, 'Công ty Nguyên Liệu Pha Chế Vinbar', 'Vũ Thị Mai', 'contact@vinbar.vn', '0933889900', '758/28/18 Xô Viết Nghệ Tĩnh, P.25, Bình Thạnh, TP.HCM', 2, 4.6, 4.7, 1, '2026-11-08 04:37:55');
INSERT INTO nha_cung_cap (ma_nha_cung_cap, ten_nha_cung_cap, nguoi_lien_he, email, sdt, dia_chi, thoi_gian_giao_du_kien, diem_uy_tin, diem_chat_luong, trang_thai, ngay_tao) VALUES (4, 'Tổng kho Bao bì Thực phẩm Tân Bình', 'Đặng Quốc Dũng', 'baobitanbinh@pack.vn', '0988112233', '120 Tân Hải, Phường 13, Tân Bình, TP.HCM', 3, 4.5, 4.4, 1, '2026-11-08 04:37:55');
INSERT INTO nha_cung_cap (ma_nha_cung_cap, ten_nha_cung_cap, nguoi_lien_he, email, sdt, dia_chi, thoi_gian_giao_du_kien, diem_uy_tin, diem_chat_luong, trang_thai, ngay_tao) VALUES (5, 'Công ty Trà Việt TeaMaster Bảo Lộc', 'Nguyễn Bích Loan', 'teamaster@baoloc.vn', '0908556677', '88 Trần Phú, TP. Bảo Lộc, Lâm Đồng', 2, 4.9, 4.8, 1, '2026-11-08 04:37:55');

-- Du lieu cho bang: nguyen_lieu (15 dong)
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (1, 'Hạt cà phê Robusta Buôn Ma Thuột', 'Cà phê', 'kg', 15.0, 12.5, 80.0, 1, '2026-11-08 04:37:55', '2026-11-08 04:43:07');
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (2, 'Hạt cà phê Arabica Cầu Đất', 'Cà phê', 'kg', 10.0, 8.5, 50.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (3, 'Sữa tươi tiệt trùng Barista 1L', 'Sữa & Kem', 'hộp', 25.0, 18.0, 120.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (4, 'Sữa đặc Phương Nam 1.284kg', 'Sữa & Kem', 'lon', 20.0, 45.0, 150.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (5, 'Sữa tươi thanh trùng Đà Lạt Milk 950ml', 'Sữa & Kem', 'chai', 12.0, 24.0, 60.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (6, 'Siro Đào Monin 700ml', 'Siro & Xốt', 'chai', 5.0, 12.0, 30.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (7, 'Siro Dâu Torani 750ml', 'Siro & Xốt', 'chai', 4.0, 10.0, 25.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (8, 'Xốt Socola Hershey 1.36kg', 'Siro & Xốt', 'chai', 4.0, 9.0, 25.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (9, 'Bột Cacao Nguyên Chất Đắk Lắk', 'Bột & Topping', 'kg', 8.0, 95.0, 60.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (10, 'Bột Matcha Uji Nhật Bản', 'Bột & Topping', 'kg', 3.0, 6.5, 20.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (11, 'Bột Frappe Base tạo sánh', 'Bột & Topping', 'kg', 5.0, 14.0, 40.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (12, 'Trà Đen Phúc Long Đặc Biệt', 'Trà', 'kg', 8.0, 22.0, 60.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (13, 'Trà Ô Long Kim Tuyên Bảo Lộc', 'Trà', 'kg', 6.0, 16.0, 50.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (14, 'Ly nhựa PET Takeaway 500ml', 'Bao bì', 'cái', 500.0, 1800.0, 5000.0, 1, '2026-11-08 04:37:55', NULL);
INSERT INTO nguyen_lieu (ma_nguyen_lieu, ten_nguyen_lieu, danh_muc, don_vi_tinh, muc_ton_an_toan, ton_kho_hien_tai, muc_ton_toi_da, trang_thai, ngay_tao, ngay_cap_nhat) VALUES (15, 'Ống hút giấy sinh học bọc màng', 'Bao bì', 'cái', 600.0, 2200.0, 6000.0, 1, '2026-11-08 04:37:55', NULL);

-- Du lieu cho bang: cc_nguyen_lieu (19 dong)
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (1, 1, 145000.0, 10.0, 2, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (3, 1, 155000.0, 5.0, 1, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (1, 2, 260000.0, 5.0, 2, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (3, 2, 280000.0, 2.0, 1, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (2, 3, 33000.0, 12.0, 1, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (3, 3, 35500.0, 6.0, 2, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (2, 4, 68000.0, 6.0, 1, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (2, 5, 38000.0, 6.0, 1, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (3, 6, 215000.0, 2.0, 2, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (3, 7, 195000.0, 2.0, 2, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (3, 8, 185000.0, 2.0, 2, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (1, 9, 160000.0, 5.0, 2, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (3, 9, 175000.0, 2.0, 1, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (3, 10, 650000.0, 1.0, 2, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (3, 11, 110000.0, 2.0, 2, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (5, 12, 135000.0, 5.0, 2, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (5, 13, 220000.0, 3.0, 2, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (4, 14, 550.0, 500.0, 3, '2026-11-08 04:37:55');
INSERT INTO cc_nguyen_lieu (ma_nha_cung_cap, ma_nguyen_lieu, don_gia, so_luong_dat_toi_thieu, thoi_gian_giao_hang, ngay_cap_nhat_gia) VALUES (4, 15, 180.0, 1000.0, 3, '2026-11-08 04:37:55');

-- Du lieu cho bang: lo_hang (6 dong)
INSERT INTO lo_hang (ma_lo_hang, ma_nguyen_lieu, ma_lo_nha_cung_cap, so_luong_nhap, so_luong_con_lai, ngay_nhap_kho, han_su_dung, don_gia_nhap) VALUES (1, 1, 'DKL-ROB-20261015', 30.0, 12.0, '2026-10-19 11:37:53.993145', '2027-04-17', 145000.0);
INSERT INTO lo_hang (ma_lo_hang, ma_nguyen_lieu, ma_lo_nha_cung_cap, so_luong_nhap, so_luong_con_lai, ngay_nhap_kho, han_su_dung, don_gia_nhap) VALUES (2, 2, 'DKL-ARA-20261018', 20.0, 8.5, '2026-10-21 11:37:53.993145', '2027-04-07', 260000.0);
INSERT INTO lo_hang (ma_lo_hang, ma_nguyen_lieu, ma_lo_nha_cung_cap, so_luong_nhap, so_luong_con_lai, ngay_nhap_kho, han_su_dung, don_gia_nhap) VALUES (3, 3, 'MILK-BAR-20261028', 48.0, 18.0, '2026-10-29 11:37:53.993145', '2026-12-28', 33000.0);
INSERT INTO lo_hang (ma_lo_hang, ma_nguyen_lieu, ma_lo_nha_cung_cap, so_luong_nhap, so_luong_con_lai, ngay_nhap_kho, han_su_dung, don_gia_nhap) VALUES (4, 5, 'DLM-EXP-NEAR', 12.0, 6.0, '2026-10-31 11:37:53.993145', '2026-11-11', 38000.0);
INSERT INTO lo_hang (ma_lo_hang, ma_nguyen_lieu, ma_lo_nha_cung_cap, so_luong_nhap, so_luong_con_lai, ngay_nhap_kho, han_su_dung, don_gia_nhap) VALUES (5, 5, 'DLM-FRESH', 18.0, 18.0, '2026-11-07 11:37:53.993145', '2026-11-18', 38000.0);
INSERT INTO lo_hang (ma_lo_hang, ma_nguyen_lieu, ma_lo_nha_cung_cap, so_luong_nhap, so_luong_con_lai, ngay_nhap_kho, han_su_dung, don_gia_nhap) VALUES (6, 9, 'CC-OVERSTOCK-LOT', 100.0, 95.0, '2026-10-24 11:37:53.993145', '2027-07-06', 160000.0);

-- Du lieu cho bang: giao_dich_kho (28 dong)
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (1, 1, 'XUAT_BAN', 150.0, '2025-12-08 11:37:53.993145', 'POS-SUM-M1', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (2, 3, 'XUAT_BAN', 200.0, '2025-12-08 11:37:53.993145', 'POS-MILK-M1', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (3, 1, 'XUAT_BAN', 135.0, '2026-01-07 11:37:53.993145', 'POS-SUM-M2', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (4, 3, 'XUAT_BAN', 180.0, '2026-01-07 11:37:53.993145', 'POS-MILK-M2', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (5, 1, 'XUAT_BAN', 120.0, '2026-02-06 11:37:53.993145', 'POS-SUM-M3', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (6, 3, 'XUAT_BAN', 200.0, '2026-02-06 11:37:53.993145', 'POS-MILK-M3', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (7, 1, 'XUAT_BAN', 150.0, '2026-03-08 11:37:53.993145', 'POS-SUM-M4', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (8, 3, 'XUAT_BAN', 180.0, '2026-03-08 11:37:53.993145', 'POS-MILK-M4', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (9, 1, 'XUAT_BAN', 135.0, '2026-04-07 11:37:53.993145', 'POS-SUM-M5', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (10, 3, 'XUAT_BAN', 200.0, '2026-04-07 11:37:53.993145', 'POS-MILK-M5', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (11, 1, 'XUAT_BAN', 120.0, '2026-05-07 11:37:53.993145', 'POS-SUM-M6', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (12, 3, 'XUAT_BAN', 180.0, '2026-05-07 11:37:53.993145', 'POS-MILK-M6', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (13, 1, 'XUAT_BAN', 150.0, '2026-06-06 11:37:53.993145', 'POS-SUM-M7', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (14, 3, 'XUAT_BAN', 200.0, '2026-06-06 11:37:53.993145', 'POS-MILK-M7', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (15, 1, 'XUAT_BAN', 135.0, '2026-07-06 11:37:53.993145', 'POS-SUM-M8', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (16, 3, 'XUAT_BAN', 180.0, '2026-07-06 11:37:53.993145', 'POS-MILK-M8', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (17, 1, 'XUAT_BAN', 120.0, '2026-08-05 11:37:53.993145', 'POS-SUM-M9', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (18, 3, 'XUAT_BAN', 200.0, '2026-08-05 11:37:53.993145', 'POS-MILK-M9', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (19, 1, 'XUAT_BAN', 150.0, '2026-09-04 11:37:53.993145', 'POS-SUM-M10', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (20, 3, 'XUAT_BAN', 180.0, '2026-09-04 11:37:53.993145', 'POS-MILK-M10', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (21, 1, 'XUAT_BAN', 135.0, '2026-10-04 11:37:53.993145', 'POS-SUM-M11', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (22, 3, 'XUAT_BAN', 200.0, '2026-10-04 11:37:53.993145', 'POS-MILK-M11', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (23, 1, 'XUAT_BAN', 120.0, '2026-11-03 11:37:53.993145', 'POS-SUM-M12', 'Tiêu hao bóc tách công thức qua đơn bán POS');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (24, 3, 'XUAT_BAN', 180.0, '2026-11-03 11:37:53.993145', 'POS-MILK-M12', 'Tiêu hao pha chế Latte, Cappuccino');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (25, 1, 'NHAP', 30.0, '2026-10-19 11:37:53.993145', 'PNK-20261015-01', 'Nhập kho theo đơn đặt hàng NCC Đắk Lắk');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (26, 5, 'HAO_HUT', 1.0, '2026-11-06 11:37:53.993145', 'HH-20261106', 'Rơi vỡ trong ca làm việc buổi sáng');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (27, 1, 'KIEM_KE', 12.5, '2026-11-08 04:43:07', 'TEST-KK-01', 'Kiem ke cuoi ngay tu dong test');
INSERT INTO giao_dich_kho (ma_giao_dich, ma_nguyen_lieu, loai_giao_dich, so_luong, ngay_giao_dich, ma_tham_chieu, ghi_chu) VALUES (28, 1, 'KIEM_KE', 12.5, '2026-11-08 04:47:58', 'TEST-KK-01', 'Kiem ke cuoi ngay tu dong test');

-- Du lieu cho bang: du_bao_nhu_cau (35 dong)
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (1, 1, '2026-11-09', 4.2, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (2, 2, '2026-11-09', 2.6, 0.94, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (3, 3, '2026-11-09', 7.5, 0.96, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (4, 4, '2026-11-09', 4.0, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (5, 14, '2026-11-09', 180.0, 0.92, 'XGBoost_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (6, 1, '2026-11-10', 4.41, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (7, 2, '2026-11-10', 2.73, 0.94, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (8, 3, '2026-11-10', 7.88, 0.96, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (9, 4, '2026-11-10', 4.2, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (10, 14, '2026-11-10', 189.0, 0.92, 'XGBoost_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (11, 1, '2026-11-11', 4.62, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (12, 2, '2026-11-11', 2.86, 0.94, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (13, 3, '2026-11-11', 8.25, 0.96, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (14, 4, '2026-11-11', 4.4, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (15, 14, '2026-11-11', 198.0, 0.92, 'XGBoost_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (16, 1, '2026-11-12', 4.83, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (17, 2, '2026-11-12', 2.99, 0.94, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (18, 3, '2026-11-12', 8.62, 0.96, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (19, 4, '2026-11-12', 4.6, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (20, 14, '2026-11-12', 207.0, 0.92, 'XGBoost_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (21, 1, '2026-11-13', 5.88, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (22, 2, '2026-11-13', 3.64, 0.94, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (23, 3, '2026-11-13', 10.5, 0.96, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (24, 4, '2026-11-13', 5.6, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (25, 14, '2026-11-13', 252.0, 0.92, 'XGBoost_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (26, 1, '2026-11-14', 6.3, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (27, 2, '2026-11-14', 3.9, 0.94, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (28, 3, '2026-11-14', 11.25, 0.96, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (29, 4, '2026-11-14', 6.0, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (30, 14, '2026-11-14', 270.0, 0.92, 'XGBoost_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (31, 1, '2026-11-15', 5.04, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (32, 2, '2026-11-15', 3.12, 0.94, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (33, 3, '2026-11-15', 9.0, 0.96, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (34, 4, '2026-11-15', 4.8, 0.95, 'Prophet_v1', '2026-11-08 04:37:55');
INSERT INTO du_bao_nhu_cau (ma_du_bao, ma_nguyen_lieu, ngay_du_bao, so_luong_du_bao, do_tin_cay, phuong_phap, thoi_gian_tao) VALUES (35, 14, '2026-11-15', 216.0, 0.92, 'XGBoost_v1', '2026-11-08 04:37:55');

-- Du lieu cho bang: phieu_de_xuat_mua (2 dong)
INSERT INTO phieu_de_xuat_mua (ma_phieu_de_xuat, ngay_tao, tong_tien_du_kien, trang_thai, ly_do_tong_quan, nguoi_tao) VALUES (1, '2026-11-08 08:37:53.993145', 12850000.0, 'DA_DUYET', 'AI Agent phát hiện 3 nguyên liệu chạm ngưỡng cảnh báo tồn kho (Tồn <= ROP) dựa trên dự báo tiêu thụ 7 ngày tới. Đề xuất đặt hàng sớm để tránh đứt gãy pha chế vào cao điểm cuối tuần.', 'AI Procurement Agent (Gemini Pro)');
INSERT INTO phieu_de_xuat_mua (ma_phieu_de_xuat, ngay_tao, tong_tien_du_kien, trang_thai, ly_do_tong_quan, nguoi_tao) VALUES (2, '2026-11-01 11:37:53.993145', 3850000.0, 'DA_DUYET', 'Bổ sung định kỳ tuần trước cho các dòng siro và bao bì.', 'AI Procurement Agent');

-- Du lieu cho bang: ct_de_xuat_mua (5 dong)
INSERT INTO ct_de_xuat_mua (ma_chi_tiet, ma_phieu_de_xuat, ma_nguyen_lieu, ma_nha_cung_cap, so_luong_de_xuat, don_gia_du_kien, so_luong_du_doan_7ngay, ly_do_de_xuat) VALUES (1, 1, 1, 1, 40.0, 145000.0, 34.8, 'Tồn kho còn 12kg ≤ ROP 23.4kg. Chọn NCC Cà phê Đắk Lắk vì đạt điểm MCDM cao nhất (92.4/100), đơn giá thấp hơn 10.000đ/kg và chất lượng 4.9 sao.');
INSERT INTO ct_de_xuat_mua (ma_chi_tiet, ma_phieu_de_xuat, ma_nguyen_lieu, ma_nha_cung_cap, so_luong_de_xuat, don_gia_du_kien, so_luong_du_doan_7ngay, ly_do_de_xuat) VALUES (2, 1, 2, 1, 20.0, 260000.0, 21.5, 'Tồn kho còn 8.5kg ≤ ROP 15.2kg. Chọn NCC Cà phê Đắk Lắk kết hợp chuyến xe giao cùng hạt Robusta để tối ưu chi phí vận chuyển.');
INSERT INTO ct_de_xuat_mua (ma_chi_tiet, ma_phieu_de_xuat, ma_nguyen_lieu, ma_nha_cung_cap, so_luong_de_xuat, don_gia_du_kien, so_luong_du_doan_7ngay, ly_do_de_xuat) VALUES (3, 1, 3, 2, 60.0, 33000.0, 62.0, 'Tồn kho còn 18 hộp ≤ ROP 32.5 hộp. Đại lý Sữa Horeca Sài Gòn có Lead Time chỉ 1 ngày, giá tốt nhất 33.000đ/hộp.');
INSERT INTO ct_de_xuat_mua (ma_chi_tiet, ma_phieu_de_xuat, ma_nguyen_lieu, ma_nha_cung_cap, so_luong_de_xuat, don_gia_du_kien, so_luong_du_doan_7ngay, ly_do_de_xuat) VALUES (4, 2, 14, 4, 2000.0, 550.0, 1200.0, 'Đạt MOQ 500 cái của Tổng kho Bao bì Tân Bình.');
INSERT INTO ct_de_xuat_mua (ma_chi_tiet, ma_phieu_de_xuat, ma_nguyen_lieu, ma_nha_cung_cap, so_luong_de_xuat, don_gia_du_kien, so_luong_du_doan_7ngay, ly_do_de_xuat) VALUES (5, 2, 15, 4, 3000.0, 180.0, 1400.0, 'Bổ sung ống hút giấy thân thiện môi trường.');

-- Du lieu cho bang: lich_su_duyet (3 dong)
INSERT INTO lich_su_duyet (ma_lich_su, ma_phieu_de_xuat, nguoi_duyet, hanh_dong, y_kien, thoi_gian_duyet) VALUES (1, 2, 'Nguyễn Văn Quản Lý', 'APPROVE', 'Đã kiểm tra kho thực tế, số lượng bao bì phù hợp với công suất bán dự kiến.', '2026-11-01 15:37:53.993145');
INSERT INTO lich_su_duyet (ma_lich_su, ma_phieu_de_xuat, nguoi_duyet, hanh_dong, y_kien, thoi_gian_duyet) VALUES (2, 1, 'Nguyen Van Quan Ly', 'APPROVE', 'Duyet don hang de kip chuan bi cho cuoi tuan.', '2026-11-08 11:43:07.320563');
INSERT INTO lich_su_duyet (ma_lich_su, ma_phieu_de_xuat, nguoi_duyet, hanh_dong, y_kien, thoi_gian_duyet) VALUES (3, 1, 'Nguyen Van Quan Ly', 'APPROVE', 'Duyet don hang de kip chuan bi cho cuoi tuan.', '2026-11-08 11:47:58.089248');

-- Du lieu cho bang: menu_items (12 dong)
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (1, 'Cà phê Đen Đá Buôn Ma Thuột', 'Cà phê truyền thống', 29000.0, TRUE);
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (2, 'Cà phê Sữa Đá Sài Gòn', 'Cà phê truyền thống', 35000.0, TRUE);
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (3, 'Bạc Xỉu Đá Đà Lạt', 'Cà phê truyền thống', 39000.0, TRUE);
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (4, 'Cà phê Sữa Tươi Pha Máy', 'Cà phê máy', 49000.0, TRUE);
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (5, 'Cà phê Bọt Sữa Ý Cầu Đất', 'Cà phê máy', 49000.0, TRUE);
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (6, 'Cà phê Socola Đá Xay', 'Đá xay', 55000.0, TRUE);
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (7, 'Trà Đào Cam Sả Đặc Biệt', 'Trà trái cây', 45000.0, TRUE);
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (8, 'Trà Dâu Tằm Pha Lê Tuyết', 'Trà trái cây', 45000.0, TRUE);
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (9, 'Trà Sữa Ô Long Bảo Lộc', 'Trà sữa', 45000.0, TRUE);
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (10, 'Trà Xanh Sữa Nhật Bản', 'Trà xanh', 52000.0, TRUE);
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (11, 'Trà Xanh Đá Xay Kem Tuyết', 'Đá xay', 59000.0, TRUE);
INSERT INTO menu_items (ma_mon, ten_mon, danh_muc, don_gia_ban, trang_thai) VALUES (12, 'Cacao Socola Đắk Lắk Đá', 'Socola & Cacao', 45000.0, TRUE);

-- Du lieu cho bang: recipes_bom (56 dong - phu 100% ca 15 nguyen lieu)
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (1, 1, 1, 0.025, '25g hạt Robusta');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (2, 1, 14, 1.0, '1 ly nhựa PET 500ml');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (3, 1, 15, 1.0, '1 ống hút giấy');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (4, 2, 1, 0.022, '22g hạt Robusta');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (5, 2, 4, 0.03, '0.03 lon sữa đặc (~38g)');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (6, 2, 14, 1.0, '1 ly nhựa PET 500ml');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (7, 2, 15, 1.0, '1 ống hút giấy');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (8, 3, 1, 0.015, '15g hạt Robusta');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (9, 3, 4, 0.035, '0.035 lon sữa đặc');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (10, 3, 5, 0.08, '80ml sữa thanh trùng Đà Lạt');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (11, 3, 14, 1.0, '1 ly nhựa PET 500ml');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (12, 3, 15, 1.0, '1 ống hút giấy');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (13, 4, 2, 0.02, '20g hạt Arabica Cầu Đất');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (14, 4, 3, 0.18, '180ml sữa tươi pha chế');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (15, 4, 14, 1.0, '1 ly tiêu chuẩn');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (16, 4, 15, 1.0, '1 ống hút giấy');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (17, 5, 2, 0.018, '18g hạt Arabica Cầu Đất');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (18, 5, 3, 0.15, '150ml sữa tươi tạo bọt');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (19, 5, 9, 0.003, '3g bột cacao rắc mặt');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (20, 5, 14, 1.0, '1 ly tiêu chuẩn');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (21, 5, 15, 1.0, '1 ống hút giấy');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (22, 6, 2, 0.018, '18g hạt Arabica');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (23, 6, 3, 0.1, '100ml sữa tươi');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (24, 6, 8, 0.025, '0.025 chai xốt Socola');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (25, 6, 11, 0.02, '20g bột nền đá xay');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (26, 6, 14, 1.0, '1 ly nhựa PET 500ml');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (27, 6, 15, 1.0, '1 ống hút giấy');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (28, 7, 12, 0.015, '15g cốt trà đen Phúc Long');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (29, 7, 6, 0.04, '0.04 chai siro Đào (~28ml)');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (30, 7, 14, 1.0, '1 ly nhựa PET 500ml');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (31, 7, 15, 1.0, '1 ống hút giấy');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (32, 8, 13, 0.015, '15g cốt trà Ô Long');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (33, 8, 7, 0.04, '0.04 chai siro Dâu (~30ml)');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (34, 8, 14, 1.0, '1 ly nhựa PET 500ml');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (35, 8, 15, 1.0, '1 ống hút giấy');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (36, 9, 13, 0.018, '18g trà Ô Long Kim Tuyên');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (37, 9, 4, 0.025, '0.025 lon sữa đặc');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (38, 9, 5, 0.07, '70ml sữa thanh trùng');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (39, 9, 14, 1.0, '1 ly nhựa PET 500ml');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (40, 9, 15, 1.0, '1 ống hút giấy');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (41, 10, 10, 0.012, '12g bột trà xanh Nhật Bản');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (42, 10, 3, 0.16, '160ml sữa tươi pha chế');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (43, 10, 4, 0.015, '0.015 lon sữa đặc');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (44, 10, 14, 1.0, '1 ly nhựa PET 500ml');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (45, 10, 15, 1.0, '1 ống hút giấy');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (46, 11, 10, 0.015, '15g bột trà xanh Nhật Bản');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (47, 11, 5, 0.1, '100ml sữa thanh trùng');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (48, 11, 11, 0.025, '25g bột nền đá xay');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (49, 11, 14, 1.0, '1 ly nhựa PET 500ml');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (50, 11, 15, 1.0, '1 ống hút giấy');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (51, 12, 9, 0.025, '25g bột Cacao nguyên chất');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (52, 12, 8, 0.02, '0.02 chai xốt Socola');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (53, 12, 4, 0.025, '0.025 lon sữa đặc');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (54, 12, 3, 0.1, '100ml sữa tươi');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (55, 12, 14, 1.0, '1 ly nhựa PET 500ml');
INSERT INTO recipes_bom (ma_dinh_muc, ma_mon, ma_nguyen_lieu, so_luong_tieu_hao, ghi_chu) VALUES (56, 12, 15, 1.0, '1 ống hút giấy');

-- Du lieu cho bang: nhat_ky_xu_ly_du_lieu (1 dong)
INSERT INTO nhat_ky_xu_ly_du_lieu (ma_lan_chay, ten_quy_trinh, tong_dong_tho, so_dong_trung_lap, so_dong_thieu_du_lieu, so_dong_am_hoac_loi, so_dong_ngoai_lai_da_xu_ly, tong_dong_sach, ty_le_du_lieu_sach, so_ngay_xu_ly, tong_ban_ghi_tieu_hao_sinh_ra, trang_thai, ghi_chu) VALUES (1, 'QUY_TRINH_BOC_TACH_DINH_MUC_V1', 4413, 16, 10, 7, 9, 4385, 99.37, 365, 5475, 'THANH_CONG', 'Đã làm sạch 4385/4413 bản ghi bán hàng POS (99.37%), xử lý 9 ngoại lai IQR và bóc tách 12 món thành 5475 điểm dữ liệu chuỗi thời gian của 15 nguyên liệu.');

-- Cap nhat Sequence ID PostgreSQL sau khi chen ID co dinh
SELECT setval(pg_get_serial_sequence('nguoi_dung', 'ma_nguoi_dung'), COALESCE(MAX(ma_nguoi_dung), 1)) FROM nguoi_dung;
SELECT setval(pg_get_serial_sequence('nha_cung_cap', 'ma_nha_cung_cap'), COALESCE(MAX(ma_nha_cung_cap), 1)) FROM nha_cung_cap;
SELECT setval(pg_get_serial_sequence('nguyen_lieu', 'ma_nguyen_lieu'), COALESCE(MAX(ma_nguyen_lieu), 1)) FROM nguyen_lieu;
SELECT setval(pg_get_serial_sequence('lo_hang', 'ma_lo_hang'), COALESCE(MAX(ma_lo_hang), 1)) FROM lo_hang;
SELECT setval(pg_get_serial_sequence('giao_dich_kho', 'ma_giao_dich'), COALESCE(MAX(ma_giao_dich), 1)) FROM giao_dich_kho;
SELECT setval(pg_get_serial_sequence('du_bao_nhu_cau', 'ma_du_bao'), COALESCE(MAX(ma_du_bao), 1)) FROM du_bao_nhu_cau;
SELECT setval(pg_get_serial_sequence('phieu_de_xuat_mua', 'ma_phieu_de_xuat'), COALESCE(MAX(ma_phieu_de_xuat), 1)) FROM phieu_de_xuat_mua;
SELECT setval(pg_get_serial_sequence('ct_de_xuat_mua', 'ma_chi_tiet'), COALESCE(MAX(ma_chi_tiet), 1)) FROM ct_de_xuat_mua;
SELECT setval(pg_get_serial_sequence('lich_su_duyet', 'ma_lich_su'), COALESCE(MAX(ma_lich_su), 1)) FROM lich_su_duyet;
SELECT setval(pg_get_serial_sequence('menu_items', 'ma_mon'), COALESCE(MAX(ma_mon), 1)) FROM menu_items;
SELECT setval(pg_get_serial_sequence('recipes_bom', 'ma_dinh_muc'), COALESCE(MAX(ma_dinh_muc), 1)) FROM recipes_bom;
SELECT setval(pg_get_serial_sequence('nhat_ky_xu_ly_du_lieu', 'ma_lan_chay'), COALESCE(MAX(ma_lan_chay), 1)) FROM nhat_ky_xu_ly_du_lieu;
