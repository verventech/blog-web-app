export default function Loader({ label = "Loading" }) {
  return (
    <div className="loader-wrap">
      <div className="loader">
        <span />
        <span />
        <span />
      </div>
      <p>{label}…</p>
    </div>
  );
}
