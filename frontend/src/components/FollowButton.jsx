import { useEffect, useState } from "react";
import { UserCheck, UserPlus } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { localSet } from "../utils";

export default function FollowButton({ targetId }) {
  const { user } = useAuth();
  const toast = useToast();
  const [following, setFollowing] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setFollowing(localSet.has("follows", user?.id, targetId));
  }, [user, targetId]);

  const toggle = async () => {
    setBusy(true);
    try {
      const res = await api.toggleFollow(targetId);
      setFollowing(res.following);
      localSet.set("follows", user.id, targetId, res.following);
      toast(res.following ? "Following" : "Unfollowed", "success");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <button className={`btn btn-sm ${following ? "btn-ghost" : "btn-primary"}`} onClick={toggle} disabled={busy}>
      {following ? <UserCheck size={16} /> : <UserPlus size={16} />}
      {following ? "Following" : "Follow"}
    </button>
  );
}
