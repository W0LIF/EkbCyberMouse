import {
  AlertCircle,
  BarChart3,
  Building2,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Layers3,
  ListTodo,
  LogOut,
  Map,
  Settings,
  TriangleAlert,
  ToolCase,
  Users,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { navItems } from "../../shared/config/nav";
import { Logo } from "../../shared/ui/Logo";
import { Tooltip } from "../../shared/ui/Tooltip";
import { useAuth } from "../../features/auth/AuthContext";

const iconMap: Record<string, typeof Map> = {
  Map,
  BarChart3,
  ListTodo,
  TriangleAlert,
  AlertCircle,
  ToolCase,
  Users,
  Building2,
  Settings,
  CircleHelp,
  Layers3,
};

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapsed: () => void;
}

export function Sidebar({ collapsed, onToggleCollapsed }: SidebarProps) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="side-head">
        <Logo compact={collapsed} />
        <button onClick={onToggleCollapsed}>
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>
      <nav>
        {navItems.map((item, index) => {
          const Icon = iconMap[item.icon] ?? Map;
          const isDup = index === 4 && location.pathname === "/risks";
          const isActive = location.pathname === `/${item.id}` && !isDup;
          return (
            <Tooltip text={collapsed ? item.label : ""} key={`${item.label}-${index}`}>
              <button
                className={isActive ? "active" : ""}
                onClick={() => navigate(`/${item.id}`)}
              >
                <Icon size={20} />
                <span>{item.label}</span>
                {item.badge && <b className={`badge ${item.tone}`}>{item.badge}</b>}
              </button>
            </Tooltip>
          );
        })}
      </nav>
      <div className="side-user">
        <span className="avatar">АД</span>
        {!collapsed && (
          <span className="user-copy">
            <b>Администратор</b>
            <small>
              <i /> онлайн
            </small>
          </span>
        )}
        <Tooltip text="Выйти из системы">
          <button onClick={logout}>
            <LogOut size={18} />
          </button>
        </Tooltip>
      </div>
    </aside>
  );
}
