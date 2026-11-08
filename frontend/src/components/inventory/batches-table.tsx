"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorNotice, LoadingState } from "@/components/shared/query-state";
import { formatDate, formatNumber } from "@/lib/utils";
import type { LoHangStatus } from "@/types";

function ExpiryBadge({ batch }: { batch: LoHangStatus }) {
  const d = batch.so_ngay_con_han;
  if (d === null || d === undefined) return <Badge>Không có HSD</Badge>;
  if (d < 0) return <Badge variant="danger" className="whitespace-nowrap">Đã hết hạn</Badge>;
  if (batch.canh_bao_het_han) return <Badge variant="warning" className="whitespace-nowrap">Sắp hết hạn</Badge>;
  return <Badge variant="success" className="whitespace-nowrap">Còn hạn</Badge>;
}

export function BatchesTable() {
  const [onlyExpiring, setOnlyExpiring] = useState(false);

  const { data = [], isLoading, isError, refetch } = useQuery<LoHangStatus[]>({
    queryKey: ["batches", onlyExpiring],
    queryFn: async () => {
      const res = await api.get<LoHangStatus[]>("/inventory/batches", {
        params: onlyExpiring ? { canh_bao_het_han: true } : {},
      });
      return res.data;
    },
  });

  return (
    <>
      <label className="mb-4 inline-flex cursor-pointer items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={onlyExpiring}
          onChange={(e) => setOnlyExpiring(e.target.checked)}
          className="h-4 w-4 accent-primary"
        />
        Chỉ hiện lô sắp hoặc đã hết hạn
      </label>

      {isLoading ? (
        <LoadingState label="Đang tải lô hàng" />
      ) : isError ? (
        <ErrorNotice onRetry={() => refetch()} />
      ) : data.length === 0 ? (
        <EmptyState message={onlyExpiring ? "Không có lô hàng nào sắp hết hạn." : "Chưa có lô hàng nào."} />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b bg-muted/40 text-xs font-semibold uppercase text-muted-foreground">
                <th className="px-4 py-3">Nguyên liệu</th>
                <th className="px-4 py-3">Mã lô NCC</th>
                <th className="px-4 py-3">Ngày nhập kho</th>
                <th className="px-4 py-3 text-right">Nhập / Còn lại</th>
                <th className="px-4 py-3">Hạn sử dụng</th>
                <th className="px-4 py-3">Tình trạng</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.map((b) => (
                <tr key={b.ma_lo_hang} className="hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{b.ten_nguyen_lieu ?? `#${b.ma_nguyen_lieu}`}</td>
                  <td className="px-4 py-3 text-muted-foreground">{b.ma_lo_nha_cung_cap ?? "—"}</td>
                  <td className="px-4 py-3">{b.ngay_nhap_kho ? formatDate(b.ngay_nhap_kho) : "—"}</td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {formatNumber(b.so_luong_nhap)} / {formatNumber(b.so_luong_con_lai)}
                  </td>
                  <td className="px-4 py-3">
                    {b.han_su_dung ? formatDate(b.han_su_dung) : "—"}
                    {b.so_ngay_con_han !== null && b.so_ngay_con_han !== undefined && (
                      <span className="ml-2 text-xs text-muted-foreground">
                        ({b.so_ngay_con_han < 0 ? "quá " : "còn "}
                        {Math.abs(b.so_ngay_con_han)} ngày)
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3"><ExpiryBadge batch={b} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </>
  );
}
