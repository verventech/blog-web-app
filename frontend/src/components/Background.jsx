import { useEffect, useRef } from "react";

export default function Background() {
  const spotlight = useRef(null);

  useEffect(() => {
    const onMove = (e) => {
      if (!spotlight.current) return;
      spotlight.current.style.setProperty("--x", `${e.clientX}px`);
      spotlight.current.style.setProperty("--y", `${e.clientY}px`);
    };
    window.addEventListener("pointermove", onMove);
    return () => window.removeEventListener("pointermove", onMove);
  }, []);

  return (
    <div className="bg" aria-hidden>
      <div className="blob blob-1" />
      <div className="blob blob-2" />
      <div className="blob blob-3" />
      <div className="grid-overlay" />
      <div className="noise" />
      <div className="spotlight" ref={spotlight} />
    </div>
  );
}
