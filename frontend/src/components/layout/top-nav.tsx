"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Search,
  Settings,
  LogOut,
  Shield,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { useUser, useClerk } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

const navItems = [
  { title: "Dashboard", href: "/dashboard" },
  { title: "My Events", href: "/events" },
  { title: "Explore", href: "/explore" },
  { title: "Companies", href: "/companies" },
  { title: "Hedging", href: "/hedging" },
  { title: "Settings", href: "/settings" },
];

function getInitials(name: string | null | undefined): string {
  if (!name) return "?";
  return name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function TopNav() {
  const pathname = usePathname();
  const { user } = useUser();
  const { signOut } = useClerk();
  const queryClient = useQueryClient();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background">
      {/* Row 1: Logo, Search, User */}
      <div className="flex h-14 items-center gap-4 px-4 sm:px-6">
        <Link href="/dashboard" className="flex items-center gap-2 shrink-0">
          <Shield className="h-6 w-6 text-primary" />
          <span className="text-lg font-semibold">Shielded</span>
        </Link>

        <div className="relative hidden sm:block flex-1 max-w-md mx-auto">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search events, companies..."
            className="pl-9 bg-muted/50"
          />
        </div>

        <div className="ml-auto flex items-center">
          <DropdownMenu>
            <DropdownMenuTrigger className="rounded-full outline-none focus:ring-2 focus:ring-ring">
              <Avatar className="h-8 w-8">
                <AvatarImage src={user?.imageUrl} alt={user?.fullName ?? ""} />
                <AvatarFallback className="text-xs">
                  {getInitials(user?.fullName)}
                </AvatarFallback>
              </Avatar>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="px-2 py-1.5">
                <div className="flex flex-col">
                  <span className="text-sm font-medium">{user?.fullName ?? "User"}</span>
                  <span className="text-xs text-muted-foreground">
                    {user?.primaryEmailAddress?.emailAddress}
                  </span>
                </div>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => window.location.href = "/settings"} className="cursor-pointer">
                <Settings className="h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => {
                  queryClient.clear();
                  signOut({ redirectUrl: "/" });
                }}
                className="cursor-pointer"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Row 2: Navigation links */}
      <nav className="flex items-center gap-1 overflow-x-auto px-4 sm:px-6">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "px-3 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors",
              pathname.startsWith(item.href)
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {item.title}
          </Link>
        ))}
      </nav>
    </header>
  );
}
