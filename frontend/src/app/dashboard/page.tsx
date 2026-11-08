"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/shared/page-header";
import { StatCard } from "@/components/shared/stat-card";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { DashboardStats, AlertItem, MonthlyTrend, ForecastSummary } from "@/types";
import { AlertCircle, AlertTriangle, ShieldCheck, TrendingUp, Calendar, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const { data: stats, isLoading: loadingStats } = useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: async () => {
      const res = await api.get<DashboardStats>("/dashboard/stats");
      return res.data;
    },
  });

  const { data: alerts = [] } = useQuery<AlertItem[]>({
    queryKey: ["dashboard-alerts"],
    queryFn: async () => {
      const res = await api.get<AlertItem[]>("/dashboard/alerts");
      return res.data;
    },
  });

  const { data: trends = [] } = useQuery<MonthlyTrend[]>({
    queryKey: ["dashboard-trends"],
    queryFn: async () => {
      const res = await api.get<MonthlyTrend[]>("/dashboard/trends");
      return res.data;
    },
  });

  const { data: forecast = [] } = useQuery<ForecastSummary[]>({
    queryKey: ["dashboard-forecast"],
    queryFn: async () => {
      const res = await api.get<ForecastSummary[]>("/dashboard/forecast-summary");
      return res.data;
    },
  });

  return (
    <>
      <PageHeader
        title="Tổng quan hoạt động"
        description="Giám sát tồn kho thời gian thực, cảnh báo chuỗi cung ứng và dự báo nhu cầu tiêu thụ."
      />

      {/* 4 Thẻ chỉ số tổng quan */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4 mb-6">
        <StatCard
          title="Nguyên liệu đang dùng"
          value={loadingStats ? "..." : (stats?.tong_nguyen_lieu_dang_dung ?? 0).toString()}
          hint={`Tỷ lệ an toàn: ${stats?.ty_le_an_toan ?? 0}%`}
        />
        <StatCard
          title="Nguy cơ thiếu hàng"
          value={loadingStats ? "..." : (stats?.nguy_co_thieu_hang ?? 0).toString()}
          hint="Tồn kho ≤ Điểm đặt hàng ROP"
          className={stats && stats.nguy_co_thieu_hang > 0 ? "border-danger/40 bg-danger/5" : ""}
        />
        <StatCard
          title="Nguy cơ tồn dư đọng vốn"
          value={loadingStats ? "..." : (stats?.nguy_co_ton_du ?? 0).toString()}
          hint="Tồn kho > Mức tối đa hoặc > 3 lần tuần"
          className={stats && stats.nguy_co_ton_du > 0 ? "border-amber-500/40 bg-amber-50/50" : ""}
        />
        <StatCard
          title="Phiếu đề xuất chờ duyệt"
          value={loadingStats ? "..." : (stats?.phieu_cho_duyet ?? 0).toString()}
          hint="AI Agent đã tạo, chờ Quản lý duyệt"
          className={stats && stats.phieu_cho_duyet > 0 ? "border-primary/40 bg-primary/5" : ""}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3 mb-6">
        {/* Bảng cảnh báo chủ động */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-danger" />
                <CardTitle>Cảnh báo tồn kho & Chuỗi cung ứng ({alerts.length})</CardTitle>
              </div>
              <Link href="/inventory" className="text-xs text-primary font-medium flex items-center gap-1 hover:underline">
                Xem kho <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {alerts.length === 0 ? (
              <div className="flex items-center gap-2 text-sm text-emerald-600 py-4">
                <ShieldCheck className="h-5 w-5" />
                Tất cả nguyên vật liệu đều ở trạng thái an toàn, không có cảnh báo nào!
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((al, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-md border text-sm flex items-start justify-between gap-3 ${
                      al.muc_do === "DANGER"
                        ? "border-danger/30 bg-danger/5"
                        : "border-amber-500/30 bg-amber-500/5"
                    }`}
                  >
                    <div className="flex items-start gap-2.5">
                      {al.muc_do === "DANGER" ? (
                        <AlertCircle className="h-4 w-4 text-danger mt-0.5 shrink-0" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                      )}
                      <div>
                        <div className="font-semibold text-foreground">
                          {al.ten_nguyen_lieu}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {al.noi_dung}
                        </div>
                      </div>
                    </div>
                    {al.so_luong_can_bo_sung && al.so_luong_can_bo_sung > 0 ? (
                      <Badge variant="danger" className="shrink-0 font-mono">
                        Cần +{al.so_luong_can_bo_sung} {al.don_vi_tinh}
                      </Badge>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Tổng giá trị tồn kho & Tỷ lệ */}
        <Card>
          <CardHeader>
            <CardTitle>Giá trị tồn kho ước tính</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary font-mono">
              {(stats?.tong_gia_tri_ton_kho ?? 0).toLocaleString("vi-VN")} đ
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Định giá theo đơn giá báo giá chuẩn hiện tại.
            </p>

            <div className="mt-6 border-t pt-4 space-y-3 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Tỷ lệ kho an toàn:</span>
                <strong className="text-emerald-600 font-semibold">{stats?.ty_le_an_toan ?? 0}%</strong>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Mặt hàng nguy cơ thiếu:</span>
                <strong className="text-danger font-semibold">{stats?.nguy_co_thieu_hang ?? 0} món</strong>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Mặt hàng tồn dư:</span>
                <strong className="text-amber-600 font-semibold">{stats?.nguy_co_ton_du ?? 0} món</strong>
              </div>
            </div>

            <div className="mt-6">
              <Link href="/proposals">
                <button className="w-full py-2 px-3 text-xs font-semibold rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors">
                  Xem đề xuất AI mua hàng ({stats?.phieu_cho_duyet ?? 0})
                </button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Biểu đồ xu hướng 12 tháng & Dự báo 7 ngày */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              <CardTitle>Xu hướng tiêu thụ nguyên liệu 12 tháng</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {trends.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground">Đang tải xu hướng...</div>
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-4 text-xs font-semibold text-muted-foreground border-b pb-2">
                  <span>Tháng</span>
                  <span className="text-right">Tiêu hao (kg)</span>
                  <span className="text-right col-span-2">Chi phí ước tính</span>
                </div>
                {trends.slice(-6).map((t, idx) => (
                  <div key={idx} className="grid grid-cols-4 text-xs py-1.5 items-center hover:bg-muted/30">
                    <span className="font-medium">{t.thang}</span>
                    <span className="text-right font-mono font-medium">{t.tong_tieu_hao_kg} kg</span>
                    <span className="text-right col-span-2 font-mono text-muted-foreground">
                      {t.chi_phi_uoc_tinh.toLocaleString("vi-VN")} đ
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-primary" />
              <CardTitle>Dự báo nhu cầu 7 ngày tới (AI Prophet/XGBoost)</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {forecast.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground">Đang tải dữ liệu dự báo...</div>
            ) : (
              <div className="space-y-3">
                {forecast.slice(0, 4).map((fc) => (
                  <div key={fc.ma_nguyen_lieu} className="border-b pb-2 last:border-0 last:pb-0">
                    <div className="flex justify-between items-center text-xs mb-1">
                      <span className="font-semibold text-foreground">{fc.ten_nguyen_lieu}</span>
                      <span className="text-muted-foreground">
                        Tổng tuần: <strong className="text-primary font-mono">{fc.tong_nhu_cau_7ngay} {fc.don_vi_tinh}</strong> (TB: {fc.trung_binh_ngay}/ngày)
                      </span>
                    </div>
                    <div className="flex gap-1 overflow-x-auto py-1">
                      {fc.du_lieu_7ngay.map((d, dIdx) => (
                        <div key={dIdx} className="flex-1 bg-muted/40 rounded px-1.5 py-1 text-center min-w-[38px]">
                          <div className="text-[10px] text-muted-foreground">{d.ngay}</div>
                          <div className="text-xs font-mono font-semibold text-foreground">{d.so_luong}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
