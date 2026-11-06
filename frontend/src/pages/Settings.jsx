import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AtSign, Lock, Mail, Save, User } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import AuthLayout, { Field } from "../components/AuthLayout";

export default function Settings() {
  const { user, setUser, logout } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: user.name,
    username: user.username,
    email: user.email,
    bio: user.bio ?? "",
    password: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password && form.password.length < 6) return setError("New password must be at least 6 characters.");
    setBusy(true);
    try {
      const updated = await api.updateMe({
        ...form,
        bio: form.bio.trim() || null,
        password: form.password || null,
      });
      api.invalidateUser(updated.id);
      // The JWT subject is the username, so the old token stops working after a rename.
      if (updated.username !== user.username) {
        logout();
        toast("Username changed — please log in again", "info");
        navigate("/login");
        return;
      }
      setUser(updated);
      toast("Profile updated", "success");
      navigate(`/user/${updated.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout title="Edit profile" subtitle="Update how others see you on Inkwell.">
      <form onSubmit={onSubmit} className="form">
        <Field label="Full name" icon={User} value={form.name} onChange={set("name")} required />
        <div className="form-row">
          <Field label="Username" icon={AtSign} value={form.username} onChange={set("username")} required />
          <Field label="Email" icon={Mail} type="email" value={form.email} onChange={set("email")} required />
        </div>
        <Field label="Bio" value={form.bio} onChange={set("bio")} rows={3} placeholder="A sentence about you" />
        <Field
          label="New password (leave blank to keep current)"
          icon={Lock}
          type="password"
          value={form.password}
          onChange={set("password")}
          autoComplete="new-password"
        />
        {error && <p className="form-error">{error}</p>}
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? <span className="spinner" /> : <Save size={18} />} Save changes
        </button>
      </form>
    </AuthLayout>
  );
}
