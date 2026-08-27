import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Library,
  BarChart3,
  Bug,
  FlaskConical,
  Moon,
  Sun,
  LogOut,
  FileStack,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import clsx from "clsx";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/knowledge-bases", label: "Knowledge bases", icon: Library },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/debug", label: "Retrieval debugger", icon: Bug },
  { to: "/evaluation", label: "Evaluation", icon: FlaskConical },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen bg-ink-50 dark:bg-ink-950 text-ink-900 dark:text-ink-100">
      <aside className="w-60 shrink-0 border-r border-ink-200 dark:border-ink-800 flex flex-col">
        <div className="h-16 flex items-center gap-2 px-5 border-b border-ink-200 dark:border-ink-800">
          <div className="w-7 h-7 rounded-md bg-amber-500 flex items-center justify-center text-ink-950 font-bold text-sm">
            <FileStack size={16} strokeWidth={2.5} />
          </div>
          <span className="font-display text-lg font-semibold tracking-tight">DocuRAG</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-ink-900 text-ink-50 dark:bg-ink-100 dark:text-ink-950"
                    : "text-ink-500 hover:text-ink-900 hover:bg-ink-100 dark:text-ink-400 dark:hover:text-ink-50 dark:hover:bg-ink-800"
                )
              }
            >
              <item.icon size={17} strokeWidth={2} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-ink-200 dark:border-ink-800 space-y-1">
          <button
            onClick={toggle}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-ink-500 hover:bg-ink-100 dark:text-ink-400 dark:hover:bg-ink-800"
          >
            {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-7 h-7 rounded-full bg-teal-500/20 text-teal-600 dark:text-teal-400 flex items-center justify-center text-xs font-semibold shrink-0">
              {user?.full_name?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium truncate">{user?.full_name}</p>
              <p className="text-xs text-ink-400 truncate">{user?.email}</p>
            </div>
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="text-ink-400 hover:text-rose-500 shrink-0"
              title="Log out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <Outlet />
      </main>
    </div>
  );
}
