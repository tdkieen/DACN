"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ViewTabs } from "@/components/shared/view-tabs";
import { ErrorNotice } from "@/components/shared/query-state";
import { BatchesTable } from "@/components/inventory/batches-table";
import type { NguyenLieuStatus } from "@/types";
import { Search, AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";

type Tab = "nguyen-lieu" | "lo-hang";

export default function InventoryPage() {
  const [tab, setTab] = useState<Tab>("nguyen-lieu");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

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

  return (
    <>
      <PageHeader
        title="Quản lý tồn kho"
        description="Theo dõi tồn kho thực tế, ngưỡng an toàn và điểm đặt hàng lại (ROP) tự động."
      />

      <ViewTabs
        label="Chế độ xem tồn kho"
        value={tab}
        onChange={setTab}
        tabs={[
          { id: "nguyen-lieu", label: "Nguyên liệu" },
          { id: "lo-hang", label: "Lô hàng & hạn sử dụng" },
        ]}
      />

      {tab === "lo-hang" ? (
        <BatchesTable />
      ) : (
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
                variant={statusFilter === "TON_DU" ? "outline" : "outline"}
                size="sm"
                className={statusFilter === "TON_DU" ? "border-amber-500 text-amber-600 bg-amber-50" : ""}
                onClick={() => setStatusFilter("TON_DU")}
              >
                Tồn dư đọng vốn
              </Button>
              <Button
                variant={statusFilter === "AN_TOAN" ? "outline" : "outline"}
                size="sm"
                className={statusFilter === "AN_TOAN" ? "border-emerald-500 text-emerald-600 bg-emerald-50" : ""}
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
            <div className="py-12 text-center text-muted-foreground">Đang tải dữ liệu tồn kho...</div>
          ) : isError ? (
            <ErrorNotice onRetry={() => refetch()} />
          ) : ingredients.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">Không tìm thấy nguyên liệu phù hợp bộ lọc.</div>
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
                      <td className="py-3.5 px-4 text-muted-foreground">{item.danh_muc ?? "Chung"}</td>
                      <td className="py-3.5 px-4 text-right font-semibold">
                        {item.ton_kho_hien_tai} <span className="text-xs font-normal text-muted-foreground">{item.don_vi_tinh}</span>
                      </td>
                      <td className="py-3.5 px-4 text-right font-mono text-primary font-medium">
                        {item.diem_dat_hang_lai_rop} {item.don_vi_tinh}
                      </td>
                      <td className="py-3.5 px-4 text-right text-muted-foreground font-mono">
                        {item.muc_ton_an_toan} {item.don_vi_tinh}
                      </td>
                      <td className="py-3.5 px-4 text-right font-medium">
                        {item.so_luong_can_bo_sung > 0 ? (
                          <span className="text-danger font-bold">+{item.so_luong_can_bo_sung} {item.don_vi_tinh}</span>
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
    </>
  );
}
