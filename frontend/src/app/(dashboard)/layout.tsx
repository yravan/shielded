import { TopNav } from "@/components/layout/top-nav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen w-full">
      <TopNav />
      <main className="flex-1 p-4 sm:p-6">{children}</main>
    </div>
  );
}
