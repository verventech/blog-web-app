import { motion } from "framer-motion";
import { Feather } from "lucide-react";

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="page auth-page">
      <motion.div
        className="auth-card glass"
        initial={{ opacity: 0, y: 30, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="auth-glow" />
        <div className="auth-icon">
          <Feather size={22} />
        </div>
        <h1>{title}</h1>
        <p className="muted">{subtitle}</p>
        {children}
        {footer && <div className="auth-footer">{footer}</div>}
      </motion.div>
    </div>
  );
}

export function Field({ label, icon: Icon, error, ...props }) {
  const Tag = props.rows ? "textarea" : "input";
  return (
    <label className={`field ${error ? "field-error" : ""}`}>
      <span className="field-label">{label}</span>
      <span className="field-control">
        {Icon && <Icon size={17} className="field-icon" />}
        <Tag {...props} />
      </span>
    </label>
  );
}
