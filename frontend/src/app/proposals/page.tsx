import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";

export default function ProposalsPage() {
  return (
    <>
      <PageHeader
        title="Đề xuất mua hàng"
        description="Phiếu do AI Agent lập luôn ở trạng thái chờ duyệt; quản lý xem xét, sửa và bấm duyệt."
      />
      <EmptyState message="Danh sách phiếu đề xuất và luồng duyệt sẽ hoàn thiện ở Tuần 8." />
    </>
  );
}
