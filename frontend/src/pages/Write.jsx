import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Eye, PenLine, Send } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import Avatar from "../components/Avatar";
import Markdown from "../components/Markdown";
import { readingTime } from "../utils";

const DRAFT_KEY = "inkwell_draft";

export default function Write() {
  const { user } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [draft, setDraft] = useState(() => JSON.parse(localStorage.getItem(DRAFT_KEY) || '{"title":"","content":""}'));
  const [preview, setPreview] = useState(false);
  const [busy, setBusy] = useState(false);
  const contentRef = useRef(null);

  useEffect(() => {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
  }, [draft]);

  useEffect(() => {
    const el = contentRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [draft.content, preview]);

  const words = draft.content.trim().split(/\s+/).filter(Boolean).length;
  const canPublish = draft.title.trim() && draft.content.trim();

  const publish = async () => {
    if (!canPublish) return;
    setBusy(true);
    try {
      const blog = await api.createBlog({ title: draft.title.trim(), content: draft.content.trim() });
      localStorage.removeItem(DRAFT_KEY);
      toast("Your story is live!", "success");
      navigate(`/blog/${blog.id}`);
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page narrow">
      <motion.div className="editor-bar glass" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="author-mini">
          <Avatar user={user} size={30} />
          <span>
            Draft · <span className="muted">{words} words · {readingTime(draft.content)} min read</span>
          </span>
        </div>
        <div className="editor-actions">
          <button className="btn btn-ghost btn-sm" onClick={() => setPreview((p) => !p)}>
            {preview ? <PenLine size={16} /> : <Eye size={16} />} {preview ? "Edit" : "Preview"}
          </button>
          <button className="btn btn-primary btn-sm btn-glow" onClick={publish} disabled={!canPublish || busy}>
            {busy ? <span className="spinner" /> : <Send size={16} />} Publish
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
