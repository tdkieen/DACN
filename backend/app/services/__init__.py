from app.services.inventory_service import (
    get_ingredients, get_ingredient_detail, create_ingredient, update_ingredient, delete_ingredient,
    get_batches, get_inventory_transactions, record_transaction
)
from app.services.supplier_service import (
    get_suppliers, get_supplier_by_id, create_supplier, update_supplier,
    create_or_update_quotation, evaluate_suppliers_mcdm
)
from app.services.dashboard_service import (
    get_dashboard_stats, get_active_alerts, get_consumption_trends_12_months,
    get_forecast_summary_7_days, get_dashboard_overview
)
from app.services.proposal_service import (
    get_proposals, get_proposal_by_id, handle_proposal_action, generate_ai_proposal
)
from app.services.auth_service import (
    authenticate_user, login_and_generate_token, create_user
)
from app.services.dich_vu_dinh_muc_bom import (
    khoi_tao_thuc_don_va_dinh_muc_bom,
    sinh_du_lieu_ban_hang_tho_12_thang,
    lam_sach_du_lieu_ban_hang,
    chay_quy_trinh_boc_tach_bom,
    lay_thuc_don_kem_dinh_muc_bom,
    luu_mon_an_kem_dinh_muc_bom,
    mo_phong_boc_tach_bom,
    ghi_nhan_hoa_don_pos_va_tru_kho,
    lay_lich_su_ban_hang_pos,
    lay_bao_cao_chat_luong_du_lieu,
    lay_chuoi_thoi_gian_tieu_hao,
)

__all__ = [
    "get_ingredients", "get_ingredient_detail", "create_ingredient", "update_ingredient", "delete_ingredient",
    "get_batches", "get_inventory_transactions", "record_transaction",
    "get_suppliers", "get_supplier_by_id", "create_supplier", "update_supplier",
    "create_or_update_quotation", "evaluate_suppliers_mcdm",
    "get_dashboard_stats", "get_active_alerts", "get_consumption_trends_12_months",
    "get_forecast_summary_7_days", "get_dashboard_overview",
    "get_proposals", "get_proposal_by_id", "handle_proposal_action",
    "authenticate_user", "login_and_generate_token", "create_user",
    "khoi_tao_thuc_don_va_dinh_muc_bom",
    "sinh_du_lieu_ban_hang_tho_12_thang",
    "lam_sach_du_lieu_ban_hang",
    "chay_quy_trinh_boc_tach_bom",
    "lay_thuc_don_kem_dinh_muc_bom",
    "luu_mon_an_kem_dinh_muc_bom",
    "mo_phong_boc_tach_bom",
    "ghi_nhan_hoa_don_pos_va_tru_kho",
    "lay_lich_su_ban_hang_pos",
    "lay_bao_cao_chat_luong_du_lieu",
    "lay_chuoi_thoi_gian_tieu_hao",
]
