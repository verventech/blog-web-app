import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Home from "./pages/Home";
import BlogDetail from "./pages/BlogDetail";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Write from "./pages/Write";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

function Page({ children }) {
  return <main>{children}</main>;
}

export default function App() {
  const location = useLocation();

  useEffect(() => {
    if (!location.hash) window.scrollTo({ top: 0 });
  }, [location.pathname, location.hash]);

  return (
    <>
      <Navbar />
      <Routes location={location}>
          <Route path="/" element={<Page><Home /></Page>} />
          <Route path="/blog/:id" element={<Page><BlogDetail /></Page>} />
          <Route path="/user/:id" element={<Page><Profile /></Page>} />
          <Route path="/login" element={<Page><Login /></Page>} />
          <Route path="/register" element={<Page><Register /></Page>} />
          <Route path="/write" element={<ProtectedRoute><Page><Write /></Page></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Page><Settings /></Page></ProtectedRoute>} />
          <Route path="*" element={<Page><NotFound /></Page>} />
      </Routes>
      <footer className="footer">© {new Date().getFullYear()} Inkwell</footer>
    </>
  );
}
