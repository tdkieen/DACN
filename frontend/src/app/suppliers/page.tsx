"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { NhaCungCapWithQuotations } from "@/types";
import { Search, Star, Clock, Phone, Mail, MapPin, ChevronDown, ChevronUp } from "lucide-react";

export default function SuppliersPage() {
  const [search, setSearch] = useState("");
  const [expandedSupplier, setExpandedSupplier] = useState<string | number | null>(null);

  const { data: suppliers = [], isLoading, isError, refetch } = useQuery<NhaCungCapWithQuotations[]>({
    queryKey: ["suppliers", search],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      const res = await api.get<NhaCungCapWithQuotations[]>("/suppliers", { params });
      return res.data;
    },
  });

  const toggleExpand = (id: string | number) => {
    setExpandedSupplier((prev) => (prev === id ? null : id));
  };

  return (
    <>
      <PageHeader
        title="Nhà cung cấp & Báo giá"
        description="Thông tin đối tác cung ứng, lead time, độ uy tín và bảng báo giá đa tiêu chuẩn."
      />

      <Card className="mb-6">
        <CardContent className="pt-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Tìm tên nhà cung cấp..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm rounded-md border bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Làm mới danh sách
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4">
        {isLoading ? (
          <div className="py-12 text-center text-muted-foreground">Đang tải danh sách nhà cung cấp...</div>
        ) : isError ? (
          <div className="py-12 text-center text-danger">
            Không thể tải dữ liệu nhà cung cấp từ Backend API. Vui lòng kiểm tra server FastAPI.
          </div>
        ) : suppliers.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground">Không tìm thấy nhà cung cấp nào.</div>
        ) : (
          suppliers.map((sup) => {
            const isExpanded = expandedSupplier === sup.ma_nha_cung_cap;
            return (
              <Card key={sup.ma_nha_cung_cap} className="overflow-hidden transition-all">
                <CardHeader className="cursor-pointer hover:bg-muted/20" onClick={() => toggleExpand(sup.ma_nha_cung_cap)}>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-base font-bold text-foreground">
                          {sup.ten_nha_cung_cap}
                        </CardTitle>
                        <Badge variant="default" className="text-xs">
                          {sup.quotations?.length ?? 0} mặt hàng
                        </Badge>
                      </div>
                      <div className="flex flex-wrap items-center gap-4 mt-2 text-xs text-muted-foreground">
                        {sup.nguoi_lien_he && (
                          <span>Liên hệ: <strong className="text-foreground">{sup.nguoi_lien_he}</strong></span>
                        )}
                        {sup.sdt && (
                          <span className="flex items-center gap-1"><Phone className="h-3 w-3" /> {sup.sdt}</span>
                        )}
                        {sup.email && (
                          <span className="flex items-center gap-1"><Mail className="h-3 w-3" /> {sup.email}</span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1.5 text-xs bg-amber-500/10 text-amber-700 px-2.5 py-1 rounded-md font-medium">
                        <Star className="h-3.5 w-3.5 fill-amber-500 text-amber-500" />
                        Uy tín: {sup.diem_uy_tin}/5.0
                      </div>
                      <div className="flex items-center gap-1.5 text-xs bg-primary/10 text-primary px-2.5 py-1 rounded-md font-medium">
                        <Clock className="h-3.5 w-3.5" />
                        Lead time: {sup.thoi_gian_giao_du_kien} ngày
                      </div>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                </CardHeader>

                {isExpanded && (
                  <CardContent className="border-t bg-muted/10 pt-4">
                    {sup.dia_chi && (
                      <div className="text-xs text-muted-foreground flex items-center gap-1 mb-4">
                        <MapPin className="h-3.5 w-3.5 text-primary" />
                        Địa chỉ: {sup.dia_chi}
                      </div>
                    )}

                    <h4 className="text-xs font-semibold uppercase text-muted-foreground mb-2">
                      Bảng báo giá các nguyên vật liệu cung ứng ({sup.quotations?.length ?? 0})
                    </h4>
                    {(!sup.quotations || sup.quotations.length === 0) ? (
                      <div className="text-xs text-muted-foreground py-3">Chưa có báo giá nào cho NCC này.</div>
                    ) : (
                      <div className="overflow-x-auto rounded border bg-background">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="border-b bg-muted/40 font-semibold text-muted-foreground">
                              <th className="py-2.5 px-3">Nguyên liệu</th>
                              <th className="py-2.5 px-3 text-right">Đơn giá</th>
                              <th className="py-2.5 px-3 text-right">Đặt tối thiểu (MOQ)</th>
                              <th className="py-2.5 px-3 text-right">Lead time</th>
                              <th className="py-2.5 px-3 text-right">Cập nhật lần cuối</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {sup.quotations.map((q) => (
                              <tr key={`${q.ma_nha_cung_cap}-${q.ma_nguyen_lieu}`} className="hover:bg-muted/30">
                                <td className="py-2.5 px-3 font-medium text-foreground">
                                  {q.ten_nguyen_lieu ?? `Nguyên liệu #${q.ma_nguyen_lieu}`}
                                </td>
                                <td className="py-2.5 px-3 text-right font-semibold text-primary">
                                  {q.don_gia.toLocaleString("vi-VN")} đ
                                </td>
                                <td className="py-2.5 px-3 text-right">{q.so_luong_dat_toi_thieu}</td>
                                <td className="py-2.5 px-3 text-right">{q.thoi_gian_giao_hang} ngày</td>
                                <td className="py-2.5 px-3 text-right text-muted-foreground">
                                  {q.ngay_cap_nhat_gia ? new Date(q.ngay_cap_nhat_gia).toLocaleDateString("vi-VN") : "Gần đây"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </CardContent>
                )}
              </Card>
            );
          })
        )}
      </div>
    </>
  );
}
