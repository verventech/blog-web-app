import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="page narrow">
      <div className="empty glass">
        <h1 className="gradient-text big-404">404</h1>
        <h3>This page wandered off</h3>
        <p>The page you're looking for doesn't exist.</p>
        <Link to="/" className="btn btn-primary">
          <ArrowLeft size={16} /> Back home
        </Link>
      </div>
    </div>
  );
}
