import { gradientFor, initials } from "../utils";

export default function Avatar({ user, size = 40, ring = false }) {
  return (
    <div
      className={`avatar ${ring ? "avatar-ring" : ""}`}
      style={{
        width: size,
        height: size,
        fontSize: size * 0.4,
        background: gradientFor(user?.id ?? user?.username ?? 0),
      }}
      title={user?.name}
    >
      {initials(user?.name)}
    </div>
  );
}
