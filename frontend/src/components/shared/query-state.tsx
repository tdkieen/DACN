"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

/** Khung chờ khi đang tải dữ liệu. */
export function LoadingState({ label = "Đang tải dữ liệu" }: { label?: string }) {
  return (
    <Card className="space-y-3 p-5" aria-busy="true" aria-label={label}>
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="h-6 animate-pulse rounded-md bg-muted" />
      ))}
    </Card>
  );
}

/** Thông báo lỗi kết nối Backend, có nút thử lại. */
export function ErrorNotice({ onRetry, message }: { onRetry?: () => void; message?: string }) {
  return (
    <Card className="flex flex-col items-center gap-3 p-8 text-center" role="alert">
      <AlertTriangle className="h-6 w-6 text-danger" aria-hidden />
      <p className="text-sm">
        {message ?? "Không tải được dữ liệu. Kiểm tra Backend FastAPI đang chạy tại cổng 8000 rồi thử lại."}
      </p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Thử lại
        </Button>
      )}
    </Card>
  );
}
