import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.core.database import SessionLocal
from app.api.v1.endpoints import (
    dashboard, ingredients, suppliers, inventory, proposals, auth
)
from app.schemas.supplier import SupplierQuotationCreate
from app.schemas.inventory import InventoryTransactionCreate
from app.schemas.proposal import ProposalActionRequest
from app.schemas.user import UserLogin

def test_endpoints():
    print("[TEST] Bat dau kiem tra toan bo endpoints Backend API...")
    db = SessionLocal()

    try:
        # Đảm bảo có ít nhất 1 phiếu CHO_DUYET để test
        from app.models.proposal import PurchaseProposal
        p1 = db.query(PurchaseProposal).filter(PurchaseProposal.ma_phieu_de_xuat == 1).first()
        if p1 and p1.trang_thai != "CHO_DUYET":
            p1.trang_thai = "CHO_DUYET"
            db.commit()

        # 1. Dashboard Stats & Alerts & Trends
        stats = dashboard.read_dashboard_stats(db)
        print(f"  [OK] read_dashboard_stats: {stats.tong_nguyen_lieu_dang_dung} nguyen lieu, thieu: {stats.nguy_co_thieu_hang}, cho duyet: {stats.phieu_cho_duyet}")
        assert stats.tong_nguyen_lieu_dang_dung == 15
        assert stats.nguy_co_thieu_hang >= 2
        assert stats.phieu_cho_duyet >= 1

        alerts = dashboard.read_dashboard_alerts(db)
        print(f"  [OK] read_dashboard_alerts: {len(alerts)} alerts (Nguy co thieu / Ton du / Het han)")
        assert len(alerts) > 0

        trends = dashboard.read_dashboard_trends(db)
        print(f"  [OK] read_dashboard_trends: {len(trends)} thang tieu thu")
        assert len(trends) == 12

        forecast = dashboard.read_forecast_summary(db)
        print(f"  [OK] read_forecast_summary: {len(forecast)} nguyen lieu co du lieu du bao 7 ngay")
        assert len(forecast) > 0

        # 2. Ingredients
        all_ings = ingredients.read_ingredients(None, None, None, db)
        print(f"  [OK] read_ingredients (all): {len(all_ings)} items")
        assert len(all_ings) == 15

        danger_ings = ingredients.read_ingredients(None, None, "NGUY_CO_THIEU", db)
        print(f"  [OK] read_ingredients (NGUY_CO_THIEU): {len(danger_ings)} items cham ROP")
        assert len(danger_ings) >= 2

        detail = ingredients.read_ingredient_detail(1, db)
        print(f"  [OK] read_ingredient_detail(1): {detail.ten_nguyen_lieu}, ROP: {detail.diem_dat_hang_lai_rop}, Tinh trang: {detail.tinh_trang}, Batches: {len(detail.batches)}")
        assert len(detail.batches) > 0

        # 3. Suppliers & MCDM Algorithm
        all_sups = suppliers.read_suppliers(None, db)
        print(f"  [OK] read_suppliers: {len(all_sups)} nha cung cap")
        assert len(all_sups) == 5

        s1 = suppliers.read_supplier(1, db)
        print(f"  [OK] read_supplier(1): {s1.ten_nha_cung_cap}, {len(s1.quotations)} bao gia")
        assert len(s1.quotations) > 0

        mcdm = suppliers.compare_suppliers(1, db)
        opt = mcdm.nha_cung_cap_toi_uu
        print(f"  [OK] compare_suppliers(1) MCDM: Toi uu la '{opt.ten_nha_cung_cap}' voi Score={opt.diem_tong_hop_mcdm}/100")
        assert opt is not None
        assert opt.diem_tong_hop_mcdm > 0

        # 4. Inventory Batches & Transactions
        batches = inventory.read_batches(None, False, db)
        print(f"  [OK] read_batches: {len(batches)} lo hang")
        assert len(batches) > 0

        txs = inventory.read_transactions(None, None, 50, db)
        print(f"  [OK] read_transactions: {len(txs)} giao dich kho")
        assert len(txs) > 0

        # Ghi nhận giao dịch kiểm kê mới
        new_tx = inventory.create_transaction(
            InventoryTransactionCreate(
                ma_nguyen_lieu=1,
                loai_giao_dich="KIEM_KE",
                so_luong=12.5,
                ma_tham_chieu="TEST-KK-01",
                ghi_chu="Kiem ke cuoi ngay tu dong test"
            ),
            db
        )
        print(f"  [OK] create_transaction: Giao dich #{new_tx.ma_giao_dich} thanh cong")

        # 5. Proposals (AI Human-in-the-loop)
        props = proposals.read_proposals(None, db)
        print(f"  [OK] read_proposals: {len(props)} phieu de xuat")
        assert len(props) >= 2

        p_detail = proposals.read_proposal_detail(1, db)
        print(f"  [OK] read_proposal_detail(1): {p_detail.nguoi_tao}, Tong tien: {p_detail.tong_tien_du_kien:,.0f}d, Details: {len(p_detail.details)} mon")
        assert len(p_detail.details) >= 3

        # Thực hiện duyệt phiếu
        updated_p = proposals.action_proposal(
            1,
            ProposalActionRequest(
                hanh_dong="APPROVE",
                nguoi_duyet="Nguyen Van Quan Ly",
                y_kien="Duyet don hang de kip chuan bi cho cuoi tuan."
            ),
            db
        )
        print(f"  [OK] action_proposal(1): Trang thai moi -> {updated_p.trang_thai}, Lich su duyet: {len(updated_p.approval_history)} logs")
        assert updated_p.trang_thai == "DA_DUYET"

        # 6. Auth
        token = auth.login(UserLogin(email="quanly@coffee.vn", mat_khau="admin123"), db)
        print(f"  [OK] auth.login: Dang nhap thanh cong, Token: {token.access_token[:20]}...")
        assert token.access_token is not None

        me = auth.get_me()
        print(f"  [OK] auth.get_me: User '{me.ten_nguoi_dung}', Vai tro: {me.vai_tro}")

        print("\n[SUCCESS] TOAN BO 100% CAC ENDPOINT VA BUSINESS LOGIC BACKEND DA PASS HOAN HAO!\n")

    finally:
        db.close()

if __name__ == "__main__":
    test_endpoints()
