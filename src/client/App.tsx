import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import DashboardPage from './pages/dashboard/DashboardPage'
import ArticleDistributionPage from './pages/dashboard/ArticleDistributionPage'
import ArticleDistributionAccountsPage from './pages/dashboard/ArticleDistributionAccountsPage'
import ArticleDistributionReportPage from './pages/dashboard/ArticleDistributionReportPage'
import ArticleTrafficStatsPage from './pages/dashboard/ArticleTrafficStatsPage'
import ProfilePage from './pages/profile/ProfilePage'
import SecurityPage from './pages/profile/SecurityPage'
import DevicesPage from './pages/profile/DevicesPage'
import AdminManagementPage from './pages/admin/AdminManagementPage'
import LoginPage from './pages/auth/LoginPage'
import ConfirmPasswordChangePage from './pages/auth/ConfirmPasswordChangePage'
import RegisterPage from './pages/auth/RegisterPage'
import ResetPasswordPage from './pages/auth/ResetPasswordPage'
import OAuthAuthorizePage from './pages/auth/OAuthAuthorizePage'
import OAuthDeviceAuthorizePage from './pages/auth/OAuthDeviceAuthorizePage'
import PublicDashboardPage from './pages/public/PublicDashboardPage'
import { AuthProvider, RequireAdmin, RequireAuth, RequireScope } from './providers/AuthProvider'
import { RuntimeConfigProvider } from './providers/RuntimeConfigProvider'
import ThemeToggle from './components/theme/ThemeToggle'

export default function App() {
  return (
    <Router>
      <RuntimeConfigProvider>
        <AuthProvider>
          <>
            <Routes>
            <Route path="/" element={<HomeRedirect />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
            <Route path="/profile/password-change/:token" element={<ConfirmPasswordChangePage />} />
            <Route path="/public/dashboard/:projectCode" element={<PublicDashboardPage />} />
            <Route
              path="/oauth/authorize"
              element={
                <RequireAuth>
                  <OAuthAuthorizePage />
                </RequireAuth>
              }
            />
            <Route
              path="/oauth/device"
              element={
                <RequireAuth>
                  <OAuthDeviceAuthorizePage />
                </RequireAuth>
              }
            />
            <Route
              element={
                <RequireAuth>
                  <MainLayout />
                </RequireAuth>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/article-distribution" element={<ArticleDistributionPage />} />
              <Route path="/article-distribution/accounts" element={<ArticleDistributionAccountsPage />} />
              <Route path="/article-distribution/traffic" element={<ArticleTrafficStatsPage />} />
              <Route
                path="/article-distribution/report"
                element={
                  <RequireScope scope="article_distribution:report:read">
                    <ArticleDistributionReportPage />
                  </RequireScope>
                }
              />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/profile/security" element={<SecurityPage />} />
              <Route path="/profile/devices" element={<DevicesPage />} />
              <Route
                path="/admin"
                element={
                  <RequireAdmin>
                    <AdminManagementPage />
                  </RequireAdmin>
                }
              />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            <ThemeToggle />
          </>
        </AuthProvider>
      </RuntimeConfigProvider>
    </Router>
  )
}

function HomeRedirect() {
  return <Navigate to="/article-distribution" replace />
}
