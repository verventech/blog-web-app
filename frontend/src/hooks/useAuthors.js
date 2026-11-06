import { useEffect, useState } from "react";
import { api } from "../api";

export default function useAuthors(ids) {
  const [authors, setAuthors] = useState({});
  const key = [...new Set(ids)].sort((a, b) => a - b).join(",");

  useEffect(() => {
    if (!key) return;
    let cancelled = false;
    const unique = key.split(",").map(Number);
    Promise.allSettled(unique.map((id) => api.getUser(id))).then((results) => {
      if (cancelled) return;
      const map = {};
      results.forEach((r, i) => {
        map[unique[i]] =
          r.status === "fulfilled" ? r.value : { id: unique[i], name: "Unknown author", username: "unknown" };
      });
      setAuthors((prev) => ({ ...prev, ...map }));
    });
    return () => {
      cancelled = true;
    };
  }, [key]);

  return authors;
}
