"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type {
  MonAnKemDinhMucBom,
  BaoCaoChatLuongDuLieu,
  KetQuaMoPhongBom,
  ChuoiThoiGianNguyenLieu,
  LichSuBanHangPos,
} from "@/types";
import {
  FlaskConical,
  Play,
  RefreshCw,
  CheckCircle2,
  Database,
  TrendingUp,
  ShoppingBag,
  Sparkles,
} from "lucide-react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

export default function TrangDinhMucBom() {
  const queryClient = useQueryClient();

  const [maNguyenLieuChon, setMaNguyenLieuChon] = useState<number>(1);
  const [soNgayHienThi, setSoNgayHienThi] = useState<number>(60);
  const [soLuongLyTheoMon, setSoLuongLyTheoMon] = useState<Record<number, number>>({
    1: 40,
    2: 50,
    4: 25,
    7: 30,
  });
  const [ketQuaMoPhong, setKetQuaMoPhong] = useState<KetQuaMoPhongBom | null>(null);
  const [thongBaoTrangThai, setThongBaoTrangThai] = useState<string | null>(null);

  // 1. Báo cáo kiểm định chất lượng dữ liệu bán hàng POS
  const { data: baoCaoChatLuong, isLoading: dangTaiBaoCao } = useQuery<BaoCaoChatLuongDuLieu>({
    queryKey: ["bao-cao-chat-luong-bom"],
    queryFn: async () => {
      const res = await api.get<BaoCaoChatLuongDuLieu>("/dinh-muc-bom/bao-cao-chat-luong");
      return res.data;
    },
  });

  // 2. Danh sách thực đơn 12 món & định mức BOM
  const { data: danhSachMon = [], isLoading: dangTaiThucDon } = useQuery<MonAnKemDinhMucBom[]>({
    queryKey: ["thuc-don-dinh-muc-bom"],
    queryFn: async () => {
      const res = await api.get<MonAnKemDinhMucBom[]>("/dinh-muc-bom/thuc-don-bom");
      return res.data;
    },
  });

  // 3. Chuỗi thời gian tiêu hao nguyên liệu theo ngày
  const { data: chuoiThoiGian, isLoading: dangTaiChuoiThoiGian } = useQuery<ChuoiThoiGianNguyenLieu>({
    queryKey: ["chuoi-thoi-gian-nguyen-lieu", maNguyenLieuChon, soNgayHienThi],
    queryFn: async () => {
      const res = await api.get<ChuoiThoiGianNguyenLieu>(
        `/dinh-muc-bom/chuoi-thoi-gian/${maNguyenLieuChon}`,
        { params: { so_ngay: soNgayHienThi } }
      );
      return res.data;
    },
  });

  // 4. Lịch sử hóa đơn bán hàng POS sạch gần nhất
  const { data: lichSuPos = [] } = useQuery<LichSuBanHangPos[]>({
    queryKey: ["lich-su-ban-hang-pos"],
    queryFn: async () => {
      const res = await api.get<LichSuBanHangPos[]>("/dinh-muc-bom/lich-su-pos", {
        params: { gioi_han: 12 },
      });
      return res.data;
    },
  });

  // Chạy lại toàn bộ Quy trình làm sạch & bóc tách định mức BOM 12 tháng
  const chayQuyTrinhMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post<BaoCaoChatLuongDuLieu>("/dinh-muc-bom/chay-quy-trinh?so_ngay=365");
      return res.data;
    },
    onSuccess: (duLieu) => {
      queryClient.invalidateQueries({ queryKey: ["bao-cao-chat-luong-bom"] });
      queryClient.invalidateQueries({ queryKey: ["chuoi-thoi-gian-nguyen-lieu"] });
      queryClient.invalidateQueries({ queryKey: ["lich-su-ban-hang-pos"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-trends"] });
      setThongBaoTrangThai(
        `Đã thực thi thành công quy trình dữ liệu: làm sạch ${duLieu.tong_dong_sach}/${duLieu.tong_dong_tho} dòng bán hàng POS (${duLieu.ty_le_du_lieu_sach}%).`
      );
    },
  });

  // Mô phỏng bóc tách định mức BOM
  const moPhongMutation = useMutation({
    mutationFn: async () => {
      const danhSach = Object.entries(soLuongLyTheoMon)
        .filter(([, soLy]) => soLy > 0)
        .map(([ma_mon, so_luong_ly]) => ({
          ma_mon: Number(ma_mon),
          so_luong_ly: Number(so_luong_ly),
        }));
      const res = await api.post<KetQuaMoPhongBom>("/dinh-muc-bom/mo-phong-bom", {
        danh_sach_mon_ban: danhSach,
        cap_nhat_xuat_kho: false,
      });
      return res.data;
    },
    onSuccess: (duLieu) => {
      setKetQuaMoPhong(duLieu);
      setThongBaoTrangThai(
        `Đã mô phỏng bóc tách ${duLieu.tong_so_ly_ban} ly đồ uống thành ${duLieu.danh_sach_nguyen_lieu_tieu_hao.length} nguyên vật liệu tiêu hao.`
      );
    },
  });

  // Ghi nhận hóa đơn POS thực tế & trừ tồn kho lô hàng (Hết hạn trước xuất trước)
  const ghiNhanPosMutation = useMutation({
    mutationFn: async () => {
      const danhSach = Object.entries(soLuongLyTheoMon)
        .filter(([, soLy]) => soLy > 0)
        .map(([ma_mon, so_luong_ly]) => ({
          ma_mon: Number(ma_mon),
          so_luong_ly: Number(so_luong_ly),
        }));
      const res = await api.post<KetQuaMoPhongBom>("/dinh-muc-bom/hoa-don-pos", {
        ca_ban: "SANG",
        danh_sach_mon_ban: danhSach,
      });
      return res.data;
    },
    onSuccess: (duLieu) => {
      setKetQuaMoPhong(duLieu);
      queryClient.invalidateQueries({ queryKey: ["ingredients"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-alerts"] });
      queryClient.invalidateQueries({ queryKey: ["lich-su-ban-hang-pos"] });
      setThongBaoTrangThai(
        `Đã ghi nhận hóa đơn bán hàng POS (${duLieu.tong_so_ly_ban} ly), tự động bóc tách định mức BOM và trừ kho theo lô hết hạn trước!`
      );
    },
  });

  const capNhatSoLuongLy = (maMon: number, giaTri: string) => {
    const so = Math.max(0, Number(giaTri) || 0);
    setSoLuongLyTheoMon((truoc) => ({ ...truoc, [maMon]: so }));
  };

  return (
    <>
      <PageHeader
        title="Định mức Công thức Pha chế (BOM) & Làm sạch Dữ liệu Bán hàng"
        description="Thu thập, làm sạch dữ liệu bán hàng POS 12 tháng, bóc tách định mức (12 món đồ uống → 15 nguyên liệu) và trích xuất chuỗi thời gian tiêu hao."
      />

      {thongBaoTrangThai && (
        <div className="mb-6 p-3.5 rounded-md border border-emerald-500/30 bg-emerald-500/10 text-emerald-800 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span>{thongBaoTrangThai}</span>
          </div>
          <button
            onClick={() => setThongBaoTrangThai(null)}
            className="text-xs font-semibold underline ml-4"
          >
            Đóng
          </button>
        </div>
      )}

      {/* KHU VỰC 1: BÁO CÁO CHẤT LƯỢNG DỮ LIỆU & LÀM SẠCH BÁN HÀNG POS */}
      <Card className="mb-6">
        <CardHeader className="border-b bg-muted/15">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-primary" />
              <CardTitle>
                Báo cáo Kiểm định & Làm sạch Dữ liệu Bán hàng POS 12 Tháng
              </CardTitle>
            </div>
            <Button
              size="sm"
              onClick={() => chayQuyTrinhMutation.mutate()}
              disabled={chayQuyTrinhMutation.isPending}
              className="gap-1.5"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${chayQuyTrinhMutation.isPending ? "animate-spin" : ""}`} />
              {chayQuyTrinhMutation.isPending ? "Đang xử lý dữ liệu..." : "Chạy lại Quy trình Dữ liệu BOM"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-4">
          {dangTaiBaoCao || !baoCaoChatLuong ? (
            <div className="py-6 text-center text-xs text-muted-foreground">
              Đang tải báo cáo kiểm định chất lượng dữ liệu...
            </div>
          ) : (
            <>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
                <div className="p-3 rounded border bg-muted/20">
                  <div className="text-[11px] text-muted-foreground">Tổng dòng POS thô</div>
                  <div className="text-lg font-bold font-mono mt-0.5">
                    {baoCaoChatLuong.tong_dong_tho.toLocaleString("vi-VN")}
                  </div>
                </div>
                <div className="p-3 rounded border border-emerald-500/30 bg-emerald-500/5">
                  <div className="text-[11px] text-emerald-700 font-medium">Dòng dữ liệu sạch</div>
                  <div className="text-lg font-bold font-mono text-emerald-700 mt-0.5">
                    {baoCaoChatLuong.tong_dong_sach.toLocaleString("vi-VN")}{" "}
                    <span className="text-xs">({baoCaoChatLuong.ty_le_du_lieu_sach}%)</span>
                  </div>
                </div>
                <div className="p-3 rounded border bg-amber-500/5 border-amber-500/20">
                  <div className="text-[11px] text-amber-700">Đã khử trùng lặp</div>
                  <div className="text-lg font-bold font-mono text-amber-700 mt-0.5">
                    -{baoCaoChatLuong.so_dong_trung_lap} dòng
                  </div>
                </div>
                <div className="p-3 rounded border bg-amber-500/5 border-amber-500/20">
                  <div className="text-[11px] text-amber-700">Xử lý thiếu dữ liệu</div>
                  <div className="text-lg font-bold font-mono text-amber-700 mt-0.5">
                    {baoCaoChatLuong.so_dong_thieu_du_lieu} dòng
                  </div>
                </div>
                <div className="p-3 rounded border bg-danger/5 border-danger/20">
                  <div className="text-[11px] text-danger">Đơn âm & Ngoại lai</div>
                  <div className="text-lg font-bold font-mono text-danger mt-0.5">
                    {baoCaoChatLuong.so_dong_am_hoac_loi + baoCaoChatLuong.so_dong_ngoai_lai_da_xu_ly} dòng
                  </div>
                </div>
                <div className="p-3 rounded border border-primary/30 bg-primary/5">
                  <div className="text-[11px] text-primary font-medium">Chuỗi tiêu hao (365 ngày)</div>
                  <div className="text-lg font-bold font-mono text-primary mt-0.5">
                    {baoCaoChatLuong.tong_ban_ghi_tieu_hao_sinh_ra.toLocaleString("vi-VN")} dòng
                  </div>
                </div>
              </div>
              {baoCaoChatLuong.ghi_chu && (
                <p className="text-xs text-muted-foreground mt-3">
                  <strong>Ghi chú kiểm định:</strong> {baoCaoChatLuong.ghi_chu}
                </p>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* KHU VỰC 2: MÔ PHỎNG BÓC TÁCH ĐỊNH MỨC BOM + BIỂU ĐỒ CHUỖI THỜI GIAN */}
      <div className="grid gap-6 lg:grid-cols-12 mb-6">
        {/* Bộ mô phỏng bóc tách BOM & Ghi nhận POS */}
        <Card className="lg:col-span-5">
          <CardHeader className="border-b">
            <div className="flex items-center gap-2">
              <FlaskConical className="h-4 w-4 text-primary" />
              <CardTitle>Mô phỏng Bóc tách Định mức & Xuất bán tại Quầy</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-4">
            <p className="text-xs text-muted-foreground">
              Nhập số lượng ly bán ra cho từng món để quy đổi tức thì sang định mức nguyên liệu tiêu hao và kiểm tra khả năng đáp ứng của kho:
            </p>

            <div className="max-h-60 overflow-y-auto pr-1 space-y-2 border rounded p-2.5 bg-muted/10">
              {danhSachMon.map((m) => (
                <div
                  key={m.ma_mon}
                  className="flex items-center justify-between gap-2 text-xs py-1 border-b last:border-0"
                >
                  <div>
                    <div className="font-medium text-foreground">{m.ten_mon}</div>
                    <div className="text-[10px] text-muted-foreground">
                      Giá bán: {m.don_gia_ban.toLocaleString("vi-VN")}đ • Giá vốn định mức:{" "}
                      {m.gia_von_nguyen_lieu.toLocaleString("vi-VN")}đ
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <input
                      type="number"
                      min={0}
                      max={2000}
                      value={soLuongLyTheoMon[m.ma_mon] ?? 0}
                      onChange={(e) => capNhatSoLuongLy(m.ma_mon, e.target.value)}
                      className="w-16 px-2 py-1 text-right font-mono text-xs rounded border bg-background"
                    />
                    <span className="text-[11px] text-muted-foreground">ly</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                className="flex-1 gap-1.5"
                onClick={() => moPhongMutation.mutate()}
                disabled={moPhongMutation.isPending}
              >
                <Play className="h-3.5 w-3.5" />
                Tính nháp Định mức BOM
              </Button>
              <Button
                variant="default"
                size="sm"
                className="flex-1 gap-1.5"
                onClick={() => ghiNhanPosMutation.mutate()}
                disabled={ghiNhanPosMutation.isPending}
              >
                <ShoppingBag className="h-3.5 w-3.5" />
                Ghi nhận Đơn bán & Trừ kho
              </Button>
            </div>

            {ketQuaMoPhong && (
              <div className="border-t pt-3 space-y-3">
                <div className="grid grid-cols-3 gap-2 text-center bg-primary/5 p-2.5 rounded border border-primary/20">
                  <div>
                    <div className="text-[10px] text-muted-foreground">Tổng số ly</div>
                    <div className="text-sm font-bold font-mono text-primary">
                      {ketQuaMoPhong.tong_so_ly_ban} ly
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-muted-foreground">Doanh thu</div>
                    <div className="text-sm font-bold font-mono text-foreground">
                      {ketQuaMoPhong.tong_doanh_thu_du_kien.toLocaleString("vi-VN")}đ
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-muted-foreground">Lợi nhuận gộp</div>
                    <div className="text-sm font-bold font-mono text-emerald-700">
                      {ketQuaMoPhong.loi_nhuan_gop_du_kien.toLocaleString("vi-VN")}đ
                    </div>
                  </div>
                </div>

                <div className="overflow-x-auto max-h-56 border rounded">
                  <table className="w-full text-left text-[11px]">
                    <thead>
                      <tr className="border-b bg-muted/40 text-muted-foreground font-semibold">
                        <th className="py-2 px-2.5">Nguyên liệu bóc tách</th>
                        <th className="py-2 px-2.5 text-right">Tiêu hao</th>
                        <th className="py-2 px-2.5 text-right">Tồn sau trừ</th>
                        <th className="py-2 px-2.5 text-center">Đáp ứng</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {ketQuaMoPhong.danh_sach_nguyen_lieu_tieu_hao.map((item) => (
                        <tr key={item.ma_nguyen_lieu} className="hover:bg-muted/20">
                          <td className="py-1.5 px-2.5 font-medium">{item.ten_nguyen_lieu}</td>
                          <td className="py-1.5 px-2.5 text-right font-mono text-primary font-semibold">
                            -{item.tong_luong_tieu_hao} {item.don_vi_tinh}
                          </td>
                          <td className="py-1.5 px-2.5 text-right font-mono">
                            {item.ton_kho_sau_tieu_hao} {item.don_vi_tinh}
                          </td>
                          <td className="py-1.5 px-2.5 text-center">
                            {item.du_ton_kho_dap_ung ? (
                              <Badge variant="success">Đủ hàng</Badge>
                            ) : (
                              <Badge variant="danger">Thiếu hàng</Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Biểu đồ Chuỗi Thời Gian Tiêu Hao Nguyên Liệu & Trung Bình Trượt 7 Ngày */}
        <Card className="lg:col-span-7">
          <CardHeader className="border-b">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-primary" />
                <CardTitle>Biểu đồ Chuỗi thời gian Tiêu hao & Trung bình trượt 7 ngày</CardTitle>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={maNguyenLieuChon}
                  onChange={(e) => setMaNguyenLieuChon(Number(e.target.value))}
                  className="text-xs border rounded px-2.5 py-1.5 bg-background font-medium"
                >
                  <option value={1}>#1 - Hạt cà phê Robusta (kg)</option>
                  <option value={2}>#2 - Hạt cà phê Arabica (kg)</option>
                  <option value={3}>#3 - Sữa tươi Barista 1L (hộp)</option>
                  <option value={4}>#4 - Sữa đặc Phương Nam (lon)</option>
                  <option value={5}>#5 - Sữa thanh trùng Đà Lạt Milk (chai)</option>
                  <option value={6}>#6 - Siro Đào Monin (chai)</option>
                  <option value={7}>#7 - Siro Dâu Torani (chai)</option>
                  <option value={8}>#8 - Xốt Socola Hershey (chai)</option>
                  <option value={9}>#9 - Bột Cacao Đắk Lắk (kg)</option>
                  <option value={10}>#10 - Bột Matcha Uji (kg)</option>
                  <option value={11}>#11 - Bột Frappe Base (kg)</option>
                  <option value={12}>#12 - Trà Đen Phúc Long (kg)</option>
                  <option value={13}>#13 - Trà Ô Long Kim Tuyên (kg)</option>
                  <option value={14}>#14 - Ly nhựa PET 500ml (cái)</option>
                  <option value={15}>#15 - Ống hút giấy sinh học (cái)</option>
                </select>
                <select
                  value={soNgayHienThi}
                  onChange={(e) => setSoNgayHienThi(Number(e.target.value))}
                  className="text-xs border rounded px-2 py-1.5 bg-background"
                >
                  <option value={30}>30 ngày</option>
                  <option value={60}>60 ngày</option>
                  <option value={90}>90 ngày</option>
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            {dangTaiChuoiThoiGian || !chuoiThoiGian ? (
              <div className="py-12 text-center text-xs text-muted-foreground">
                Đang tải dữ liệu chuỗi thời gian tiêu hao...
              </div>
            ) : (
              <>
                <div className="grid grid-cols-3 gap-3 mb-4 text-xs">
                  <div className="p-2.5 rounded border bg-muted/20">
                    <span className="text-muted-foreground block">Trung bình mỗi ngày:</span>
                    <strong className="font-mono text-sm">
                      {chuoiThoiGian.trung_binh_ngay} {chuoiThoiGian.don_vi_tinh}/ngày
                    </strong>
                  </div>
                  <div className="p-2.5 rounded border bg-muted/20">
                    <span className="text-muted-foreground block">TB Ngày thường (T2–T6):</span>
                    <strong className="font-mono text-sm">
                      {chuoiThoiGian.tieu_hao_ngay_thuong_tb} {chuoiThoiGian.don_vi_tinh}
                    </strong>
                  </div>
                  <div className="p-2.5 rounded border border-amber-500/30 bg-amber-500/5">
                    <span className="text-amber-800 block">TB Cuối tuần (T7–CN):</span>
                    <strong className="font-mono text-sm text-amber-700">
                      {chuoiThoiGian.tieu_hao_cuoi_tuan_tb} {chuoiThoiGian.don_vi_tinh} (+
                      {chuoiThoiGian.ty_le_tang_cuoi_tuan_pct}%)
                    </strong>
                  </div>
                </div>

                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                      data={chuoiThoiGian.chuoi_thoi_gian.map((pt) => ({
                        ...pt,
                        ngay_ngan: pt.ngay.slice(5),
                      }))}
                      margin={{ top: 8, right: 12, left: -10, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                      <XAxis dataKey="ngay_ngan" tick={{ fontSize: 10 }} minTickGap={18} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip
                        formatter={(val: number, name: string) => [
                          `${val} ${chuoiThoiGian.don_vi_tinh}`,
                          name,
                        ]}
                      />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      <Area
                        type="monotone"
                        dataKey="so_luong_tieu_hao"
                        name="Tiêu hao thực tế theo ngày"
                        fill="#2d5a43"
                        fillOpacity={0.18}
                        stroke="#2d5a43"
                        strokeWidth={1.5}
                      />
                      <Line
                        type="monotone"
                        dataKey="trung_binh_truot_7_ngay"
                        name="Trung bình trượt 7 ngày"
                        stroke="#d97706"
                        strokeWidth={2.2}
                        dot={false}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* KHU VỰC 3: BẢNG MA TRẬN THỰC ĐƠN 12 MÓN & CÔNG THỨC BOM */}
      <Card className="mb-6">
        <CardHeader className="border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <CardTitle>
                Ma trận Thực đơn Đồ uống & Định mức Công thức Pha chế ({danhSachMon.length} món)
              </CardTitle>
            </div>
            <Badge variant="success">Phủ kín 15/15 nguyên liệu trong kho</Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-4">
          {dangTaiThucDon ? (
            <div className="py-8 text-center text-xs text-muted-foreground">
              Đang tải ma trận công thức định mức...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b bg-muted/40 font-semibold uppercase text-muted-foreground">
                    <th className="py-2.5 px-3">Mã</th>
                    <th className="py-2.5 px-3">Tên món đồ uống</th>
                    <th className="py-2.5 px-3">Danh mục</th>
                    <th className="py-2.5 px-3 text-right">Giá bán</th>
                    <th className="py-2.5 px-3 text-right">Giá vốn định mức</th>
                    <th className="py-2.5 px-3 text-right">Tỷ suất lãi gộp</th>
                    <th className="py-2.5 px-3">Chi tiết định mức nguyên liệu (1 ly)</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {danhSachMon.map((m) => (
                    <tr key={m.ma_mon} className="hover:bg-muted/20">
                      <td className="py-3 px-3 font-mono font-semibold text-muted-foreground">
                        #{m.ma_mon}
                      </td>
                      <td className="py-3 px-3 font-semibold text-foreground">{m.ten_mon}</td>
                      <td className="py-3 px-3 text-muted-foreground">{m.danh_muc}</td>
                      <td className="py-3 px-3 text-right font-mono font-medium">
                        {m.don_gia_ban.toLocaleString("vi-VN")} đ
                      </td>
                      <td className="py-3 px-3 text-right font-mono text-primary font-semibold">
                        {m.gia_von_nguyen_lieu.toLocaleString("vi-VN")} đ
                      </td>
                      <td className="py-3 px-3 text-right">
                        <Badge variant="success">{m.ty_suat_loi_nhuan_gop}%</Badge>
                      </td>
                      <td className="py-3 px-3">
                        <div className="flex flex-wrap gap-1.5">
                          {m.cong_thuc_bom.map((r) => (
                            <span
                              key={r.ma_dinh_muc}
                              className="inline-flex items-center px-2 py-0.5 rounded bg-muted text-[11px] font-mono"
                            >
                              {r.ten_nguyen_lieu}:{" "}
                              <strong className="ml-1">
                                {r.so_luong_tieu_hao} {r.don_vi_tinh}
                              </strong>
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* KHU VỰC 4: LỊCH SỬ HÓA ĐƠN BÁN HÀNG ĐÃ LÀM SẠCH GẦN NHẤT */}
      <Card>
        <CardHeader className="border-b">
          <CardTitle>Lịch sử Hóa đơn Bán hàng Đã Làm Sạch & Bóc Tách Định Mức Gần Nhất</CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          {lichSuPos.length === 0 ? (
            <div className="py-6 text-center text-xs text-muted-foreground">
              Chưa có lịch sử hóa đơn bán hàng.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b bg-muted/40 font-semibold text-muted-foreground">
                    <th className="py-2 px-3">Mã hóa đơn</th>
                    <th className="py-2 px-3">Ngày bán</th>
                    <th className="py-2 px-3">Ca bán</th>
                    <th className="py-2 px-3">Tên món đồ uống</th>
                    <th className="py-2 px-3 text-right">Số lượng</th>
                    <th className="py-2 px-3 text-right">Thành tiền</th>
                    <th className="py-2 px-3 text-center">Trạng thái xử lý</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {lichSuPos.map((h) => (
                    <tr key={h.ma_ban_hang} className="hover:bg-muted/20">
                      <td className="py-2 px-3 font-mono font-medium">{h.ma_hoa_don_pos}</td>
                      <td className="py-2 px-3 font-mono">{h.ngay_ban}</td>
                      <td className="py-2 px-3">
                        {h.ca_ban === "SANG"
                          ? "Ca sáng"
                          : h.ca_ban === "CHIEU"
                            ? "Ca chiều"
                            : "Ca tối"}
                      </td>
                      <td className="py-2 px-3 font-medium">{h.ten_mon}</td>
                      <td className="py-2 px-3 text-right font-mono font-semibold">
                        {h.so_luong_ly} ly
                      </td>
                      <td className="py-2 px-3 text-right font-mono">
                        {h.thanh_tien.toLocaleString("vi-VN")} đ
                      </td>
                      <td className="py-2 px-3 text-center">
                        <Badge variant="success">Đã bóc tách định mức</Badge>
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
  );
}
