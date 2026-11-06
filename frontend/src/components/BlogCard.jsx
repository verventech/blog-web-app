import { useRef } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Clock, Heart, MessageCircle } from "lucide-react";
import Avatar from "./Avatar";
import { excerpt, gradientFor, readingTime } from "../utils";

export default function BlogCard({ blog, author, index = 0, featured = false }) {
  const ref = useRef(null);

  const onMove = (e) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width;
    const py = (e.clientY - r.top) / r.height;
    el.style.setProperty("--mx", `${px * 100}%`);
    el.style.setProperty("--my", `${py * 100}%`);
    el.style.setProperty("--rx", `${(0.5 - py) * 6}deg`);
    el.style.setProperty("--ry", `${(px - 0.5) * 6}deg`);
  };

  const onLeave = () => {
    ref.current?.style.setProperty("--rx", "0deg");
    ref.current?.style.setProperty("--ry", "0deg");
  };

  return (
    <motion.article
      className={`card-wrap ${featured ? "card-featured" : ""}`}
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: Math.min(index, 8) * 0.06, ease: [0.22, 1, 0.36, 1] }}
      layout
    >
      <Link to={`/blog/${blog.id}`} className="card" ref={ref} onMouseMove={onMove} onMouseLeave={onLeave}>
        <div className="card-cover" style={{ background: gradientFor(blog.id * 7 + blog.author_id) }}>
          <span className="card-cover-letter">{blog.title?.[0]?.toUpperCase()}</span>
          <span className="chip chip-glass">
            <Clock size={12} /> {readingTime(blog.content)} min read
          </span>
        </div>
        <div className="card-body">
          <h3 className="card-title">{blog.title}</h3>
          <p className="card-excerpt">{excerpt(blog.content, featured ? 260 : 140)}</p>
          <div className="card-foot">
            <div className="author-mini">
              <Avatar user={author ?? { id: blog.author_id, name: "?" }} size={28} />
              <span>{author?.name ?? "Loading…"}</span>
            </div>
            <div className="stats">
              <span>
                <Heart size={14} /> {blog.likes_count}
              </span>
              <span>
                <MessageCircle size={14} /> {blog.comments_count}
              </span>
            </div>
          </div>
        </div>
      </Link>
    </motion.article>
  );
}

export function BlogCardSkeleton() {
  return (
    <div className="card-wrap">
      <div className="card skeleton-card">
        <div className="card-cover shimmer" />
        <div className="card-body">
          <div className="sk-line shimmer" style={{ width: "80%", height: 22 }} />
          <div className="sk-line shimmer" />
          <div className="sk-line shimmer" style={{ width: "60%" }} />
        </div>
      </div>
    </div>
  );
}
