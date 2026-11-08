import { PageHeader } from "@/components/shared/page-header";
import { StatCard } from "@/components/shared/stat-card";
import { EmptyState } from "@/components/shared/empty-state";

export default function DashboardPage() {
  return (
    <>
      <PageHeader
        title="Tổng quan"
        description="Tình hình tồn kho, cảnh báo thiếu/thừa nguyên liệu và các đề xuất đang chờ duyệt."
      />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Nguyên liệu đang dùng" value="—" hint="Dữ liệu từ NGUYEN_LIEU (Tuần 4)" />
        <StatCard title="Nguy cơ thiếu hàng" value="—" hint="Tồn kho ≤ ROP" />
        <StatCard title="Nguy cơ tồn dư đọng vốn" value="—" hint="Tồn kho > Max Stock" />
        <StatCard title="Phiếu chờ duyệt" value="—" hint="Trạng thái CHO_DUYET" />
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <EmptyState message="Biểu đồ xu hướng tiêu thụ 12 tháng sẽ hiển thị tại đây." />
        <EmptyState message="Đường dự báo nhu cầu 7 ngày tới sẽ hiển thị tại đây." />
      </div>
    </>
  );
}
