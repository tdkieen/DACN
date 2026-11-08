import Link from "next/link";
import { NAV_ITEMS } from "@/lib/constants";

export function Header() {
  return (
    <header className="border-b bg-card">
      <div className="flex h-16 items-center justify-between px-4 md:px-8">
        <p className="text-sm text-muted-foreground">Quản lý tồn kho quán cà phê</p>
        <span className="rounded-sm bg-muted px-2 py-1 text-xs text-muted-foreground">
          Đồ án chuyên ngành – HUTECH
        </span>
      </div>
      {/* Điều hướng rút gọn cho màn hình nhỏ */}
      <nav className="flex gap-1 overflow-x-auto border-t px-3 py-2 md:hidden" aria-label="Điều hướng">
        {NAV_ITEMS.map(({ href, label }) => (
          <Link key={href} href={href} className="whitespace-nowrap rounded-md px-3 py-1.5 text-sm hover:bg-muted">
            {label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
