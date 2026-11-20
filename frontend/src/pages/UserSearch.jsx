import { useState } from "react";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { api } from "../api";
import Avatar from "../components/Avatar";

export default function UserSearch() {
  const [name, setName] = useState("");
  const [users, setUsers] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const search = async (event) => {
    event.preventDefault();
    const query = name.trim();
    if (!query) {
      setError("Enter a name to search.");
      setUsers(null);
      return;
    }

    setLoading(true);
    setError("");
    try {
      setUsers(await api.searchUsers(query));
    } catch (e) {
      setError(e.message);
      setUsers(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page narrow">
      <header className="page-head">
        <h1>Find people</h1>
        <p>Search writers by name.</p>
      </header>

      <form className="user-search-form" onSubmit={search}>
        <div className="search">
          <Search size={16} />
          <input
            aria-label="Name"
            autoComplete="off"
            maxLength={100}
            onChange={(event) => setName(event.target.value)}
            placeholder="Search by name"
            value={name}
          />
        </div>
        <button className="btn btn-primary" disabled={loading || !name.trim()}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <p className="form-error">{error}</p>}
      {users?.length === 0 && (
        <div className="empty">
          <h3>No people found</h3>
          <p>Try a different name.</p>
        </div>
      )}
      {users?.length > 0 && (
        <ul className="user-search-results">
          {users.map((user) => (
            <li key={user.id}>
              <Link className="user-search-result glass" to={`/user/${user.id}`}>
                <Avatar user={user} size={44} />
                <span className="user-search-info">
                  <strong>{user.name}</strong>
                  <span className="muted">@{user.username}</span>
                  {user.bio && <span className="user-search-bio">{user.bio}</span>}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
