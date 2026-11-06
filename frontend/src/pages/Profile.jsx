import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Heart, Mail, MessageCircle, PenSquare, Settings, BookOpen } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Avatar from "../components/Avatar";
import BlogCard, { BlogCardSkeleton } from "../components/BlogCard";
import FollowButton from "../components/FollowButton";
import Loader from "../components/Loader";
import { gradientFor } from "../utils";

export default function Profile() {
  const { id } = useParams();
  const userId = Number(id);
  const { user: me } = useAuth();
  const [profile, setProfile] = useState(null);
  const [blogs, setBlogs] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setProfile(null);
    setBlogs(null);
    setError("");
    api.getUser(userId).then(setProfile).catch((e) => setError(e.message));
    api
      .getBlogs()
      .then((all) => setBlogs(all.filter((b) => b.author_id === userId).sort((a, b) => b.id - a.id)))
      .catch(() => setBlogs([]));
  }, [userId]);

  const stats = useMemo(
    () => ({
      likes: (blogs ?? []).reduce((n, b) => n + b.likes_count, 0),
      comments: (blogs ?? []).reduce((n, b) => n + b.comments_count, 0),
    }),
    [blogs]
  );

  if (error)
    return (
      <div className="page narrow">
        <div className="empty glass">
          <h3>User not found</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  if (!profile) return <Loader label="Loading profile" />;

  const isMe = me?.id === profile.id;

  return (
    <div className="page">
      <motion.section className="profile-hero glass" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="profile-banner" style={{ background: gradientFor(profile.id) }} />
        <div className="profile-main">
          <motion.div initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", delay: 0.15 }}>
            <Avatar user={profile} size={104} ring />
          </motion.div>
          <div className="profile-info">
            <h1>{profile.name}</h1>
            <p className="muted">@{profile.username}</p>
            {profile.bio && <p className="profile-bio">{profile.bio}</p>}
            {isMe && (
              <p className="muted small">
                <Mail size={13} /> {profile.email}
              </p>
            )}
          </div>
          <div className="profile-actions">
            {isMe ? (
              <>
                <Link to="/settings" className="btn btn-ghost btn-sm">
                  <Settings size={16} /> Edit profile
                </Link>
                <Link to="/write" className="btn btn-primary btn-sm">
                  <PenSquare size={16} /> New story
                </Link>
              </>
            ) : (
              me && <FollowButton targetId={profile.id} />
            )}
          </div>
        </div>
        <div className="profile-stats">
          <div><BookOpen size={16} /><strong>{blogs?.length ?? "–"}</strong><span>Stories</span></div>
          <div><Heart size={16} /><strong>{stats.likes}</strong><span>Likes received</span></div>
          <div><MessageCircle size={16} /><strong>{stats.comments}</strong><span>Responses</span></div>
        </div>
      </motion.section>

      <h2 className="section-title">{isMe ? "Your stories" : `Stories by ${profile.name.split(" ")[0]}`}</h2>

      {blogs && blogs.length === 0 && (
        <div className="empty glass">
          <h3>No stories yet</h3>
          <p>{isMe ? "Your published stories will appear here." : "This writer hasn't published anything yet."}</p>
          {isMe && (
            <Link to="/write" className="btn btn-primary">
              <PenSquare size={16} /> Write your first story
            </Link>
          )}
        </div>
      )}

      <div className="grid">
        {!blogs && Array.from({ length: 3 }).map((_, i) => <BlogCardSkeleton key={i} />)}
        {blogs?.map((b, i) => (
          <BlogCard key={b.id} blog={b} author={profile} index={i} />
        ))}
      </div>
    </div>
  );
}
