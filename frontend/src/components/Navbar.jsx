import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { LogOut, PenSquare, Settings, User as UserIcon } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import Avatar from "./Avatar";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const handleLogout = () => {
    setMenuOpen(false);
    logout();
    navigate("/");
  };

  return (
    <header className={`nav ${scrolled ? "nav-scrolled" : ""}`}>
      <div className="nav-inner">
        <Link to="/" className="brand">
          <img src="/logo-mark.jpg" alt="" className="brand-mark" />
          <span className="brand-lockup">
            <span className="brand-text">Inkwell</span>
            <span className="brand-tag">Stories worth keeping</span>
          </span>
        </Link>

        <img src="/header-still.jpg" alt="" className="nav-graphic" />

        <nav className="nav-links">
          <NavLink to="/" end className="nav-link">
            Home
          </NavLink>
          {user && (
            <NavLink to={`/user/${user.id}`} className="nav-link">
              My stories
            </NavLink>
          )}
        </nav>

        <div className="nav-actions">
          {user ? (
            <>
              <Link to="/write" className="btn btn-primary btn-sm">
                <PenSquare size={16} /> <span className="hide-sm">Write</span>
              </Link>
              <div className="menu-wrap" ref={menuRef}>
                <button className="avatar-btn" onClick={() => setMenuOpen((o) => !o)} aria-label="Account menu">
                  <Avatar user={user} size={32} />
                </button>
                <AnimatePresence>
                  {menuOpen && (
                    <motion.div
                      className="menu"
                      initial={{ opacity: 0, y: -8, scale: 0.96 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: -8, scale: 0.96 }}
                      transition={{ duration: 0.15 }}
                    >
                      <div className="menu-head">
                        <strong>{user.name}</strong>
                        <span>@{user.username}</span>
                      </div>
                      <Link to={`/user/${user.id}`} className="menu-item" onClick={() => setMenuOpen(false)}>
                        <UserIcon size={16} /> Profile
                      </Link>
                      <Link to="/settings" className="menu-item" onClick={() => setMenuOpen(false)}>
                        <Settings size={16} /> Settings
                      </Link>
                      <button className="menu-item danger" onClick={handleLogout}>
                        <LogOut size={16} /> Log out
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost btn-sm">
                Log in
              </Link>
              <Link to="/register" className="btn btn-primary btn-sm">
                Get started
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
