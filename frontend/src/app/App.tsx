import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import type { ModalType } from "../shared/types/domain";
import { Sidebar } from "../widgets/sidebar/Sidebar";
import { Header } from "../widgets/header/Header";
import { OrderDrawer } from "../widgets/modals/OrderDrawer";
import { NewOrderModal } from "../widgets/modals/NewOrderModal";
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
import { DispatchDataProvider } from "../features/dispatch/DispatchDataContext";

export default function App() {
  const { logged, login, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [modal, setModal] = useState<ModalType>(null);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [explainOrderId, setExplainOrderId] = useState<string | null>(null);
  const [newOrderOpen, setNewOrderOpen] = useState(false);
  const [help, setHelp] = useState(false);
  const [tour, setTour] = useState(false);
  const navigate = useNavigate();
  function openOrder(orderId: string) {
    setSelectedOrderId(orderId);
    setModal("order");
  }
  function openExplanation(orderId: string) {
    setSelectedOrderId(null);
    setExplainOrderId(orderId);
    setModal("explain");
  }
  function openAssignment(orderId: string) {
    setSelectedOrderId(null);
    setExplainOrderId(orderId);
    setModal("reassign");
  }

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

  return (
    <DispatchDataProvider>
      {isMobile ? (
        <MobileRoutePage logout={logout} />
      ) : (
        <>
          <div className="app-shell">
            <Sidebar
              collapsed={collapsed}
              onToggleCollapsed={() => setCollapsed(!collapsed)}
            />
            <div className="app-main">
              <Header
                onHelp={() => setHelp(true)}
                onOpenOrder={openOrder}
              />
              <div className="content">
                <Routes>
                  <Route path="/" element={<Navigate to="/map" replace />} />
                  <Route path="/map" element={<MapPage openOrder={openOrder} openCreate={() => setNewOrderOpen(true)} />} />
                  <Route path="/plan" element={<PlanPage setModal={setModal} openOrder={openOrder} />} />
                  <Route path="/orders" element={<OrdersPage openOrder={openOrder} openCreate={() => setNewOrderOpen(true)} />} />
                  <Route path="/risks" element={<RisksPage openOrder={openOrder} />} />
                  <Route path="/unassigned" element={<RisksPage openOrder={openOrder} showOnlyUnassigned />} />
                  <Route path="/pgp" element={<PgpPage />} />
                  <Route path="/people" element={<PeoplePage />} />
                  <Route path="/centers" element={<CentersPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="/help" element={<HelpPage />} />
                  <Route path="/library" element={<LibraryPage />} />
                </Routes>
              </div>
            </div>
          </div>
          {modal === "order" && (
            <OrderDrawer
              orderId={selectedOrderId}
              close={() => {
                setModal(null);
                setSelectedOrderId(null);
              }}
              onExplain={openExplanation}
              onAssign={openAssignment}
            />
          )}
          {newOrderOpen && <NewOrderModal close={() => setNewOrderOpen(false)} />}
          {modal && modal !== "order" && (
            <CenterModal
              type={modal}
              orderId={explainOrderId}
              close={() => setModal(null)}
            />
          )}
          {help && (
            <HelpPanel
              close={() => setHelp(false)}
              startTour={() => {
                setHelp(false);
                setTour(true);
              }}
            />
          )}
          {tour && (
            <Onboarding
              finish={() => {
                setTour(false);
                localStorage.setItem("rtk-tour", "done");
              }}
            />
          )}
        </>
      )}
    </DispatchDataProvider>
  );
}
