import {
  LayoutDashboard,
  Package,
  Truck,
  ClipboardCheck,
  FlaskConical,
  type LucideIcon,
} from "lucide-react";
import type { TrangThaiPhieu } from "@/types";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Tổng quan", icon: LayoutDashboard },
  { href: "/inventory", label: "Tồn kho & Lô hàng", icon: Package },
  { href: "/bom", label: "Định mức & Dữ liệu BOM", icon: FlaskConical },
  { href: "/suppliers", label: "Nhà cung cấp", icon: Truck },
  { href: "/proposals", label: "Đề xuất mua hàng", icon: ClipboardCheck },
];

export const TRANG_THAI_PHIEU_LABEL: Record<TrangThaiPhieu, string> = {
  CHO_DUYET: "Chờ duyệt",
  DA_DUYET: "Đã duyệt",
  TU_CHOI: "Từ chối",
  DA_SUA: "Đã sửa",
};
