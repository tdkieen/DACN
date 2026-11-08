import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

export const metadata: Metadata = {
  title: "AI Procurement Agent – Quản lý tồn kho",
  description: "Dashboard dự báo nhu cầu nguyên liệu và duyệt đề xuất mua hàng",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex min-w-0 flex-1 flex-col">
              <Header />
              <main className="flex-1 p-4 md:p-8">{children}</main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
