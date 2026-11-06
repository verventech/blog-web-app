export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="page auth-page">
      <div className="auth-card">
        <h1>{title}</h1>
        <p className="muted">{subtitle}</p>
        {children}
        {footer && <div className="auth-footer">{footer}</div>}
      </div>
    </div>
  );
}

export function Field({ label, icon: Icon, error, ...props }) {
  const Tag = props.rows ? "textarea" : "input";
  return (
    <label className={`field ${error ? "field-error" : ""}`}>
      <span className="field-label">{label}</span>
      <span className="field-control">
        {Icon && <Icon size={16} className="field-icon" />}
        <Tag {...props} />
      </span>
    </label>
  );
}
