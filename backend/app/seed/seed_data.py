import sys
import os
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

# Đảm bảo đường dẫn module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.ingredient import Ingredient
from app.models.supplier import Supplier, SupplierQuotation
from app.models.inventory import Batch, InventoryTransaction
from app.models.recipe import MenuItem, RecipeBOM
from app.models.forecast import DemandForecast
from app.models.proposal import PurchaseProposal, ProposalDetail, ApprovalHistory
from app.models.user import User

def seed_database(db: Session):
    print("[INFO] Bat dau nap du lieu mau (Seeding Database)...")

    # 1. Kiểm tra nếu đã có dữ liệu thì xóa hoặc bỏ qua
    existing_ing = db.query(Ingredient).count()
    if existing_ing > 0:
        print(f"[INFO] Co so du lieu da co {existing_ing} nguyen lieu. Bo qua seed de bao ton du lieu.")
        return

    today = date.today()
    now = datetime.now()

    # 2. Tạo Người dùng (Users)
    users = [
        User(
            ten_nguoi_dung="Nguyễn Văn Quản Lý",
            email="quanly@coffee.vn",
            mat_khau_hash=hash_password("admin123"),
            vai_tro="QUAN_LY",
            trang_thai=True
        ),
        User(
            ten_nguoi_dung="Trần Thị Thủ Kho",
            email="kho@coffee.vn",
            mat_khau_hash=hash_password("admin123"),
            vai_tro="NHAN_VIEN_KHO",
            trang_thai=True
        ),
        User(
            ten_nguoi_dung="Quản Trị Viên Hệ Thống",
            email="admin@coffee.vn",
            mat_khau_hash=hash_password("admin123"),
            vai_tro="ADMIN",
            trang_thai=True
        )
    ]
    db.add_all(users)
    db.commit()
    print("[SUCCESS] Da tao 3 nguoi dung mau (quanly@coffee.vn, kho@coffee.vn, admin@coffee.vn).")

    # 3. Tạo Nhà Cung Cấp (Suppliers)
    suppliers = [
        Supplier(
            ma_nha_cung_cap=1,
            ten_nha_cung_cap="Công ty Cà phê Nguyên Chất Đắk Lắk",
            nguoi_lien_he="Lê Hoàng Long",
            email="daklakcoffee@supply.vn",
            sdt="0903123456",
            dia_chi="Km 12, Quốc lộ 14, TP. Buôn Ma Thuột, Đắk Lắk",
            thoi_gian_giao_du_kien=2,
            diem_uy_tin=4.8,
            diem_chat_luong=4.9,
            trang_thai=True
        ),
        Supplier(
            ma_nha_cung_cap=2,
            ten_nha_cung_cap="Đại lý Phân phối Sữa Horeca Sài Gòn",
            nguoi_lien_he="Phạm Minh Tuấn",
            email="horecasg@dairy.vn",
            sdt="0918765432",
            dia_chi="Số 45 Đường số 7, KDC Trung Sơn, Bình Chánh, TP.HCM",
            thoi_gian_giao_du_kien=1,
            diem_uy_tin=4.7,
            diem_chat_luong=4.8,
            trang_thai=True
        ),
        Supplier(
            ma_nha_cung_cap=3,
            ten_nha_cung_cap="Công ty Nguyên Liệu Pha Chế Vinbar",
            nguoi_lien_he="Vũ Thị Mai",
            email="contact@vinbar.vn",
            sdt="0933889900",
            dia_chi="758/28/18 Xô Viết Nghệ Tĩnh, P.25, Bình Thạnh, TP.HCM",
            thoi_gian_giao_du_kien=2,
            diem_uy_tin=4.6,
            diem_chat_luong=4.7,
            trang_thai=True
        ),
        Supplier(
            ma_nha_cung_cap=4,
            ten_nha_cung_cap="Tổng kho Bao bì Thực phẩm Tân Bình",
            nguoi_lien_he="Đặng Quốc Dũng",
            email="baobitanbinh@pack.vn",
            sdt="0988112233",
            dia_chi="120 Tân Hải, Phường 13, Tân Bình, TP.HCM",
            thoi_gian_giao_du_kien=3,
            diem_uy_tin=4.5,
            diem_chat_luong=4.4,
            trang_thai=True
        ),
        Supplier(
            ma_nha_cung_cap=5,
            ten_nha_cung_cap="Công ty Trà Việt TeaMaster Bảo Lộc",
            nguoi_lien_he="Nguyễn Bích Loan",
            email="teamaster@baoloc.vn",
            sdt="0908556677",
            dia_chi="88 Trần Phú, TP. Bảo Lộc, Lâm Đồng",
            thoi_gian_giao_du_kien=2,
            diem_uy_tin=4.9,
            diem_chat_luong=4.8,
            trang_thai=True
        )
    ]
    db.add_all(suppliers)
    db.commit()
    print("[SUCCESS] Da tao 5 nha cung cap chuyen nghiep F&B.")

    # 4. Tạo Nguyên Liệu (Ingredients)
    # Thiết kế có tính toán: 3 món cảnh báo thiếu (ĐỎ), 1 món tồn dư (VÀNG), còn lại an toàn (XANH)
    ingredients = [
        # Nhóm Cà phê
        Ingredient(
            ma_nguyen_lieu=1,
            ten_nguyen_lieu="Hạt cà phê Robusta Buôn Ma Thuột",
            danh_muc="Cà phê",
            don_vi_tinh="kg",
            muc_ton_an_toan=15.0,
            ton_kho_hien_tai=12.0,  # <= ROP (~18-20kg) -> NGUY_CO_THIEU (ĐỎ)
            muc_ton_toi_da=80.0,
            trang_thai=True
        ),
        Ingredient(
            ma_nguyen_lieu=2,
            ten_nguyen_lieu="Hạt cà phê Arabica Cầu Đất",
            danh_muc="Cà phê",
            don_vi_tinh="kg",
            muc_ton_an_toan=10.0,
            ton_kho_hien_tai=8.5,   # <= ROP (~14-16kg) -> NGUY_CO_THIEU (ĐỎ)
            muc_ton_toi_da=50.0,
            trang_thai=True
        ),
        # Nhóm Sữa
        Ingredient(
            ma_nguyen_lieu=3,
            ten_nguyen_lieu="Sữa tươi tiệt trùng Barista 1L",
            danh_muc="Sữa & Kem",
            don_vi_tinh="hộp",
            muc_ton_an_toan=25.0,
            ton_kho_hien_tai=18.0,  # <= ROP (~32 hộp) -> NGUY_CO_THIEU (ĐỎ)
            muc_ton_toi_da=120.0,
            trang_thai=True
        ),
        Ingredient(
            ma_nguyen_lieu=4,
            ten_nguyen_lieu="Sữa đặc Phương Nam 1.284kg",
            danh_muc="Sữa & Kem",
            don_vi_tinh="lon",
            muc_ton_an_toan=20.0,
            ton_kho_hien_tai=45.0,  # AN_TOAN
            muc_ton_toi_da=150.0,
            trang_thai=True
        ),
        Ingredient(
            ma_nguyen_lieu=5,
            ten_nguyen_lieu="Sữa tươi thanh trùng Đà Lạt Milk 950ml",
            danh_muc="Sữa & Kem",
            don_vi_tinh="chai",
            muc_ton_an_toan=12.0,
            ton_kho_hien_tai=24.0,  # AN_TOAN nhưng sẽ có lô sắp hết hạn!
            muc_ton_toi_da=60.0,
            trang_thai=True
        ),
        # Nhóm Siro & Xốt
        Ingredient(
            ma_nguyen_lieu=6,
            ten_nguyen_lieu="Siro Đào Monin 700ml",
            danh_muc="Siro & Xốt",
            don_vi_tinh="chai",
            muc_ton_an_toan=5.0,
            ton_kho_hien_tai=12.0,
            muc_ton_toi_da=30.0,
            trang_thai=True
        ),
        Ingredient(
            ma_nguyen_lieu=7,
            ten_nguyen_lieu="Siro Dâu Torani 750ml",
            danh_muc="Siro & Xốt",
            don_vi_tinh="chai",
            muc_ton_an_toan=4.0,
            ton_kho_hien_tai=10.0,
            muc_ton_toi_da=25.0,
            trang_thai=True
        ),
        Ingredient(
            ma_nguyen_lieu=8,
            ten_nguyen_lieu="Xốt Socola Hershey 1.36kg",
            danh_muc="Siro & Xốt",
            don_vi_tinh="chai",
            muc_ton_an_toan=4.0,
            ton_kho_hien_tai=9.0,
            muc_ton_toi_da=25.0,
            trang_thai=True
        ),
        # Nhóm Bột
        Ingredient(
            ma_nguyen_lieu=9,
            ten_nguyen_lieu="Bột Cacao Nguyên Chất Đắk Lắk",
            danh_muc="Bột & Topping",
            don_vi_tinh="kg",
            muc_ton_an_toan=8.0,
            ton_kho_hien_tai=95.0,  # Vượt trần 60kg và > 3 lần nhu cầu tuần -> TON_DU (VÀNG)
            muc_ton_toi_da=60.0,
            trang_thai=True
        ),
        Ingredient(
            ma_nguyen_lieu=10,
            ten_nguyen_lieu="Bột Matcha Uji Nhật Bản",
            danh_muc="Bột & Topping",
            don_vi_tinh="kg",
            muc_ton_an_toan=3.0,
            ton_kho_hien_tai=6.5,
            muc_ton_toi_da=20.0,
            trang_thai=True
        ),
        Ingredient(
            ma_nguyen_lieu=11,
            ten_nguyen_lieu="Bột Frappe Base tạo sánh",
            danh_muc="Bột & Topping",
            don_vi_tinh="kg",
            muc_ton_an_toan=5.0,
            ton_kho_hien_tai=14.0,
            muc_ton_toi_da=40.0,
            trang_thai=True
        ),
        # Nhóm Trà
        Ingredient(
            ma_nguyen_lieu=12,
            ten_nguyen_lieu="Trà Đen Phúc Long Đặc Biệt",
            danh_muc="Trà",
            don_vi_tinh="kg",
            muc_ton_an_toan=8.0,
            ton_kho_hien_tai=22.0,
            muc_ton_toi_da=60.0,
            trang_thai=True
        ),
        Ingredient(
            ma_nguyen_lieu=13,
            ten_nguyen_lieu="Trà Ô Long Kim Tuyên Bảo Lộc",
            danh_muc="Trà",
            don_vi_tinh="kg",
            muc_ton_an_toan=6.0,
            ton_kho_hien_tai=16.0,
            muc_ton_toi_da=50.0,
            trang_thai=True
        ),
        # Nhóm Bao bì
        Ingredient(
            ma_nguyen_lieu=14,
            ten_nguyen_lieu="Ly nhựa PET Takeaway 500ml",
            danh_muc="Bao bì",
            don_vi_tinh="cái",
            muc_ton_an_toan=500.0,
            ton_kho_hien_tai=1800.0,
            muc_ton_toi_da=5000.0,
            trang_thai=True
        ),
        Ingredient(
            ma_nguyen_lieu=15,
            ten_nguyen_lieu="Ống hút giấy sinh học bọc màng",
            danh_muc="Bao bì",
            don_vi_tinh="cái",
            muc_ton_an_toan=600.0,
            ton_kho_hien_tai=2200.0,
            muc_ton_toi_da=6000.0,
            trang_thai=True
        )
    ]
    db.add_all(ingredients)
    db.commit()
    print("[SUCCESS] Da tao 15 nguyen lieu F&B voi cac kich ban ton kho thuc te.")

    # 5. Tạo Báo Giá Nhà Cung Cấp (CC_NGUYEN_LIEU)
    # Cung cấp báo giá đa dạng để chạy giải thuật so sánh MCDM
    quotations = [
        # Robusta (id=1): NCC 1 và NCC 3
        SupplierQuotation(ma_nha_cung_cap=1, ma_nguyen_lieu=1, don_gia=145000.0, so_luong_dat_toi_thieu=10.0, thoi_gian_giao_hang=2),
        SupplierQuotation(ma_nha_cung_cap=3, ma_nguyen_lieu=1, don_gia=155000.0, so_luong_dat_toi_thieu=5.0, thoi_gian_giao_hang=1),
        
        # Arabica (id=2): NCC 1 và NCC 3
        SupplierQuotation(ma_nha_cung_cap=1, ma_nguyen_lieu=2, don_gia=260000.0, so_luong_dat_toi_thieu=5.0, thoi_gian_giao_hang=2),
        SupplierQuotation(ma_nha_cung_cap=3, ma_nguyen_lieu=2, don_gia=280000.0, so_luong_dat_toi_thieu=2.0, thoi_gian_giao_hang=1),

        # Sữa tươi 1L (id=3): NCC 2 và NCC 3
        SupplierQuotation(ma_nha_cung_cap=2, ma_nguyen_lieu=3, don_gia=33000.0, so_luong_dat_toi_thieu=12.0, thoi_gian_giao_hang=1),
        SupplierQuotation(ma_nha_cung_cap=3, ma_nguyen_lieu=3, don_gia=35500.0, so_luong_dat_toi_thieu=6.0, thoi_gian_giao_hang=2),

        # Sữa đặc (id=4): NCC 2
        SupplierQuotation(ma_nha_cung_cap=2, ma_nguyen_lieu=4, don_gia=68000.0, so_luong_dat_toi_thieu=6.0, thoi_gian_giao_hang=1),

        # Sữa tươi Đà Lạt Milk (id=5): NCC 2
        SupplierQuotation(ma_nha_cung_cap=2, ma_nguyen_lieu=5, don_gia=38000.0, so_luong_dat_toi_thieu=6.0, thoi_gian_giao_hang=1),

        # Siro Đào (id=6): NCC 3
        SupplierQuotation(ma_nha_cung_cap=3, ma_nguyen_lieu=6, don_gia=215000.0, so_luong_dat_toi_thieu=2.0, thoi_gian_giao_hang=2),

        # Siro Dâu (id=7): NCC 3
        SupplierQuotation(ma_nha_cung_cap=3, ma_nguyen_lieu=7, don_gia=195000.0, so_luong_dat_toi_thieu=2.0, thoi_gian_giao_hang=2),

        # Xốt Socola (id=8): NCC 3
        SupplierQuotation(ma_nha_cung_cap=3, ma_nguyen_lieu=8, don_gia=185000.0, so_luong_dat_toi_thieu=2.0, thoi_gian_giao_hang=2),

        # Bột Cacao (id=9): NCC 1 và NCC 3
        SupplierQuotation(ma_nha_cung_cap=1, ma_nguyen_lieu=9, don_gia=160000.0, so_luong_dat_toi_thieu=5.0, thoi_gian_giao_hang=2),
        SupplierQuotation(ma_nha_cung_cap=3, ma_nguyen_lieu=9, don_gia=175000.0, so_luong_dat_toi_thieu=2.0, thoi_gian_giao_hang=1),

        # Bột Matcha (id=10): NCC 3
        SupplierQuotation(ma_nha_cung_cap=3, ma_nguyen_lieu=10, don_gia=650000.0, so_luong_dat_toi_thieu=1.0, thoi_gian_giao_hang=2),

        # Bột Frappe (id=11): NCC 3
        SupplierQuotation(ma_nha_cung_cap=3, ma_nguyen_lieu=11, don_gia=110000.0, so_luong_dat_toi_thieu=2.0, thoi_gian_giao_hang=2),

        # Trà Đen (id=12): NCC 5
        SupplierQuotation(ma_nha_cung_cap=5, ma_nguyen_lieu=12, don_gia=135000.0, so_luong_dat_toi_thieu=5.0, thoi_gian_giao_hang=2),

        # Trà Ô Long (id=13): NCC 5
        SupplierQuotation(ma_nha_cung_cap=5, ma_nguyen_lieu=13, don_gia=220000.0, so_luong_dat_toi_thieu=3.0, thoi_gian_giao_hang=2),

        # Ly nhựa (id=14): NCC 4
        SupplierQuotation(ma_nha_cung_cap=4, ma_nguyen_lieu=14, don_gia=550.0, so_luong_dat_toi_thieu=500.0, thoi_gian_giao_hang=3),

        # Ống hút (id=15): NCC 4
        SupplierQuotation(ma_nha_cung_cap=4, ma_nguyen_lieu=15, don_gia=180.0, so_luong_dat_toi_thieu=1000.0, thoi_gian_giao_hang=3),
    ]
    db.add_all(quotations)
    db.commit()
    print("[SUCCESS] Da tao bang bao gia da tieu chuan (CC_NGUYEN_LIEU).")

    # 6. Tạo Lô Hàng (LO_HANG)
    # Lô đặc biệt: Sữa Đà Lạt Milk có lô sắp hết hạn trong 3 ngày
    batches = [
        Batch(
            ma_nguyen_lieu=1,
            ma_lo_nha_cung_cap="DKL-ROB-20261015",
            so_luong_nhap=30.0,
            so_luong_con_lai=12.0,
            ngay_nhap_kho=now - timedelta(days=20),
            han_su_dung=today + timedelta(days=160),
            don_gia_nhap=145000.0
        ),
        Batch(
            ma_nguyen_lieu=2,
            ma_lo_nha_cung_cap="DKL-ARA-20261018",
            so_luong_nhap=20.0,
            so_luong_con_lai=8.5,
            ngay_nhap_kho=now - timedelta(days=18),
            han_su_dung=today + timedelta(days=150),
            don_gia_nhap=260000.0
        ),
        Batch(
            ma_nguyen_lieu=3,
            ma_lo_nha_cung_cap="MILK-BAR-20261028",
            so_luong_nhap=48.0,
            so_luong_con_lai=18.0,
            ngay_nhap_kho=now - timedelta(days=10),
            han_su_dung=today + timedelta(days=50),
            don_gia_nhap=33000.0
        ),
        # Lô Sữa Đà Lạt Milk: có 6 chai hết hạn trong 3 ngày tới!
        Batch(
            ma_nguyen_lieu=5,
            ma_lo_nha_cung_cap="DLM-EXP-NEAR",
            so_luong_nhap=12.0,
            so_luong_con_lai=6.0,
            ngay_nhap_kho=now - timedelta(days=8),
            han_su_dung=today + timedelta(days=3),  # Cảnh báo hết hạn!
            don_gia_nhap=38000.0
        ),
        Batch(
            ma_nguyen_lieu=5,
            ma_lo_nha_cung_cap="DLM-FRESH",
            so_luong_nhap=18.0,
            so_luong_con_lai=18.0,
            ngay_nhap_kho=now - timedelta(days=1),
            han_su_dung=today + timedelta(days=10),
            don_gia_nhap=38000.0
        ),
        Batch(
            ma_nguyen_lieu=9,
            ma_lo_nha_cung_cap="CC-OVERSTOCK-LOT",
            so_luong_nhap=100.0,
            so_luong_con_lai=95.0,
            ngay_nhap_kho=now - timedelta(days=15),
            han_su_dung=today + timedelta(days=240),
            don_gia_nhap=160000.0
        ),
    ]
    db.add_all(batches)
    db.commit()
    print("[SUCCESS] Da tao cac lo hang thuc te (LO_HANG) kem kich ban canh bao han dung.")

    # 7. Tạo Lịch Sử Biến Động Kho (GIAO_DICH_KHO) 12 tháng gần nhất
    transactions = []
    # Sinh các giao dịch xuất bán đại diện cho từng tháng
    for month_back in range(11, -1, -1):
        tx_date = now - timedelta(days=month_back * 30 + 5)
        # Xuất bán cà phê Robusta
        transactions.append(
            InventoryTransaction(
                ma_nguyen_lieu=1,
                loai_giao_dich="XUAT_BAN",
                so_luong=round(120.0 + (month_back % 3) * 15.0, 1),
                ngay_giao_dich=tx_date,
                ma_tham_chieu=f"POS-SUM-M{12-month_back}",
                ghi_chu="Tiêu hao bóc tách công thức qua đơn bán POS"
            )
        )
        # Xuất bán Sữa tươi
        transactions.append(
            InventoryTransaction(
                ma_nguyen_lieu=3,
                loai_giao_dich="XUAT_BAN",
                so_luong=round(180.0 + (month_back % 2) * 20.0, 1),
                ngay_giao_dich=tx_date,
                ma_tham_chieu=f"POS-MILK-M{12-month_back}",
                ghi_chu="Tiêu hao pha chế Latte, Cappuccino"
            )
        )

    # Thêm giao dịch gần nhất
    transactions.append(
        InventoryTransaction(
            ma_nguyen_lieu=1,
            loai_giao_dich="NHAP",
            so_luong=30.0,
            ngay_giao_dich=now - timedelta(days=20),
            ma_tham_chieu="PNK-20261015-01",
            ghi_chu="Nhập kho theo đơn đặt hàng NCC Đắk Lắk"
        )
    )
    transactions.append(
        InventoryTransaction(
            ma_nguyen_lieu=5,
            loai_giao_dich="HAO_HUT",
            so_luong=1.0,
            ngay_giao_dich=now - timedelta(days=2),
            ma_tham_chieu="HH-20261106",
            ghi_chu="Rơi vỡ trong ca làm việc buổi sáng"
        )
    )
    db.add_all(transactions)
    db.commit()
    print("[SUCCESS] Da tao lich su bien dong kho 12 thang (GIAO_DICH_KHO).")

    # 8. Tạo Dự Báo Nhu Cầu 7 Ngày Tới (DU_BAO_NHU_CAU)
    forecasts = []
    # Dự báo cho Robusta (id=1): tiêu hao ~4.5 - 6.5 kg/ngày (cuối tuần cao điểm)
    daily_weights = [1.0, 1.05, 1.1, 1.15, 1.4, 1.5, 1.2] # T2 -> CN
    for idx, w in enumerate(daily_weights):
        day_target = today + timedelta(days=idx + 1)
        # Robusta
        forecasts.append(
            DemandForecast(
                ma_nguyen_lieu=1,
                ngay_du_bao=day_target,
                so_luong_du_bao=round(4.2 * w, 2),
                do_tin_cay=0.95,
                phuong_phap="Prophet_v1"
            )
        )
        # Arabica
        forecasts.append(
            DemandForecast(
                ma_nguyen_lieu=2,
                ngay_du_bao=day_target,
                so_luong_du_bao=round(2.6 * w, 2),
                do_tin_cay=0.94,
                phuong_phap="Prophet_v1"
            )
        )
        # Sữa tươi
        forecasts.append(
            DemandForecast(
                ma_nguyen_lieu=3,
                ngay_du_bao=day_target,
                so_luong_du_bao=round(7.5 * w, 2),
                do_tin_cay=0.96,
                phuong_phap="Prophet_v1"
            )
        )
        # Sữa đặc
        forecasts.append(
            DemandForecast(
                ma_nguyen_lieu=4,
                ngay_du_bao=day_target,
                so_luong_du_bao=round(4.0 * w, 2),
                do_tin_cay=0.95,
                phuong_phap="Prophet_v1"
            )
        )
        # Ly nhựa
        forecasts.append(
            DemandForecast(
                ma_nguyen_lieu=14,
                ngay_du_bao=day_target,
                so_luong_du_bao=round(180.0 * w, 0),
                do_tin_cay=0.92,
                phuong_phap="XGBoost_v1"
            )
        )
    db.add_all(forecasts)
    db.commit()
    print("[SUCCESS] Da tao du lieu du bao nhu cau AI 7 ngay toi (DU_BAO_NHU_CAU).")

    # 9. Tạo Phiếu Đề Xuất Mua Hàng Mẫu (AI Human-in-the-loop)
    # Phiếu 1: Đang chờ duyệt (CHO_DUYET) do AI Procurement Agent tạo cho 3 nguyên liệu thiếu
    proposal_pending = PurchaseProposal(
        ma_phieu_de_xuat=1,
        ngay_tao=now - timedelta(hours=3),
        tong_tien_du_kien=12850000.0,
        trang_thai="CHO_DUYET",
        ly_do_tong_quan="AI Agent phát hiện 3 nguyên liệu chạm ngưỡng cảnh báo tồn kho (Tồn <= ROP) dựa trên dự báo tiêu thụ 7 ngày tới. Đề xuất đặt hàng sớm để tránh đứt gãy pha chế vào cao điểm cuối tuần.",
        nguoi_tao="AI Procurement Agent (Gemini Pro)"
    )
    db.add(proposal_pending)
    db.commit()

    details_pending = [
        ProposalDetail(
            ma_phieu_de_xuat=1,
            ma_nguyen_lieu=1,
            ma_nha_cung_cap=1,
            so_luong_de_xuat=40.0,
            don_gia_du_kien=145000.0,
            so_luong_du_doan_7ngay=34.8,
            ly_do_de_xuat="Tồn kho còn 12kg ≤ ROP 23.4kg. Chọn NCC Cà phê Đắk Lắk vì đạt điểm MCDM cao nhất (92.4/100), đơn giá thấp hơn 10.000đ/kg và chất lượng 4.9 sao."
        ),
        ProposalDetail(
            ma_phieu_de_xuat=1,
            ma_nguyen_lieu=2,
            ma_nha_cung_cap=1,
            so_luong_de_xuat=20.0,
            don_gia_du_kien=260000.0,
            so_luong_du_doan_7ngay=21.5,
            ly_do_de_xuat="Tồn kho còn 8.5kg ≤ ROP 15.2kg. Chọn NCC Cà phê Đắk Lắk kết hợp chuyến xe giao cùng hạt Robusta để tối ưu chi phí vận chuyển."
        ),
        ProposalDetail(
            ma_phieu_de_xuat=1,
            ma_nguyen_lieu=3,
            ma_nha_cung_cap=2,
            so_luong_de_xuat=60.0,
            don_gia_du_kien=33000.0,
            so_luong_du_doan_7ngay=62.0,
            ly_do_de_xuat="Tồn kho còn 18 hộp ≤ ROP 32.5 hộp. Đại lý Sữa Horeca Sài Gòn có Lead Time chỉ 1 ngày, giá tốt nhất 33.000đ/hộp."
        )
    ]
    db.add_all(details_pending)

    # Phiếu 2: Đã duyệt tuần trước (DA_DUYET) kèm Lịch sử duyệt
    proposal_approved = PurchaseProposal(
        ma_phieu_de_xuat=2,
        ngay_tao=now - timedelta(days=7),
        tong_tien_du_kien=3850000.0,
        trang_thai="DA_DUYET",
        ly_do_tong_quan="Bổ sung định kỳ tuần trước cho các dòng siro và bao bì.",
        nguoi_tao="AI Procurement Agent"
    )
    db.add(proposal_approved)
    db.commit()

    details_approved = [
        ProposalDetail(
            ma_phieu_de_xuat=2,
            ma_nguyen_lieu=14,
            ma_nha_cung_cap=4,
            so_luong_de_xuat=2000.0,
            don_gia_du_kien=550.0,
            so_luong_du_doan_7ngay=1200.0,
            ly_do_de_xuat="Đạt MOQ 500 cái của Tổng kho Bao bì Tân Bình."
        ),
        ProposalDetail(
            ma_phieu_de_xuat=2,
            ma_nguyen_lieu=15,
            ma_nha_cung_cap=4,
            so_luong_de_xuat=3000.0,
            don_gia_du_kien=180.0,
            so_luong_du_doan_7ngay=1400.0,
            ly_do_de_xuat="Bổ sung ống hút giấy thân thiện môi trường."
        )
    ]
    db.add_all(details_approved)

    approval_log = ApprovalHistory(
        ma_phieu_de_xuat=2,
        nguoi_duyet="Nguyễn Văn Quản Lý",
        hanh_dong="APPROVE",
        y_kien="Đã kiểm tra kho thực tế, số lượng bao bì phù hợp với công suất bán dự kiến.",
        thoi_gian_duyet=now - timedelta(days=6, hours=20)
    )
    db.add(approval_log)
    db.commit()
    print("[SUCCESS] Da tao cac phieu de xuat mua hang (PHIEU_DE_XUAT_MUA) va lich su duyet.")

    # 10. Tạo Thực Đơn & Công Thức Bóc Tách (MenuItem & RecipeBOM)
    menu_items = [
        MenuItem(ma_mon=1, ten_mon="Cà phê đen đá Buôn Ma Thuột", danh_muc="Cà phê truyền thống", don_gia_ban=29000.0),
        MenuItem(ma_mon=2, ten_mon="Cà phê sữa đá Sài Gòn", danh_muc="Cà phê truyền thống", don_gia_ban=35000.0),
        MenuItem(ma_mon=3, ten_mon="Latte Nóng Barista", danh_muc="Espresso Bar", don_gia_ban=49000.0),
        MenuItem(ma_mon=4, ten_mon="Trà Đào Cam Sả", danh_muc="Trà trái cây", don_gia_ban=45000.0),
    ]
    db.add_all(menu_items)
    db.commit()

    recipes = [
        # Cà phê đen đá: 0.025kg Robusta, 1 ly nhựa, 1 ống hút
        RecipeBOM(ma_mon=1, ma_nguyen_lieu=1, so_luong_tieu_hao=0.025, ghi_chu="25g Robusta nguyên chất"),
        RecipeBOM(ma_mon=1, ma_nguyen_lieu=14, so_luong_tieu_hao=1.0, ghi_chu="1 ly nhựa 500ml"),
        RecipeBOM(ma_mon=1, ma_nguyen_lieu=15, so_luong_tieu_hao=1.0, ghi_chu="1 ống hút giấy"),

        # Cà phê sữa đá: 0.025kg Robusta, 0.03 lon sữa đặc (~40g), 1 ly, 1 ống hút
        RecipeBOM(ma_mon=2, ma_nguyen_lieu=1, so_luong_tieu_hao=0.025, ghi_chu="25g Robusta"),
        RecipeBOM(ma_mon=2, ma_nguyen_lieu=4, so_luong_tieu_hao=0.03, ghi_chu="40g sữa đặc Phương Nam"),
        RecipeBOM(ma_mon=2, ma_nguyen_lieu=14, so_luong_tieu_hao=1.0, ghi_chu="1 ly nhựa"),
        RecipeBOM(ma_mon=2, ma_nguyen_lieu=15, so_luong_tieu_hao=1.0, ghi_chu="1 ống hút"),

        # Latte: 0.02kg Arabica, 0.2 hộp sữa tươi 1L (200ml)
        RecipeBOM(ma_mon=3, ma_nguyen_lieu=2, so_luong_tieu_hao=0.02, ghi_chu="Double shot Arabica Cầu Đất"),
        RecipeBOM(ma_mon=3, ma_nguyen_lieu=3, so_luong_tieu_hao=0.20, ghi_chu="200ml sữa tươi Barista steam bọt"),

        # Trà đào: 0.015kg trà đen, 0.04 chai siro đào (30ml), 1 ly, 1 ống hút
        RecipeBOM(ma_mon=4, ma_nguyen_lieu=12, so_luong_tieu_hao=0.015, ghi_chu="15g trà đen ủ cốt"),
        RecipeBOM(ma_mon=4, ma_nguyen_lieu=6, so_luong_tieu_hao=0.04, ghi_chu="30ml siro đào Monin"),
        RecipeBOM(ma_mon=4, ma_nguyen_lieu=14, so_luong_tieu_hao=1.0, ghi_chu="1 ly nhựa"),
        RecipeBOM(ma_mon=4, ma_nguyen_lieu=15, so_luong_tieu_hao=1.0, ghi_chu="1 ống hút"),
    ]
    db.add_all(recipes)
    db.commit()
    print("[SUCCESS] Da tao thuc don do uong va dinh muc boc tach nguyen lieu (BOM).")

    print("\n[DONE] HOAN TAT NAP DU LIEU MAU THANH CONG 100%!\n")

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
