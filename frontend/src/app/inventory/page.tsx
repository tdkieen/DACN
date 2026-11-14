"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/shared/query-state";
import type { NguyenLieuStatus, LoHangOut, GiaoDichKhoOut } from "@/types";
import {
  Search,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Package,
  CalendarClock,
  History,
  PlusCircle,
} from "lucide-react";

type InventoryTab = "STOCK" | "BATCHES" | "TRANSACTIONS";

export default function InventoryPage() {
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<InventoryTab>("STOCK");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [expiringOnly, setExpiringOnly] = useState<boolean>(false);
  const [txTypeFilter, setTxTypeFilter] = useState<string>("ALL");

  // Form tạo giao dịch kho nhanh (Kiểm kê / Hao hụt / Nhập)
  const [txIngredientId, setTxIngredientId] = useState<number>(1);
  const [txType, setTxType] = useState<string>("KIEM_KE");
  const [txQty, setTxQty] = useState<string>("15");
  const [txNote, setTxNote] = useState<string>("");

  // Form nhập lô hàng mới
  const [batchIngId, setBatchIngId] = useState<number>(1);
  const [batchCode, setBatchCode] = useState<string>("LOT-202611-NEW");
  const [batchQty, setBatchQty] = useState<string>("25");
  const [batchPrice, setBatchPrice] = useState<string>("145000");
  const [batchExpiry, setBatchExpiry] = useState<string>("2027-05-15");

  const { data: ingredients = [], isLoading, isError, refetch } = useQuery<NguyenLieuStatus[]>({
    queryKey: ["ingredients", search, statusFilter],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (statusFilter !== "ALL") params.tinh_trang = statusFilter;
      const res = await api.get<NguyenLieuStatus[]>("/ingredients", { params });
      return res.data;
    },
  });

  const { data: batches = [], isLoading: loadingBatches } = useQuery<LoHangOut[]>({
    queryKey: ["inventory-batches", expiringOnly],
    queryFn: async () => {
      const res = await api.get<LoHangOut[]>("/inventory/batches", {
        params: { canh_bao_het_han: expiringOnly },
      });
      return res.data;
    },
  });

  const { data: transactions = [], isLoading: loadingTxs } = useQuery<GiaoDichKhoOut[]>({
    queryKey: ["inventory-transactions", txTypeFilter],
    queryFn: async () => {
      const params: Record<string, string | number> = { limit: 50 };
      if (txTypeFilter !== "ALL") params.loai_giao_dich = txTypeFilter;
      const res = await api.get<GiaoDichKhoOut[]>("/inventory/transactions", { params });
      return res.data;
    },
  });

  const createTxMutation = useMutation({
    mutationFn: async () => {
      await api.post("/inventory/transactions", {
        ma_nguyen_lieu: txIngredientId,
        loai_giao_dich: txType,
        so_luong: Number(txQty),
        ma_tham_chieu: `MAN-${txType}-${Date.now().toString().slice(-4)}`,
        ghi_chu: txNote || `Ghi nhận ${txType} trực tiếp từ trang Quản lý kho`,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ingredients"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-batches"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-transactions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      setTxNote("");
    },
  });

  const createBatchMutation = useMutation({
    mutationFn: async () => {
      const q = Number(batchQty);
      await api.post("/inventory/batches", {
        ma_nguyen_lieu: batchIngId,
        ma_lo_nha_cung_cap: batchCode,
        so_luong_nhap: q,
        so_luong_con_lai: q,
        han_su_dung: batchExpiry || null,
        don_gia_nhap: Number(batchPrice),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ingredients"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-batches"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-transactions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  return (
    <>
      <PageHeader
        title="Quản lý tồn kho, Lô hàng (FEFO) & Biến động kho"
        description="Theo dõi tồn kho thực tế, điểm đặt hàng lại (ROP), hạn sử dụng từng lô hàng và lịch sử xuất - nhập - kiểm kê."
      />

      {/* Thanh chuyển đổi 3 Tab */}
      <div className="flex flex-wrap gap-2 mb-6 border-b pb-3">
        <Button
          variant={activeTab === "STOCK" ? "default" : "outline"}
          size="sm"
          onClick={() => setActiveTab("STOCK")}
          className="gap-1.5"
        >
          <Package className="h-4 w-4" /> Danh mục Tồn kho & ROP ({ingredients.length})
        </Button>
        <Button
          variant={activeTab === "BATCHES" ? "default" : "outline"}
          size="sm"
          onClick={() => setActiveTab("BATCHES")}
          className="gap-1.5"
        >
          <CalendarClock className="h-4 w-4" /> Lô hàng & Hạn sử dụng FEFO ({batches.length})
        </Button>
        <Button
          variant={activeTab === "TRANSACTIONS" ? "default" : "outline"}
          size="sm"
          onClick={() => setActiveTab("TRANSACTIONS")}
          className="gap-1.5"
        >
          <History className="h-4 w-4" /> Nhật ký Biến động Kho ({transactions.length})
        </Button>
      </div>

      {/* TAB 1: DANH MỤC TỒN KHO & ĐIỂM ROP */}
      {activeTab === "STOCK" && (
        <>
          <Card className="mb-6">
            <CardContent className="pt-5">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Tìm tên nguyên liệu..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 text-sm rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant={statusFilter === "ALL" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setStatusFilter("ALL")}
                  >
                    Tất cả
                  </Button>
                  <Button
                    variant={statusFilter === "NGUY_CO_THIEU" ? "danger" : "outline"}
                    size="sm"
                    onClick={() => setStatusFilter("NGUY_CO_THIEU")}
                  >
                    Nguy cơ thiếu (ROP)
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className={
                      statusFilter === "TON_DU"
                        ? "border-amber-500 text-amber-600 bg-amber-50"
                        : ""
                    }
                    onClick={() => setStatusFilter("TON_DU")}
                  >
                    Tồn dư đọng vốn
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className={
                      statusFilter === "AN_TOAN"
                        ? "border-emerald-500 text-emerald-600 bg-emerald-50"
                        : ""
                    }
                    onClick={() => setStatusFilter("AN_TOAN")}
                  >
                    An toàn
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Danh sách nguyên vật liệu ({ingredients.length})</CardTitle>
                <Button variant="outline" size="sm" onClick={() => refetch()}>
                  Làm mới
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="py-12 text-center text-muted-foreground">
                  Đang tải dữ liệu tồn kho...
                </div>
              ) : isError ? (
                <ErrorNotice onRetry={() => refetch()} />
              ) : ingredients.length === 0 ? (
                <div className="py-12 text-center text-muted-foreground">
                  Không tìm thấy nguyên liệu phù hợp bộ lọc.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b text-xs font-semibold uppercase text-muted-foreground bg-muted/40">
                        <th className="py-3 px-4">Tên nguyên liệu</th>
                        <th className="py-3 px-4">Danh mục</th>
                        <th className="py-3 px-4 text-right">Tồn hiện tại</th>
                        <th className="py-3 px-4 text-right">Điểm ROP</th>
                        <th className="py-3 px-4 text-right">Mức an toàn</th>
                        <th className="py-3 px-4 text-right">Nhu cầu 7 ngày</th>
                        <th className="py-3 px-4 text-right">Cần bổ sung</th>
                        <th className="py-3 px-4 text-center">Trạng thái</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {ingredients.map((item) => (
                        <tr key={item.ma_nguyen_lieu} className="hover:bg-muted/30 transition-colors">
                          <td className="py-3.5 px-4 font-medium">
                            {item.ten_nguyen_lieu}
                            {item.thong_bao_canh_bao && (
                              <div className="text-xs text-danger font-normal mt-0.5">
                                {item.thong_bao_canh_bao}
                              </div>
                            )}
                          </td>
                          <td className="py-3.5 px-4 text-muted-foreground">
                            {item.danh_muc ?? "Chung"}
                          </td>
                          <td className="py-3.5 px-4 text-right font-semibold">
                            {item.ton_kho_hien_tai}{" "}
                            <span className="text-xs font-normal text-muted-foreground">
                              {item.don_vi_tinh}
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-right font-mono text-primary font-medium">
                            {item.diem_dat_hang_lai_rop} {item.don_vi_tinh}
                          </td>
                          <td className="py-3.5 px-4 text-right text-muted-foreground font-mono">
                            {item.muc_ton_an_toan} {item.don_vi_tinh}
                          </td>
                          <td className="py-3.5 px-4 text-right font-mono text-xs">
                            {item.nhu_cau_du_bao_7ngay} {item.don_vi_tinh}
                          </td>
                          <td className="py-3.5 px-4 text-right font-medium">
                            {item.so_luong_can_bo_sung > 0 ? (
                              <span className="text-danger font-bold">
                                +{item.so_luong_can_bo_sung} {item.don_vi_tinh}
                              </span>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </td>
                          <td className="py-3.5 px-4 text-center">
                            {item.tinh_trang === "NGUY_CO_THIEU" && (
                              <Badge variant="danger" className="gap-1">
                                <ShieldAlert className="h-3 w-3" /> Nguy cơ thiếu
                              </Badge>
                            )}
                            {item.tinh_trang === "TON_DU" && (
                              <Badge variant="warning" className="gap-1">
                                <AlertTriangle className="h-3 w-3" /> Tồn dư
                              </Badge>
                            )}
                            {item.tinh_trang === "AN_TOAN" && (
                              <Badge variant="success" className="gap-1">
                                <CheckCircle2 className="h-3 w-3" /> An toàn
                              </Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* TAB 2: QUẢN LÝ LÔ HÀNG & HẠN SỬ DỤNG FEFO */}
      {activeTab === "BATCHES" && (
        <div className="grid gap-6 lg:grid-cols-12">
          <Card className="lg:col-span-4">
            <CardHeader className="border-b">
              <div className="flex items-center gap-2">
                <PlusCircle className="h-4 w-4 text-primary" />
                <CardTitle>Nhập Lô Hàng Mới Vào Kho</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-4 space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Nguyên liệu nhập kho</label>
                <select
                  value={batchIngId}
                  onChange={(e) => setBatchIngId(Number(e.target.value))}
                  className="w-full border rounded px-2.5 py-2 bg-background"
                >
                  {ingredients.map((ing) => (
                    <option key={ing.ma_nguyen_lieu} value={Number(ing.ma_nguyen_lieu)}>
                      #{ing.ma_nguyen_lieu} - {ing.ten_nguyen_lieu} ({ing.don_vi_tinh})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold block mb-1">Mã lô Nhà cung cấp</label>
                <input
                  type="text"
                  value={batchCode}
                  onChange={(e) => setBatchCode(e.target.value)}
                  className="w-full border rounded px-2.5 py-2 bg-background font-mono"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-semibold block mb-1">Số lượng nhập</label>
                  <input
                    type="number"
                    min={1}
                    value={batchQty}
                    onChange={(e) => setBatchQty(e.target.value)}
                    className="w-full border rounded px-2.5 py-2 bg-background font-mono"
                  />
                </div>
                <div>
                  <label className="font-semibold block mb-1">Đơn giá nhập (đ)</label>
                  <input
                    type="number"
                    min={0}
                    value={batchPrice}
                    onChange={(e) => setBatchPrice(e.target.value)}
                    className="w-full border rounded px-2.5 py-2 bg-background font-mono"
                  />
                </div>
              </div>
              <div>
                <label className="font-semibold block mb-1">Hạn sử dụng (FEFO)</label>
                <input
                  type="date"
                  value={batchExpiry}
                  onChange={(e) => setBatchExpiry(e.target.value)}
                  className="w-full border rounded px-2.5 py-2 bg-background font-mono"
                />
              </div>
              <Button
                className="w-full"
                size="sm"
                onClick={() => createBatchMutation.mutate()}
                disabled={createBatchMutation.isPending}
              >
                {createBatchMutation.isPending ? "Đang lưu lô hàng..." : "Nhập Kho & Cộng Tồn Thực Tế"}
              </Button>
            </CardContent>
          </Card>

          <Card className="lg:col-span-8">
            <CardHeader className="border-b">
              <div className="flex items-center justify-between">
                <CardTitle>Danh sách Lô hàng theo thứ tự FEFO ({batches.length})</CardTitle>
                <Button
                  variant={expiringOnly ? "danger" : "outline"}
                  size="sm"
                  onClick={() => setExpiringOnly(!expiringOnly)}
                >
                  {expiringOnly ? "Đang lọc: Sắp hết hạn (≤ 7 ngày)" : "Chỉ hiện lô sắp hết hạn"}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              {loadingBatches ? (
                <div className="py-8 text-center text-xs text-muted-foreground">
                  Đang tải danh sách lô hàng...
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b bg-muted/40 font-semibold text-muted-foreground">
                        <th className="py-2.5 px-3">Mã lô NCC</th>
                        <th className="py-2.5 px-3">Nguyên liệu</th>
                        <th className="py-2.5 px-3 text-right">SL Nhập</th>
                        <th className="py-2.5 px-3 text-right">SL Còn lại</th>
                        <th className="py-2.5 px-3">Hạn sử dụng</th>
                        <th className="py-2.5 px-3 text-center">Trạng thái HSD</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {batches.map((b) => (
                        <tr key={b.ma_lo_hang} className="hover:bg-muted/20">
                          <td className="py-2.5 px-3 font-mono font-semibold">
                            {b.ma_lo_nha_cung_cap}
                          </td>
                          <td className="py-2.5 px-3 font-medium">{b.ten_nguyen_lieu}</td>
                          <td className="py-2.5 px-3 text-right font-mono">{b.so_luong_nhap}</td>
                          <td className="py-2.5 px-3 text-right font-mono font-bold text-primary">
                            {b.so_luong_con_lai}
                          </td>
                          <td className="py-2.5 px-3 font-mono">{b.han_su_dung}</td>
                          <td className="py-2.5 px-3 text-center">
                            {b.canh_bao_het_han ? (
                              <Badge variant="danger">
                                Sắp hết hạn ({b.so_ngay_con_han} ngày)
                              </Badge>
                            ) : (
                              <Badge variant="success">
                                Còn {b.so_ngay_con_han} ngày
                              </Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 3: NHẬT KÝ BIẾN ĐỘNG KHO (GIAO_DICH_KHO) */}
      {activeTab === "TRANSACTIONS" && (
        <div className="grid gap-6 lg:grid-cols-12">
          <Card className="lg:col-span-4">
            <CardHeader className="border-b">
              <CardTitle>Ghi nhận Kiểm kê / Xuất - Nhập Kho</CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3 text-xs">
              <div>
                <label className="font-semibold block mb-1">Nguyên liệu</label>
                <select
                  value={txIngredientId}
                  onChange={(e) => setTxIngredientId(Number(e.target.value))}
                  className="w-full border rounded px-2.5 py-2 bg-background"
                >
                  {ingredients.map((ing) => (
                    <option key={ing.ma_nguyen_lieu} value={Number(ing.ma_nguyen_lieu)}>
                      #{ing.ma_nguyen_lieu} - {ing.ten_nguyen_lieu} (Tồn: {ing.ton_kho_hien_tai}{" "}
                      {ing.don_vi_tinh})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold block mb-1">Loại giao dịch</label>
                <select
                  value={txType}
                  onChange={(e) => setTxType(e.target.value)}
                  className="w-full border rounded px-2.5 py-2 bg-background font-medium"
                >
                  <option value="KIEM_KE">Kiểm kê (Cập nhật tồn kho thực tế)</option>
                  <option value="NHAP">Nhập kho (Nhập bổ sung)</option>
                  <option value="XUAT_BAN">Xuất bán pha chế (Trừ lô hết hạn trước)</option>
                  <option value="HAO_HUT">Hao hụt / Hủy hỏng (Trừ lô hết hạn trước)</option>
                </select>
              </div>
              <div>
                <label className="font-semibold block mb-1">Số lượng</label>
                <input
                  type="number"
                  step="0.1"
                  min={0}
                  value={txQty}
                  onChange={(e) => setTxQty(e.target.value)}
                  className="w-full border rounded px-2.5 py-2 bg-background font-mono"
                />
              </div>
              <div>
                <label className="font-semibold block mb-1">Ghi chú lý do</label>
                <input
                  type="text"
                  placeholder="VD: Kiểm kê cuối ca tối..."
                  value={txNote}
                  onChange={(e) => setTxNote(e.target.value)}
                  className="w-full border rounded px-2.5 py-2 bg-background"
                />
              </div>
              <Button
                className="w-full"
                size="sm"
                onClick={() => createTxMutation.mutate()}
                disabled={createTxMutation.isPending}
              >
                {createTxMutation.isPending ? "Đang ghi nhận..." : "Ghi nhận Giao dịch Kho"}
              </Button>
            </CardContent>
          </Card>

          <Card className="lg:col-span-8">
            <CardHeader className="border-b">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <CardTitle>Lịch sử Giao dịch Xuất - Nhập - Kiểm kê ({transactions.length})</CardTitle>
                <div className="flex flex-wrap gap-1.5">
                  {["ALL", "XUAT_BAN", "NHAP", "KIEM_KE", "HAO_HUT"].map((t) => (
                    <Button
                      key={t}
                      variant={txTypeFilter === t ? "default" : "outline"}
                      size="sm"
                      onClick={() => setTxTypeFilter(t)}
                      className="text-xs h-7 px-2.5"
                    >
                      {t === "ALL" ? "Tất cả" : t}
                    </Button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-4">
              {loadingTxs ? (
                <div className="py-8 text-center text-xs text-muted-foreground">
                  Đang tải lịch sử giao dịch kho...
                </div>
              ) : (
                <div className="overflow-x-auto max-h-[460px]">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b bg-muted/40 font-semibold text-muted-foreground">
                        <th className="py-2 px-3">Mã tham chiếu</th>
                        <th className="py-2 px-3">Nguyên liệu</th>
                        <th className="py-2 px-3 text-center">Loại</th>
                        <th className="py-2 px-3 text-right">Số lượng</th>
                        <th className="py-2 px-3">Ghi chú</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {transactions.map((tx) => (
                        <tr key={tx.ma_giao_dich} className="hover:bg-muted/20">
                          <td className="py-2 px-3 font-mono text-[11px]">
                            {tx.ma_tham_chieu ?? `#${tx.ma_giao_dich}`}
                          </td>
                          <td className="py-2 px-3 font-medium">{tx.ten_nguyen_lieu}</td>
                          <td className="py-2 px-3 text-center">
                            <Badge
                              variant={
                                tx.loai_giao_dich === "NHAP"
                                  ? "success"
                                  : tx.loai_giao_dich === "HAO_HUT"
                                    ? "danger"
                                    : "default"
                              }
                            >
                              {tx.loai_giao_dich}
                            </Badge>
                          </td>
                          <td className="py-2 px-3 text-right font-mono font-semibold">
                            {tx.so_luong} {tx.don_vi_tinh}
                          </td>
                          <td className="py-2 px-3 text-muted-foreground">{tx.ghi_chu}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}
