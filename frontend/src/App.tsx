import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import KnowledgeBasesPage from "./pages/KnowledgeBasesPage";
import KnowledgeBaseDetailPage from "./pages/KnowledgeBaseDetailPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import DebugPage from "./pages/DebugPage";
import EvaluationPage from "./pages/EvaluationPage";

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Toaster position="top-right" toastOptions={{ style: { fontSize: "13px" } }} />
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/knowledge-bases" element={<KnowledgeBasesPage />} />
                <Route path="/knowledge-bases/:kbId" element={<KnowledgeBaseDetailPage />} />
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/debug" element={<DebugPage />} />
                <Route path="/evaluation" element={<EvaluationPage />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}
