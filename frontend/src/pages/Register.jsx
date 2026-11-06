import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AtSign, Lock, Mail, User, UserPlus } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import AuthLayout, { Field } from "../components/AuthLayout";

export default function Register() {
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", username: "", email: "", password: "", bio: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password.length < 6) return setError("Password must be at least 6 characters.");
    setBusy(true);
    try {
      await api.register({ ...form, bio: form.bio.trim() || null });
      await login(form.username, form.password);
      toast("Account created — welcome to Inkwell!", "success");
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout
      title="Join Inkwell"
      subtitle="Create an account and start sharing your ideas."
      footer={
        <>
          Already have an account? <Link to="/login">Log in</Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="form">
        <Field label="Full name" icon={User} value={form.name} onChange={set("name")} required autoFocus />
        <div className="form-row">
          <Field label="Username" icon={AtSign} value={form.username} onChange={set("username")} autoComplete="username" required />
          <Field label="Email" icon={Mail} type="email" value={form.email} onChange={set("email")} autoComplete="email" required />
        </div>
        <Field label="Password" icon={Lock} type="password" value={form.password} onChange={set("password")} autoComplete="new-password" required />
        <Field label="Bio (optional)" value={form.bio} onChange={set("bio")} rows={2} placeholder="A sentence about you" />
        {error && <p className="form-error">{error}</p>}
        <button className="btn btn-primary btn-block btn-glow" disabled={busy}>
          {busy ? <span className="spinner" /> : <UserPlus size={18} />} Create account
        </button>
      </form>
    </AuthLayout>
  );
}
