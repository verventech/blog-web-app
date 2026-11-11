import { Link } from "react-router-dom";
import { Clock, Heart, MessageCircle } from "lucide-react";
import Avatar from "./Avatar";
import { cardTheme, excerpt, readingTime } from "../utils";

export default function BlogCard({ blog }) {
  const theme = cardTheme(blog.id);
  return (
    <Link
      to={`/blog/${blog.id}`}
      className="story"
      style={{ "--card": theme.solid, "--card-soft": theme.soft }}
    >
      <div className="story-band">
        <span className="story-letter">{blog.title?.[0]?.toUpperCase()}</span>
        <span className="story-time">
          <Clock size={12} /> {readingTime(blog.content)} min
        </span>
      </div>
      <div className="story-body">
        <h3 className="story-title">{blog.title}</h3>
        <p className="story-excerpt">{excerpt(blog.content, 180)}</p>
        <div className="story-foot">
          <div className="author-mini">
            <Avatar
              user={{ id: blog.author_id, name: blog.author_name, username: blog.author_username }}
              size={22}
            />
            <span>{blog.author_name}</span>
          </div>
          <div className="stats">
            <span className="stat-like">
              <Heart size={13} /> {blog.likes_count}
            </span>
            <span className="stat-comment">
              <MessageCircle size={13} /> {blog.comments_count}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}

export function BlogCardSkeleton() {
  return (
    <div className="story-skel">
      <div className="story-band shimmer" />
      <div className="story-body">
        <div className="sk-line shimmer" style={{ width: "55%", height: 18, marginTop: 0 }} />
        <div className="sk-line shimmer" />
        <div className="sk-line shimmer" style={{ width: "35%" }} />
      </div>
    </div>
  );
}
