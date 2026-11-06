const CARD_THEMES = [
  { solid: "#1d6a8a", soft: "#d4eef7" },
  { solid: "#2f7d4a", soft: "#d7f3e2" },
  { solid: "#c45c12", soft: "#fde6d0" },
  { solid: "#7a4e9a", soft: "#f0e4f8" },
  { solid: "#c2414a", soft: "#fde4e6" },
  { solid: "#0f766e", soft: "#d2f4ef" },
  { solid: "#b45309", soft: "#fef0c7" },
  { solid: "#3b5bdb", soft: "#e0e7ff" },
];

function seedNumber(seed = 0) {
  return typeof seed === "number" ? seed : [...String(seed)].reduce((a, c) => a + c.charCodeAt(0), 0);
}

export function colorFor(seed = 0) {
  return CARD_THEMES[Math.abs(seedNumber(seed)) % CARD_THEMES.length].solid;
}

export function cardTheme(seed = 0) {
  return CARD_THEMES[Math.abs(seedNumber(seed)) % CARD_THEMES.length];
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
