import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";

export default function SuppliersPage() {
  return (
    <>
      <PageHeader
        title="Nhà cung cấp"
        description="Thông tin nhà cung cấp và bảng báo giá đa tiêu chuẩn: đơn giá, lead time, MOQ, độ uy tín."
      />
      <EmptyState message="Bảng nhà cung cấp và báo giá sẽ nối với API /suppliers ở Tuần 4." />
    </>
  );
}
