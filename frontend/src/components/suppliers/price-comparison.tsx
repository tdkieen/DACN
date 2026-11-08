"use client";

import { useMemo, useState } from "react";
import { Star } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { formatDate, formatNumber, formatVND } from "@/lib/utils";
import type { NhaCungCapWithQuotations } from "@/types";

interface Row {
  key: string;
  ma_nguyen_lieu: string;
  ten_nguyen_lieu: string;
  ten_nha_cung_cap: string;
  don_gia: number;
  moq: number;
  lead: number;
  uy_tin: number;
  cap_nhat?: string | null;
}

/** So sánh báo giá của cùng một nguyên liệu giữa các nhà cung cấp. */
export function PriceComparison({ suppliers }: { suppliers: NhaCungCapWithQuotations[] }) {
  const [ingredientId, setIngredientId] = useState("ALL");

  const rows = useMemo<Row[]>(
    () =>
      suppliers.flatMap((s) =>
        (s.quotations ?? []).map((q) => ({
          key: `${q.ma_nha_cung_cap}-${q.ma_nguyen_lieu}`,
          ma_nguyen_lieu: String(q.ma_nguyen_lieu),
          ten_nguyen_lieu: q.ten_nguyen_lieu ?? `Nguyên liệu #${q.ma_nguyen_lieu}`,
          ten_nha_cung_cap: q.ten_nha_cung_cap ?? s.ten_nha_cung_cap,
          don_gia: q.don_gia,
          moq: q.so_luong_dat_toi_thieu,
          lead: q.thoi_gian_giao_hang,
          uy_tin: Number(s.diem_uy_tin),
          cap_nhat: q.ngay_cap_nhat_gia,
        })),
      ),
    [suppliers],
  );

  const ingredients = useMemo(() => {
    const m = new Map<string, string>();
    rows.forEach((r) => m.set(r.ma_nguyen_lieu, r.ten_nguyen_lieu));
    return Array.from(m.entries()).sort((a, b) => a[1].localeCompare(b[1], "vi"));
  }, [rows]);

  // Giá thấp nhất và số báo giá theo từng nguyên liệu
  const { lowest, count } = useMemo(() => {
    const low = new Map<string, number>();
    const cnt = new Map<string, number>();
    rows.forEach((r) => {
      cnt.set(r.ma_nguyen_lieu, (cnt.get(r.ma_nguyen_lieu) ?? 0) + 1);
      if (!low.has(r.ma_nguyen_lieu) || r.don_gia < (low.get(r.ma_nguyen_lieu) as number)) {
        low.set(r.ma_nguyen_lieu, r.don_gia);
      }
    });
    return { lowest: low, count: cnt };
  }, [rows]);

  const shown = useMemo(
    () =>
      rows
        .filter((r) => ingredientId === "ALL" || r.ma_nguyen_lieu === ingredientId)
        .sort((a, b) => a.ten_nguyen_lieu.localeCompare(b.ten_nguyen_lieu, "vi") || a.don_gia - b.don_gia),
    [rows, ingredientId],
  );

  if (rows.length === 0) return <EmptyState message="Chưa có báo giá nào." />;

  return (
    <>
      <div className="mb-4">
        <select
          value={ingredientId}
          onChange={(e) => setIngredientId(e.target.value)}
          aria-label="Lọc báo giá theo nguyên liệu"
          className="h-10 w-full rounded-md border bg-card px-3 text-sm sm:w-80"
        >
          <option value="ALL">Tất cả nguyên liệu</option>
          {ingredients.map(([id, name]) => (
            <option key={id} value={id}>{name}</option>
          ))}
        </select>
      </div>

      <Card className="overflow-x-auto">
        <table className="w-full min-w-[820px] text-left text-sm">
          <thead>
            <tr className="border-b bg-muted/40 text-xs font-semibold uppercase text-muted-foreground">
              <th className="px-4 py-3">Nguyên liệu</th>
              <th className="px-4 py-3">Nhà cung cấp</th>
              <th className="px-4 py-3 text-right">Đơn giá</th>
              <th className="px-4 py-3 text-right">Đặt tối thiểu</th>
              <th className="px-4 py-3 text-right">Giao hàng</th>
              <th className="px-4 py-3">Uy tín</th>
              <th className="px-4 py-3">Cập nhật giá</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {shown.map((r) => {
              const isLowest = (count.get(r.ma_nguyen_lieu) ?? 0) > 1 && lowest.get(r.ma_nguyen_lieu) === r.don_gia;
              return (
                <tr key={r.key} className="hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{r.ten_nguyen_lieu}</td>
                  <td className="px-4 py-3">{r.ten_nha_cung_cap}</td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {formatVND(r.don_gia)}
                    {isLowest && <Badge variant="success" className="ml-2 whitespace-nowrap">Giá thấp nhất</Badge>}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">{formatNumber(r.moq)}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{r.lead} ngày</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 tabular-nums">
                      <Star className="h-3.5 w-3.5 fill-warning text-warning" aria-hidden />
                      {r.uy_tin.toFixed(1)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{r.cap_nhat ? formatDate(r.cap_nhat) : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>
    </>
  );
}
