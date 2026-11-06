const GRADIENTS = [
  ["#7c3aed", "#ec4899"],
  ["#06b6d4", "#3b82f6"],
  ["#f59e0b", "#ef4444"],
  ["#10b981", "#06b6d4"],
  ["#8b5cf6", "#06b6d4"],
  ["#f43f5e", "#f59e0b"],
  ["#22c55e", "#84cc16"],
  ["#6366f1", "#a855f7"],
];

export function gradientFor(seed = 0) {
  const n = typeof seed === "number" ? seed : [...String(seed)].reduce((a, c) => a + c.charCodeAt(0), 0);
  const [a, b] = GRADIENTS[Math.abs(n) % GRADIENTS.length];
  return `linear-gradient(135deg, ${a}, ${b})`;
}

export function initials(name = "") {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("") || "?";
}

export function readingTime(text = "") {
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 200));
}

function stripMarkdown(text) {
  return text
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/^\s{0,3}(#{1,6}|>|[-*+]|\d+\.)\s+/gm, "")
    .replace(/^\s*([-*_]\s*){3,}$/gm, " ")
    .replace(/[*_~`]+/g, "");
}

export function excerpt(text = "", len = 160) {
  const clean = stripMarkdown(text).replace(/\s+/g, " ").trim();
  return clean.length > len ? `${clean.slice(0, len).trimEnd()}…` : clean;
}

// The API doesn't expose per-user like/follow state, so it's remembered locally per account.
function setKey(kind, userId) {
  return `inkwell_${kind}_${userId}`;
}

export const localSet = {
  has(kind, userId, id) {
    if (!userId) return false;
    const list = JSON.parse(localStorage.getItem(setKey(kind, userId)) || "[]");
    return list.includes(id);
  },
  set(kind, userId, id, on) {
    if (!userId) return;
    const key = setKey(kind, userId);
    const list = new Set(JSON.parse(localStorage.getItem(key) || "[]"));
    on ? list.add(id) : list.delete(id);
    localStorage.setItem(key, JSON.stringify([...list]));
  },
};
