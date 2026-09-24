import { Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { Toaster } from "sonner";

import { NavBar } from "@/components/nav-bar";
import { Footer } from "@/components/footer";
import { ErrorBoundary } from "@/components/error-boundary";
import { PageTransition } from "@/components/page-transition";
import HomePage from "@/pages/home-page";
import SubmitPage from "@/pages/submit-page";
import DashboardPage from "@/pages/dashboard-page";
import StatsPage from "@/pages/stats-page";
import NotFoundPage from "@/pages/not-found-page";

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait" initial={false}>
      <Routes location={location} key={location.pathname}>
        <Route
          path="/"
          element={
            <PageTransition>
              <HomePage />
            </PageTransition>
          }
        />
        <Route
          path="/submit"
          element={
            <PageTransition>
              <SubmitPage />
            </PageTransition>
          }
        />
        <Route
          path="/dashboard"
          element={
            <PageTransition>
              <DashboardPage />
            </PageTransition>
          }
        />
        <Route
          path="/stats"
          element={
            <PageTransition>
              <StatsPage />
            </PageTransition>
          }
        />
        <Route
          path="*"
          element={
            <PageTransition>
              <NotFoundPage />
            </PageTransition>
          }
        />
      </Routes>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <NavBar />
      <main className="flex-1">
        <ErrorBoundary>
          <AnimatedRoutes />
        </ErrorBoundary>
      </main>
      <Footer />
      <Toaster
        position="bottom-right"
        toastOptions={{
          classNames: {
            toast: "!bg-surface !text-foreground !border !border-border toast-progress",
            title: "!text-foreground",
            description: "!text-muted-foreground",
          },
        }}
      />
    </div>
  );
}
