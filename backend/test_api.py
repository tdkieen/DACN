import sys
import os

os.environ["AUTH_ENABLED"] = "true"  # test này kiểm tra cả 401/403 nên phải bật phân quyền
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.core.database import SessionLocal, Base, engine
from app.api.v1.endpoints import (
    dashboard, ingredients, suppliers, inventory, proposals, auth, dinh_muc_bom, du_bao_ai
)
from app.schemas.supplier import SupplierQuotationCreate
from app.schemas.inventory import InventoryTransactionCreate
from app.schemas.proposal import ProposalActionRequest
from app.schemas.user import UserLogin
from app.schemas.dinh_muc_bom import (
    YeuCauMoPhongBom,
    MonBanDauVao,
    YeuCauTaoHoaDonPos,
)
from app.seed.seed_data import seed_database

def test_endpoints():
    print("[TEST] Bat dau kiem tra toan bo endpoints Backend API, BOM (Tuan 5) & Du bao AI (Tuan 6)...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)

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
        assert detail.diem_dat_hang_lai_rop > 0

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

        # Phân quyền: chỉ QUAN_LY được duyệt phiếu
        from fastapi import HTTPException
        from app.api.deps import get_current_user, require_roles
        from app.models.user import User
        quan_ly = db.query(User).filter(User.email == "quanly@coffee.vn").first()
        thu_kho = db.query(User).filter(User.email == "kho@coffee.vn").first()
        admin = db.query(User).filter(User.email == "admin@coffee.vn").first()
        only_manager = require_roles("QUAN_LY")
        assert only_manager(quan_ly).vai_tro == "QUAN_LY"
        for banned in (thu_kho, admin):
            try:
                only_manager(banned)
                raise AssertionError("Vai tro khong duoc phep ma van qua duoc")
            except HTTPException as e:
                assert e.status_code == 403
        print("  [OK] require_roles(QUAN_LY): NHAN_VIEN_KHO va ADMIN bi chan 403")

        # Thực hiện duyệt phiếu (bằng tài khoản Quản lý)
        updated_p = proposals.action_proposal(
            1,
            ProposalActionRequest(
                hanh_dong="APPROVE",
                nguoi_duyet="Nguyen Van Quan Ly",
                y_kien="Duyet don hang de kip chuan bi cho cuoi tuan."
            ),
            db,
            quan_ly,
        )
        print(f"  [OK] action_proposal(1): Trang thai moi -> {updated_p.trang_thai}, Lich su duyet: {len(updated_p.approval_history)} logs")
        assert updated_p.trang_thai == "DA_DUYET"

        # Test AI tự động quét kho & lập đề xuất
        ai_prop = proposals.trigger_ai_proposal(db)
        print(
            f"  [OK] trigger_ai_proposal: Phieu #{ai_prop.ma_phieu_de_xuat}, "
            f"Tong tien: {ai_prop.tong_tien_du_kien:,.0f}d, Details: {len(ai_prop.details)} mat hang"
        )
        assert ai_prop.tong_tien_du_kien > 0
        assert len(ai_prop.details) > 0

        # 6. Auth
        token = auth.login(UserLogin(email="quanly@coffee.vn", mat_khau="admin123"), db)
        print(f"  [OK] auth.login: Dang nhap thanh cong, Token: {token.access_token[:20]}...")
        assert token.access_token is not None

        from fastapi.security import HTTPAuthorizationCredentials
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token.access_token)
        me = auth.get_me(get_current_user(creds, db))
        assert me.email == "quanly@coffee.vn" and me.vai_tro == "QUAN_LY"
        try:
            get_current_user(None, db)
            raise AssertionError("Khong co token ma van qua duoc")
        except HTTPException as e:
            assert e.status_code == 401
        print("  [OK] get_current_user: khong token -> 401, token hop le -> dung nguoi dung")
        print(f"  [OK] auth.get_me: User '{me.ten_nguoi_dung}', Vai tro: {me.vai_tro}")

        # 7. Tuần 5: Bóc tách định mức BOM & Làm sạch dữ liệu bán hàng
        menus_bom = dinh_muc_bom.doc_thuc_don_kem_dinh_muc_bom(db)
        total_bom_lines = sum(len(m.cong_thuc_bom) for m in menus_bom)
        covered_ings = {r.ma_nguyen_lieu for m in menus_bom for r in m.cong_thuc_bom}
        print(f"  [OK] dinh_muc_bom.doc_thuc_don_kem_dinh_muc_bom: {len(menus_bom)} mon do uong, {total_bom_lines} dinh muc BOM, phu {len(covered_ings)}/15 nguyen lieu")
        assert len(menus_bom) == 12
        assert len(covered_ings) == 15

        sim_res = dinh_muc_bom.mo_phong_boc_tach_dinh_muc(
            YeuCauMoPhongBom(
                danh_sach_mon_ban=[
                    MonBanDauVao(ma_mon=1, so_luong_ly=100),  # 100 ly Cà phê Đen: 2.5kg Robusta
                    MonBanDauVao(ma_mon=4, so_luong_ly=50),   # 50 ly Cà phê Sữa Tươi Pha Máy: 1.0kg Arabica, 9.0 hộp Sữa Barista
                ],
                cap_nhat_xuat_kho=False
            ),
            db
        )
        robusta_sim = next(x for x in sim_res.danh_sach_nguyen_lieu_tieu_hao if x.ma_nguyen_lieu == 1)
        arabica_sim = next(x for x in sim_res.danh_sach_nguyen_lieu_tieu_hao if x.ma_nguyen_lieu == 2)
        print(
            f"  [OK] dinh_muc_bom.mo_phong_boc_tach_dinh_muc: {sim_res.tong_so_ly_ban} ly -> "
            f"Robusta={robusta_sim.tong_luong_tieu_hao}kg, Arabica={arabica_sim.tong_luong_tieu_hao}kg, "
            f"Doanh thu={sim_res.tong_doanh_thu_du_kien:,.0f}d, Loi nhuan gop={sim_res.loi_nhuan_gop_du_kien:,.0f}d"
        )
        assert robusta_sim.tong_luong_tieu_hao == 2.5
        assert arabica_sim.tong_luong_tieu_hao == 1.0

        etl_report = dinh_muc_bom.kich_hoat_quy_trinh_du_lieu_bom(so_ngay=365, db=db)
        print(
            f"  [OK] dinh_muc_bom.kich_hoat_quy_trinh_du_lieu_bom: Tho={etl_report.tong_dong_tho}, "
            f"Sach={etl_report.tong_dong_sach} ({etl_report.ty_le_du_lieu_sach}%), "
            f"Trung={etl_report.so_dong_trung_lap}, Thieu={etl_report.so_dong_thieu_du_lieu}, "
            f"Am/Loi={etl_report.so_dong_am_hoac_loi}, Ngoai lai(IQR)={etl_report.so_dong_ngoai_lai_da_xu_ly}, "
            f"Chuoi thoi gian={etl_report.tong_ban_ghi_tieu_hao_sinh_ra}"
        )
        assert etl_report.tong_dong_tho > etl_report.tong_dong_sach
        assert etl_report.so_dong_trung_lap > 0
        assert etl_report.so_dong_ngoai_lai_da_xu_ly > 0
        assert etl_report.tong_ban_ghi_tieu_hao_sinh_ra == 365 * 15

        ts_robusta = dinh_muc_bom.doc_chuoi_thoi_gian_nguyen_lieu(ma_nguyen_lieu=1, so_ngay=90, db=db)
        print(
            f"  [OK] dinh_muc_bom.doc_chuoi_thoi_gian_nguyen_lieu(1): {ts_robusta.so_ngay_du_lieu} ngay, "
            f"TB ngay thuong={ts_robusta.tieu_hao_ngay_thuong_tb}kg, "
            f"TB cuoi tuan={ts_robusta.tieu_hao_cuoi_tuan_tb}kg (+{ts_robusta.ty_le_tang_cuoi_tuan_pct}%)"
        )
        assert ts_robusta.so_ngay_du_lieu >= 90
        assert ts_robusta.tieu_hao_cuoi_tuan_tb > ts_robusta.tieu_hao_ngay_thuong_tb

        pos_order_res = dinh_muc_bom.tao_hoa_don_ban_hang_pos(
            YeuCauTaoHoaDonPos(
                ma_hoa_don_pos="POS-TEST-FEFO-01",
                ca_ban="SANG",
                danh_sach_mon_ban=[
                    MonBanDauVao(ma_mon=7, so_luong_ly=10),  # 10 ly Trà Đào Cam Sả
                ],
            ),
            db=db,
        )
        assert pos_order_res.da_cap_nhat_kho is True
        pos_hist = dinh_muc_bom.doc_lich_su_ban_hang_pos(ma_mon=7, ca_ban="SANG", gioi_han=10, db=db)
        print(
            f"  [OK] dinh_muc_bom.tao_hoa_don_ban_hang_pos & doc_lich_su_ban_hang_pos: Ghi nhan don POS ({pos_order_res.tong_so_ly_ban} ly), "
            f"lich su truy xuat={len(pos_hist)} dong"
        )
        assert len(pos_hist) > 0

        # 8. Tuần 6: Huấn luyện, Đánh giá Mô hình ML & Dự báo Nhu cầu 7 ngày cho 15/15 Nguyên liệu
        ml_report = du_bao_ai.kich_hoat_huan_luyen_mo_hinh(chan_troi_du_bao=7, db=db)
        ml_run = ml_report.lan_huan_luyen
        print(
            f"  [OK] du_bao_ai.kich_hoat_huan_luyen_mo_hinh: {ml_run.so_nguyen_lieu}/15 nguyen lieu, "
            f"Baseline MAPE={ml_run.baseline_mape_tb}% -> ML MAPE={ml_run.ml_mape_tb}% "
            f"(-{ml_run.muc_giam_sai_so_mape_pct}%), thang nhieu nhat={ml_run.mo_hinh_tot_nhat_pho_bien}"
        )
        assert ml_run.so_nguyen_lieu == 15
        assert ml_run.ml_mape_tb < ml_run.baseline_mape_tb
        assert ml_run.ml_mape_tb < 10.0
        assert ml_run.muc_giam_sai_so_mape_pct > 40.0
        assert len(ml_report.bang_xep_hang_mo_hinh) == 5
        assert len(ml_report.danh_sach_du_bao_7_ngay) == 15

        tong_quan_ai = du_bao_ai.doc_tong_quan_du_bao_ai(db=db)
        assert tong_quan_ai.lan_huan_luyen.ma_lan_huan_luyen == ml_run.ma_lan_huan_luyen

        so_sanh_all = du_bao_ai.doc_bang_so_sanh_mo_hinh(ma_nguyen_lieu=None, chi_lay_tot_nhat=False, db=db)
        so_sanh_best = du_bao_ai.doc_bang_so_sanh_mo_hinh(ma_nguyen_lieu=None, chi_lay_tot_nhat=True, db=db)
        print(
            f"  [OK] du_bao_ai.doc_bang_so_sanh_mo_hinh: {len(so_sanh_all)} dong (15 NL x 5 mo hinh), "
            f"{len(so_sanh_best)} mo hinh thang cuoc"
        )
        assert len(so_sanh_all) == 75
        assert len(so_sanh_best) == 15

        du_bao_all = du_bao_ai.doc_du_bao_7_ngay_tat_ca(danh_muc=None, db=db)
        assert len(du_bao_all) == 15
        assert all(len(x.du_bao_chi_tiet) == 7 for x in du_bao_all)

        ct_robusta = du_bao_ai.doc_chi_tiet_du_bao_nguyen_lieu(ma_nguyen_lieu=1, db=db)
        print(
            f"  [OK] du_bao_ai.doc_chi_tiet_du_bao_nguyen_lieu(1): Mo hinh={ct_robusta.mo_hinh_duoc_chon}, "
            f"ACF7={ct_robusta.chan_doan_chuoi.tu_tuong_quan_lag_7}, "
            f"Test points={len(ct_robusta.kiem_thu_thuc_te_vs_du_bao)}, Tong 7N={ct_robusta.tong_du_bao_7_ngay}kg"
        )
        assert len(ct_robusta.kiem_thu_thuc_te_vs_du_bao) >= 40
        assert len(ct_robusta.du_bao_7_ngay_toi) == 7

        # Kiểm tra Dashboard forecast không còn rơi về 'Ước tính tạm' sau khi huấn luyện Tuần 6
        dash_forecast = dashboard.read_forecast_summary(db)
        assert len(dash_forecast) > 0
        assert all(not f.la_du_lieu_uoc_tinh for f in dash_forecast)
        print(
            f"  [OK] dashboard.read_forecast_summary (sau Tuan 6): 100% dung du bao AI that "
            f"({len(dash_forecast)} nguyen lieu hien thi, khong con uoc tinh tam)"
        )

        lich_su_ml = du_bao_ai.doc_lich_su_huan_luyen(gioi_han=5, db=db)
        assert len(lich_su_ml) >= 1

        print("\n[SUCCESS] TOAN BO 100% CAC ENDPOINT VA QUY TRINH DU LIEU - AI (DEN TUAN 6) DA PASS HOAN HAO!\n")

    finally:
        db.close()

if __name__ == "__main__":
    test_endpoints()
