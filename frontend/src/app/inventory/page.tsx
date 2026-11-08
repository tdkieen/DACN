import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";

export default function InventoryPage() {
  return (
    <>
      <PageHeader
        title="Tồn kho"
        description="Danh sách nguyên liệu, tồn kho hiện tại so với mức tồn an toàn, lô hàng và hạn sử dụng."
      />
      <EmptyState message="Bảng tồn kho nguyên liệu sẽ nối với API /ingredients ở Tuần 4." />
    </>
  );
}
