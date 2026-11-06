import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search, PenSquare, RefreshCw } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import BlogCard, { BlogCardSkeleton } from "../components/BlogCard";
import useAuthors from "../hooks/useAuthors";

const SORTS = [
  { id: "latest", label: "Latest", fn: (a, b) => b.id - a.id },
  { id: "popular", label: "Popular", fn: (a, b) => b.likes_count - a.likes_count || b.id - a.id },
  { id: "discussed", label: "Discussed", fn: (a, b) => b.comments_count - a.comments_count || b.id - a.id },
];

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

  return (
    <div className="page page-wide">
      <header className="page-head">
        <h1>Stories</h1>
        <p>Recent writing from people on Inkwell.</p>
      </header>

      <div className="toolbar">
        <div className="search">
          <Search size={16} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search"
          />
        </div>
        <div className="tabs">
          {SORTS.map(({ id, label }) => (
            <button key={id} className={`tab ${sort === id ? "active" : ""}`} onClick={() => setSort(id)}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="empty">
          <h3>Couldn't load stories</h3>
          <p>{error}</p>
          <button className="btn btn-ghost" onClick={load}>
            <RefreshCw size={16} /> Try again
          </button>
        </div>
      )}

      {!error && blogs && visible.length === 0 && (
        <div className="empty">
          <h3>{query ? "No matches" : "No stories yet"}</h3>
          <p>{query ? "Try a different search." : "Nothing has been published yet."}</p>
          {!query && (
            <Link to={user ? "/write" : "/register"} className="btn btn-primary">
              <PenSquare size={16} /> Write a story
            </Link>
          )}
        </div>
      )}

      <div className="story-list">
        {!blogs && Array.from({ length: 4 }).map((_, i) => <BlogCardSkeleton key={i} />)}
        {visible.map((b) => (
          <BlogCard key={b.id} blog={b} author={authors[b.author_id]} />
        ))}
      </div>
    </div>
  );
}
