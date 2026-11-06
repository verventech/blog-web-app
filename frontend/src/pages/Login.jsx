import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AtSign, Lock, LogIn } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import AuthLayout, { Field } from "../components/AuthLayout";

export default function Login() {
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const me = await login(form.username, form.password);
      toast(`Welcome back, ${me.name.split(" ")[0]}!`, "success");
      navigate(location.state?.from || "/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to like, comment and publish stories."
      footer={
        <>
          New to Inkwell? <Link to="/register">Create an account</Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="form">
        <Field label="Username" icon={AtSign} value={form.username} onChange={set("username")} autoComplete="username" required autoFocus />
        <Field label="Password" icon={Lock} type="password" value={form.password} onChange={set("password")} autoComplete="current-password" required />
        {error && <p className="form-error">{error}</p>}
        <button className="btn btn-primary btn-block btn-glow" disabled={busy}>
          {busy ? <span className="spinner" /> : <LogIn size={18} />} Log in
        </button>
      </form>
    </AuthLayout>
  );
}
