"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ProposalWithDetails } from "@/types";
import { Bot, CheckCircle, XCircle, Clock, ShieldCheck, MessageSquare, Sparkles, RefreshCw, CheckCircle2, AlertCircle } from "lucide-react";

export default function ProposalsPage() {
  const queryClient = useQueryClient();
  const [comments, setComments] = useState<Record<string | number, string>>({});
  const [aiNotification, setAiNotification] = useState<string | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

  const { data: proposals = [], isLoading, isError, refetch } = useQuery<ProposalWithDetails[]>({
    queryKey: ["proposals"],
    queryFn: async () => {
      const res = await api.get<ProposalWithDetails[]>("/proposals");
      return res.data;
    },
  });

  const generateAiMutation = useMutation({
    mutationFn: async () => {
      setAiError(null);
      setAiNotification(null);
      const res = await api.post<ProposalWithDetails>("/proposals/generate-ai");
      return res.data;
    },
    onSuccess: async (data) => {
      queryClient.setQueryData<ProposalWithDetails[]>(["proposals"], (old = []) => {
        const filtered = old.filter((item) => item.ma_phieu_de_xuat !== data.ma_phieu_de_xuat && item.details.length > 0);
        return [data, ...filtered];
      });
      await queryClient.invalidateQueries({ queryKey: ["proposals"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      await refetch();
      setAiNotification(
        `AI Procurement Agent đã quét kho thành công! Đã lập Phiếu đề xuất #${data.ma_phieu_de_xuat} gồm ${data.details.length} mặt hàng (Tổng dự kiến: ${Number(data.tong_tien_du_kien).toLocaleString("vi-VN")} đ).`
      );
    },
    onError: (err: Error) => {
      setAiError(
        `Không thể kích hoạt AI tạo đề xuất: ${err.message}. Hãy kiểm tra terminal Backend FastAPI đã tự reload chưa.`
      );
    },
  });

  const actionMutation = useMutation({
    mutationFn: async ({ proposalId, action, reason }: { proposalId: string | number; action: string; reason: string }) => {
      setAiError(null);
      await api.post(`/proposals/${proposalId}/action`, {
        hanh_dong: action,
        nguoi_duyet: "Nguyễn Văn Quản Lý",
        y_kien: reason || "Đã duyệt từ Dashboard",
      });
      return { proposalId, action };
    },
    onSuccess: async ({ proposalId, action }) => {
      await queryClient.invalidateQueries({ queryKey: ["proposals"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      await refetch();
      setComments((prev) => ({ ...prev, [proposalId]: "" }));
      setAiNotification(
        action === "APPROVE"
          ? `Đã phê duyệt thành công Phiếu đề xuất #${proposalId}!`
          : `Đã từ chối Phiếu đề xuất #${proposalId}.`
      );
    },
    onError: (err: Error) => {
      setAiError(`Lỗi khi xử lý phiếu đề xuất: ${err.message}`);
    },
  });

  return (
    <>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <PageHeader
          title="Đề xuất mua hàng (AI Human-in-the-loop)"
          description="Phiếu đề xuất thông minh do AI Procurement Agent tự động lập; Quản lý xem xét, chỉnh sửa và phê duyệt."
        />
        <Button
          onClick={() => generateAiMutation.mutate()}
          disabled={generateAiMutation.isPending}
          className="gap-2 shrink-0 bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm"
        >
          {generateAiMutation.isPending ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          {generateAiMutation.isPending ? "AI đang quét kho & tính toán..." : "Kích hoạt AI Quét Kho & Lập Đề Xuất"}
        </Button>
      </div>

      {aiNotification && (
        <div className="mb-6 p-4 rounded-md border border-emerald-500/30 bg-emerald-500/10 text-emerald-800 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span className="font-medium">{aiNotification}</span>
          </div>
          <button
            onClick={() => setAiNotification(null)}
            className="text-xs font-semibold underline ml-4 hover:text-emerald-950"
          >
            Đóng
          </button>
        </div>
      )}

      {aiError && (
        <div className="mb-6 p-4 rounded-md border border-danger/40 bg-danger/10 text-danger text-xs flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="h-4 w-4 text-danger shrink-0" />
            <span className="font-medium">{aiError}</span>
          </div>
          <button
            onClick={() => setAiError(null)}
            className="text-xs font-semibold underline ml-4 hover:text-danger/80"
          >
            Đóng
          </button>
        </div>
      )}

      <div className="space-y-6">
        {isLoading ? (
          <div className="py-12 text-center text-muted-foreground">Đang tải danh sách đề xuất...</div>
        ) : isError ? (
          <div className="py-12 text-center text-danger">
            Không thể tải đề xuất từ Backend API. Vui lòng kiểm tra server FastAPI.
          </div>
        ) : proposals.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground">Không có phiếu đề xuất mua hàng nào.</div>
        ) : (
          proposals.map((p) => {
            const isPending = p.trang_thai === "CHO_DUYET";
            return (
              <Card key={p.ma_phieu_de_xuat} className={isPending ? "border-primary/40 shadow-sm" : ""}>
                <CardHeader className="bg-muted/15 border-b">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="h-9 w-9 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
                        <Bot className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-base font-bold">
                            Phiếu đề xuất #{p.ma_phieu_de_xuat}
                          </CardTitle>
                          {p.trang_thai === "CHO_DUYET" && (
                            <Badge variant="warning" className="gap-1">
                              <Clock className="h-3 w-3" /> Chờ duyệt
                            </Badge>
                          )}
                          {p.trang_thai === "DA_DUYET" && (
                            <Badge variant="success" className="gap-1">
                              <CheckCircle className="h-3 w-3" /> Đã duyệt
                            </Badge>
                          )}
                          {p.trang_thai === "TU_CHOI" && (
                            <Badge variant="danger" className="gap-1">
                              <XCircle className="h-3 w-3" /> Từ chối
                            </Badge>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          Tạo bởi: <strong className="text-foreground">{p.nguoi_tao}</strong> • {new Date(p.ngay_tao).toLocaleString("vi-VN")}
                        </div>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-xs text-muted-foreground">Tổng tiền dự kiến</div>
                      <div className="text-lg font-bold text-primary font-mono">
                        {Number(p.tong_tien_du_kien).toLocaleString("vi-VN")} đ
                      </div>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="pt-4 space-y-4">
                  {/* Lập luận AI */}
                  {p.ly_do_tong_quan && (
                    <div className="p-3 bg-primary/5 border border-primary/20 rounded-md text-xs text-foreground/90">
                      <strong className="text-primary flex items-center gap-1.5 mb-1">
                        <Bot className="h-3.5 w-3.5" /> Lập luận tổng quan của AI Agent:
                      </strong>
                      <p>{p.ly_do_tong_quan}</p>
                    </div>
                  )}

                  {/* Bảng chi tiết mặt hàng */}
                  <div className="overflow-x-auto rounded border bg-background">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b bg-muted/40 font-semibold text-muted-foreground">
                          <th className="py-2.5 px-3">Nguyên liệu</th>
                          <th className="py-2.5 px-3">Nhà cung cấp đề xuất</th>
                          <th className="py-2.5 px-3 text-right">SL đề xuất</th>
                          <th className="py-2.5 px-3 text-right">Đơn giá dự kiến</th>
                          <th className="py-2.5 px-3 text-right">Thành tiền</th>
                          <th className="py-2.5 px-3">Lý do chọn NCC & Số lượng (AI)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {p.details.map((d) => (
                          <tr key={d.ma_chi_tiet} className="hover:bg-muted/30">
                            <td className="py-2.5 px-3 font-semibold text-foreground">
                              {d.ten_nguyen_lieu}
                            </td>
                            <td className="py-2.5 px-3 text-muted-foreground">
                              {d.ten_nha_cung_cap}
                            </td>
                            <td className="py-2.5 px-3 text-right font-bold text-primary font-mono">
                              {d.so_luong_de_xuat} {d.don_vi_tinh}
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono">
                              {d.don_gia_du_kien.toLocaleString("vi-VN")} đ
                            </td>
                            <td className="py-2.5 px-3 text-right font-bold font-mono">
                              {d.thanh_tien.toLocaleString("vi-VN")} đ
                            </td>
                            <td className="py-2.5 px-3 text-muted-foreground text-[11px] max-w-xs">
                              {d.ly_do_de_xuat}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Lịch sử duyệt */}
                  {p.approval_history && p.approval_history.length > 0 && (
                    <div className="border-t pt-3 space-y-1.5">
                      <div className="text-xs font-semibold text-muted-foreground flex items-center gap-1">
                        <MessageSquare className="h-3.5 w-3.5" /> Lịch sử phê duyệt:
                      </div>
                      {p.approval_history.map((h, hIdx) => (
                        <div key={hIdx} className="text-xs text-muted-foreground flex items-center justify-between bg-muted/20 p-2 rounded">
                          <div>
                            <strong>{h.nguoi_duyet}</strong>: &quot;{h.y_kien ?? "Không có ý kiến"}&quot;
                          </div>
                          <div className="text-[10px]">
                            {new Date(h.thoi_gian_duyet).toLocaleString("vi-VN")}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Vùng hành động duyệt (Human-in-the-loop) */}
                  {isPending && (
                    <div className="border-t pt-4 flex flex-col sm:flex-row items-center justify-between gap-3 bg-muted/10 p-3 rounded-md">
                      <input
                        type="text"
                        placeholder="Nhập ý kiến duyệt/chỉnh sửa của Quản lý..."
                        value={comments[p.ma_phieu_de_xuat] ?? ""}
                        onChange={(e) => setComments((prev) => ({ ...prev, [p.ma_phieu_de_xuat]: e.target.value }))}
                        className="w-full sm:flex-1 text-xs px-3 py-2 rounded border bg-background focus:outline-none focus:ring-1 focus:ring-primary"
                      />
                      <div className="flex gap-2 w-full sm:w-auto justify-end">
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-danger hover:bg-danger/10 border-danger/30"
                          onClick={() => actionMutation.mutate({ proposalId: p.ma_phieu_de_xuat, action: "REJECT", reason: comments[p.ma_phieu_de_xuat] ?? "" })}
                          disabled={actionMutation.isPending}
                        >
                          <XCircle className="h-4 w-4 mr-1" /> Từ chối
                        </Button>
                        <Button
                          variant="default"
                          size="sm"
                          className="bg-emerald-600 hover:bg-emerald-700 text-white"
                          onClick={() => actionMutation.mutate({ proposalId: p.ma_phieu_de_xuat, action: "APPROVE", reason: comments[p.ma_phieu_de_xuat] ?? "" })}
                          disabled={actionMutation.isPending}
                        >
                          <ShieldCheck className="h-4 w-4 mr-1" /> Phê duyệt đề xuất
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </>
  );
}
