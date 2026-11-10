import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AnimatePresence, motion, useScroll, useSpring } from "framer-motion";
import { ArrowLeft, Clock, Heart, MessageCircle, Send, Share2, Trash2 } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import Avatar from "../components/Avatar";
import Loader from "../components/Loader";
import FollowButton from "../components/FollowButton";
import Markdown from "../components/Markdown";
import useAuthors from "../hooks/useAuthors";
import { localSet, readingTime } from "../utils";

export default function BlogDetail() {
  const { id } = useParams();
  const blogId = Number(id);
  const { user } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const [blog, setBlog] = useState(null);
  const [comments, setComments] = useState([]);
  const [error, setError] = useState("");
  const [liked, setLiked] = useState(false);
  const [likeBusy, setLikeBusy] = useState(false);
  const [text, setText] = useState("");
  const [posting, setPosting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, { stiffness: 120, damping: 25 });

  useEffect(() => {
    setBlog(null);
    setError("");
    Promise.all([api.getBlog(blogId), api.getComments(blogId)])
      .then(([b, c]) => {
        setBlog(b);
        setComments(c);
      })
      .catch((e) => setError(e.message));
  }, [blogId]);

  useEffect(() => {
    setLiked(localSet.has("likes", user?.id, blogId));
  }, [user, blogId]);

  const people = useAuthors(blog ? [blog.author_id] : []);
  const author = blog ? people[blog.author_id] : null;
  const isOwner = user && blog && user.id === blog.author_id;

  const requireLogin = () => {
    toast("Log in to join the conversation", "info");
    navigate("/login", { state: { from: `/blog/${blogId}` } });
  };

  const handleLike = async () => {
    if (!user) return requireLogin();
    if (likeBusy) return;
    setLikeBusy(true);
    try {
      const res = await api.toggleLike(blogId);
      setLiked(res.liked);
      localSet.set("likes", user.id, blogId, res.liked);
      setBlog((b) => ({ ...b, likes_count: Math.max(0, b.likes_count + (res.liked ? 1 : -1)) }));
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setLikeBusy(false);
    }
  };

  const handleComment = async (e) => {
    e.preventDefault();
    if (!user) return requireLogin();
    if (!text.trim()) return;
    setPosting(true);
    try {
      const c = await api.addComment(blogId, text.trim());
      setComments((cs) => [...cs, c]);
      setBlog((b) => ({ ...b, comments_count: b.comments_count + 1 }));
      setText("");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setPosting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.deleteBlog(blogId);
      toast("Story deleted", "success");
      navigate("/");
    } catch (e) {
      toast(e.message, "error");
    }
  };

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast("Link copied to clipboard", "success");
    } catch {
      toast("Couldn't copy link", "error");
    }
  };

  if (error)
    return (
      <div className="page narrow">
        <div className="empty glass">
          <h3>Story not found</h3>
          <p>{error}</p>
          <Link to="/" className="btn btn-ghost">
            <ArrowLeft size={16} /> Back to stories
          </Link>
        </div>
      </div>
    );

  if (!blog) return <Loader label="Opening story" />;

  return (
    <>
      <motion.div className="read-progress" style={{ scaleX: progress }} />
      <motion.article
        className="page narrow article"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Link to="/" className="back-link">
          <ArrowLeft size={16} /> All stories
        </Link>

        <h1 className="article-title">{blog.title}</h1>

        <div className="article-meta">
          <Link to={`/user/${blog.author_id}`} className="author-block">
            <Avatar user={author ?? { id: blog.author_id, name: "?" }} size={40} />
            <div>
              <strong>{author?.name ?? "…"}</strong>
              <span>
                @{author?.username ?? "…"} · <Clock size={12} /> {readingTime(blog.content)} min read
              </span>
            </div>
          </Link>
          {user && !isOwner && <FollowButton targetId={blog.author_id} />}
        </div>

        <Markdown>{blog.content}</Markdown>

        <div className="action-bar glass">
          <button className={`action like ${liked ? "liked" : ""}`} onClick={handleLike} disabled={likeBusy}>
            <Heart size={18} fill={liked ? "currentColor" : "none"} />
            <span>{blog.likes_count}</span>
          </button>
          <a href="#comments" className="action">
            <MessageCircle size={20} /> <span>{blog.comments_count}</span>
          </a>
          <button className="action" onClick={handleShare}>
            <Share2 size={20} /> <span className="hide-sm">Share</span>
          </button>
          {isOwner && (
            <button className="action danger" onClick={() => setConfirmDelete(true)}>
              <Trash2 size={20} /> <span className="hide-sm">Delete</span>
            </button>
          )}
        </div>

        <section id="comments" className="comments">
          <h2>
            Responses <span className="count-badge">{comments.length}</span>
          </h2>

          <form className="comment-form glass" onSubmit={handleComment}>
            {user && <Avatar user={user} size={38} />}
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={user ? "Share your thoughts…" : "Log in to leave a response"}
              rows={2}
              onFocus={() => !user && requireLogin()}
            />
            <button className="btn btn-primary btn-icon" disabled={posting || !text.trim()} aria-label="Post response">
              <Send size={18} />
            </button>
          </form>

          <ul className="comment-list">
            <AnimatePresence initial={false}>
              {comments.map((c) => (
                <motion.li
                  key={c.id}
                  className="comment glass"
                  initial={{ opacity: 0, y: 12, height: 0 }}
                  animate={{ opacity: 1, y: 0, height: "auto" }}
                  transition={{ duration: 0.3 }}
                >
                  <div>
                    <div className="comment-head">
                      <span>{c.commenter_id}</span>
                    </div>
                    <p>{c.text}</p>
                  </div>
                </motion.li>
              ))}
            </AnimatePresence>
            {comments.length === 0 && <p className="muted center">No responses yet. Start the conversation.</p>}
          </ul>
        </section>
      </motion.article>

      <AnimatePresence>
        {confirmDelete && (
          <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setConfirmDelete(false)}>
            <motion.div
              className="modal glass"
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h3>Delete this story?</h3>
              <p className="muted">This permanently removes the story along with its likes and responses.</p>
              <div className="modal-actions">
                <button className="btn btn-ghost" onClick={() => setConfirmDelete(false)}>
                  Cancel
                </button>
                <button className="btn btn-danger" onClick={handleDelete}>
                  <Trash2 size={16} /> Delete
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
