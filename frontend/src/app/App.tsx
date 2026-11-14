import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import type { ModalType } from "../shared/types/domain";
import { Sidebar } from "../widgets/sidebar/Sidebar";
import { Header } from "../widgets/header/Header";
import { OrderDrawer } from "../widgets/modals/OrderDrawer";
import { CenterModal } from "../widgets/modals/CenterModal";
import { HelpPanel } from "../widgets/help-panel/HelpPanel";
import { Onboarding } from "../widgets/onboarding/Onboarding";
import { LoginPage } from "../pages/LoginPage";
import MapPage from "../pages/MapPage";
import PlanPage from "../pages/PlanPage";
import OrdersPage from "../pages/OrdersPage";
import RisksPage from "../pages/RisksPage";
import PgpPage from "../pages/PgpPage";
import PeoplePage from "../pages/PeoplePage";
import CentersPage from "../pages/CentersPage";
import SettingsPage from "../pages/SettingsPage";
import HelpPage from "../pages/HelpPage";
import LibraryPage from "../pages/LibraryPage";
import MobileRoutePage from "../pages/MobileRoutePage";
import { useAuth } from "../features/auth/AuthContext";

export default function App() {
  const { logged, login, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [modal, setModal] = useState<ModalType>(null);
  const [help, setHelp] = useState(false);
  const [tour, setTour] = useState(false);
  const navigate = useNavigate();

  const isMobile = useMemo(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia("(max-width: 600px)").matches,
    [],
  );

  useEffect(() => {
    function keys(e: KeyboardEvent) {
      const target = e.target as HTMLElement;
      const isTyping =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      if (e.key === "Escape") {
        setModal(null);
        setHelp(false);
        return;
      }

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        const searchInput = document.querySelector<HTMLInputElement>(
          ".global-search input",
        );
        searchInput?.focus();
        return;
      }

      if (isTyping || e.ctrlKey || e.metaKey || e.altKey) return;

      if (e.key.toLowerCase() === "g") navigate("/map");
      if (e.key.toLowerCase() === "p") navigate("/plan");
    }
    window.addEventListener("keydown", keys);
    return () => window.removeEventListener("keydown", keys);
  }, [navigate]);

  if (!logged) return <LoginPage onLogin={login} />;
  if (isMobile) return <MobileRoutePage logout={logout} />;

  return (
    <div className="app-shell">
      <Sidebar
        collapsed={collapsed}
        onToggleCollapsed={() => setCollapsed(!collapsed)}
      />
      <div className="app-main">
        <Header onHelp={() => setHelp(true)} />
        <div className="content">
          <Routes>
            <Route path="/" element={<Navigate to="/map" replace />} />
            <Route path="/map" element={<MapPage setModal={setModal} />} />
            <Route path="/plan" element={<PlanPage setModal={setModal} />} />
            <Route path="/orders" element={<OrdersPage setModal={setModal} />} />
            <Route path="/risks" element={<RisksPage setModal={setModal} />} />
            <Route path="/pgp" element={<PgpPage />} />
            <Route path="/people" element={<PeoplePage />} />
            <Route path="/centers" element={<CentersPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/help" element={<HelpPage />} />
            <Route path="/library" element={<LibraryPage />} />
          </Routes>
        </div>
      </div>
      {modal === "order" && (
        <OrderDrawer close={() => setModal(null)} setModal={setModal} />
      )}
      {modal && modal !== "order" && (
        <CenterModal type={modal} close={() => setModal(null)} setModal={setModal} />
      )}
      {help && <HelpPanel close={() => setHelp(false)} />}
      {tour && (
        <Onboarding
          finish={() => {
            setTour(false);
            localStorage.setItem("rtk-tour", "done");
          }}
        />
      )}
    </div>
  );
}
