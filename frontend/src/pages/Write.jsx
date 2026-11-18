import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Eye, PenLine, Send } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import Avatar from "../components/Avatar";
import Loader from "../components/Loader";
import Markdown from "../components/Markdown";
import { readingTime } from "../utils";

const DRAFT_KEY = "inkwell_draft";

export default function Write() {
  const { id } = useParams();
  const editing = Boolean(id);
  const blogId = Number(id);
  const { user } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [draft, setDraft] = useState(() =>
    editing ? { title: "", content: "" } : JSON.parse(localStorage.getItem(DRAFT_KEY) || '{"title":"","content":""}')
  );
  const [editLoaded, setEditLoaded] = useState(!editing);
  const [preview, setPreview] = useState(false);
  const [busy, setBusy] = useState(false);
  const contentRef = useRef(null);

  useEffect(() => {
    if (!editing) localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
  }, [draft, editing]);

  useEffect(() => {
    if (!editing) return;
    let active = true;
    setEditLoaded(false);
    api.getBlog(blogId).then((blog) => {
      if (!active) return;
      if (blog.author_id !== user?.id) {
        toast("You can only edit your own story", "error");
        navigate(`/blog/${blogId}`, { replace: true });
        return;
      }
      setDraft({ title: blog.title, content: blog.content });
      setEditLoaded(true);
    }).catch((e) => {
      if (!active) return;
      toast(e.message, "error");
      navigate("/", { replace: true });
    });
    return () => {
      active = false;
    };
  }, [blogId, editing, navigate, toast, user?.id]);

  useEffect(() => {
    const el = contentRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [draft.content, preview]);

  const words = draft.content.trim().split(/\s+/).filter(Boolean).length;
  const canPublish = draft.title.trim() && draft.content.trim();

  const publish = async () => {
    if (!canPublish || !editLoaded) return;
    setBusy(true);
    try {
      const content = { title: draft.title.trim(), content: draft.content.trim() };
      const blog = editing
        ? await api.updateBlog(blogId, content)
        : await api.createBlog(content);
      if (!editing) localStorage.removeItem(DRAFT_KEY);
      toast(editing ? "Story updated" : "Your story is live!", "success");
      navigate(`/blog/${blog.id}`);
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(false);
    }
  };

  if (!editLoaded) return <Loader label="Loading story" />;

  return (
    <div className="page narrow">
      <motion.div className="editor-bar glass" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="author-mini">
          <Avatar user={user} size={30} />
          <span>
            {editing ? "Editing story" : "Draft"} · <span className="muted">{words} words · {readingTime(draft.content)} min read</span>
          </span>
        </div>
        <div className="editor-actions">
          {editing && (
            <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/blog/${blogId}`)}>
              <ArrowLeft size={16} /> Cancel
            </button>
          )}
          <button className="btn btn-ghost btn-sm" onClick={() => setPreview((p) => !p)}>
            {preview ? <PenLine size={16} /> : <Eye size={16} />} {preview ? "Edit" : "Preview"}
          </button>
          <button className="btn btn-primary btn-sm" onClick={publish} disabled={!canPublish || busy}>
            {busy ? <span className="spinner" /> : <Send size={16} />} {editing ? "Save changes" : "Publish"}
          </button>
        </div>
      </motion.div>

      <motion.div className="editor" key={preview ? "p" : "e"} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        {preview ? (
          <div className="article">
            <h1 className="article-title">{draft.title || "Untitled story"}</h1>
            <Markdown>{draft.content || "Nothing written yet."}</Markdown>
          </div>
        ) : (
          <>
            <input
              className="editor-title"
              placeholder="Title"
              value={draft.title}
              onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
              maxLength={255}
              autoFocus
            />
            <textarea
              ref={contentRef}
              className="editor-content"
              placeholder="Tell your story… (Markdown supported)"
              value={draft.content}
              onChange={(e) => setDraft((d) => ({ ...d, content: e.target.value }))}
            />
          </>
        )}
      </motion.div>
    </div>
  );
}
