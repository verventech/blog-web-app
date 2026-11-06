import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Flame, MessagesSquare, Search, Sparkles, PenSquare, RefreshCw } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import BlogCard, { BlogCardSkeleton } from "../components/BlogCard";
import useAuthors from "../hooks/useAuthors";

const SORTS = [
  { id: "latest", label: "Latest", icon: Sparkles, fn: (a, b) => b.id - a.id },
  { id: "popular", label: "Popular", icon: Flame, fn: (a, b) => b.likes_count - a.likes_count || b.id - a.id },
  { id: "discussed", label: "Discussed", icon: MessagesSquare, fn: (a, b) => b.comments_count - a.comments_count || b.id - a.id },
];

const HEADLINE = ["Ideas", "worth", "sharing."];

export default function Home() {
  const { user } = useAuth();
  const [blogs, setBlogs] = useState(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("latest");

  const load = () => {
    setError("");
    setBlogs(null);
    api.getBlogs().then(setBlogs).catch((e) => {
      setError(e.message);
      setBlogs([]);
    });
  };

  useEffect(load, []);

  const authors = useAuthors((blogs ?? []).map((b) => b.author_id));

  const visible = useMemo(() => {
    if (!blogs) return [];
    const q = query.trim().toLowerCase();
    const filtered = q
      ? blogs.filter(
          (b) =>
            b.title.toLowerCase().includes(q) ||
            b.content.toLowerCase().includes(q) ||
            authors[b.author_id]?.name?.toLowerCase().includes(q)
        )
      : blogs;
    return [...filtered].sort(SORTS.find((s) => s.id === sort).fn);
  }, [blogs, query, sort, authors]);

  const totals = useMemo(
    () => ({
      stories: blogs?.length ?? 0,
      writers: new Set((blogs ?? []).map((b) => b.author_id)).size,
      likes: (blogs ?? []).reduce((n, b) => n + b.likes_count, 0),
    }),
    [blogs]
  );

  return (
    <div className="page">
      <section className="hero">
        <motion.span
          className="eyebrow"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Sparkles size={14} /> A home for curious minds
        </motion.span>
        <h1 className="hero-title">
          {HEADLINE.map((word, i) => (
            <motion.span
              key={word}
              className={i === 2 ? "gradient-text" : ""}
              initial={{ opacity: 0, y: 40, filter: "blur(8px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{ delay: 0.15 + i * 0.12, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            >
              {word}
            </motion.span>
          ))}
        </h1>
        <motion.p
          className="hero-sub"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.55 }}
        >
          Read stories from thoughtful writers, join the conversation, and publish your own in seconds.
        </motion.p>
        <motion.div
          className="hero-cta"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <Link to={user ? "/write" : "/register"} className="btn btn-primary btn-lg btn-glow">
            <PenSquare size={18} /> {user ? "Write a story" : "Start writing"}
          </Link>
          <a href="#feed" className="btn btn-ghost btn-lg">
            Explore stories
          </a>
        </motion.div>

        <motion.div
          className="hero-stats"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.85 }}
        >
          <div><strong>{totals.stories}</strong><span>Stories</span></div>
          <div><strong>{totals.writers}</strong><span>Writers</span></div>
          <div><strong>{totals.likes}</strong><span>Likes</span></div>
        </motion.div>
      </section>

      <section id="feed" className="feed">
        <div className="toolbar glass">
          <div className="search">
            <Search size={18} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search stories, topics or writers…"
            />
          </div>
          <div className="tabs">
            {SORTS.map(({ id, label, icon: Icon }) => (
              <button key={id} className={`tab ${sort === id ? "active" : ""}`} onClick={() => setSort(id)}>
                {sort === id && <motion.span layoutId="tab-pill" className="tab-pill" />}
                <span className="tab-label">
                  <Icon size={15} /> {label}
                </span>
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="empty glass">
            <h3>Couldn't load stories</h3>
            <p>{error}</p>
            <button className="btn btn-ghost" onClick={load}>
              <RefreshCw size={16} /> Try again
            </button>
          </div>
        )}

        {!error && blogs && visible.length === 0 && (
          <div className="empty glass">
            <h3>{query ? "No matches" : "No stories yet"}</h3>
            <p>{query ? "Try a different search term." : "Be the first to publish something wonderful."}</p>
            {!query && (
              <Link to={user ? "/write" : "/register"} className="btn btn-primary">
                <PenSquare size={16} /> Write the first story
              </Link>
            )}
          </div>
        )}

        <div className="grid">
          {!blogs && Array.from({ length: 6 }).map((_, i) => <BlogCardSkeleton key={i} />)}
          {visible.map((b, i) => (
            <BlogCard
              key={b.id}
              blog={b}
              author={authors[b.author_id]}
              index={i}
              featured={i === 0 && !query && visible.length > 2}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
