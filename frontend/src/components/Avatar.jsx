import { colorFor, initials } from "../utils";

export default function Avatar({ user, size = 40 }) {
  return (
    <div
      className="avatar"
      style={{
        width: size,
        height: size,
        fontSize: size * 0.38,
        background: colorFor(user?.id ?? user?.username ?? 0),
      }}
      title={user?.name}
    >
      {initials(user?.name)}
    </div>
  );
}
