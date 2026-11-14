import {
  type CSSProperties,
  type ReactNode,
  useCallback,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";

export interface TooltipProps {
  text: string;
  children: ReactNode;
  side?: "top" | "bottom" | "left" | "right" | "auto";
}

const GAP = 8;
const VIEWPORT_PAD = 8;

type Placement = "top" | "bottom" | "left" | "right";

function fits(rect: DOMRect, tipW: number, tipH: number, p: Placement) {
  if (p === "top") return rect.top - tipH - GAP >= VIEWPORT_PAD;
  if (p === "bottom") return rect.bottom + tipH + GAP <= window.innerHeight - VIEWPORT_PAD;
  if (p === "left") return rect.left - tipW - GAP >= VIEWPORT_PAD;
  return rect.right + tipW + GAP <= window.innerWidth - VIEWPORT_PAD;
}

function pickPlacement(rect: DOMRect, tipW: number, tipH: number, prefer: Placement): Placement {
  if (fits(rect, tipW, tipH, prefer)) return prefer;
  const order: Placement[] = ["bottom", "top", "right", "left"];
  for (const p of order) if (fits(rect, tipW, tipH, p)) return p;
  return prefer;
}

export function Tooltip({ text, children, side = "auto" }: TooltipProps) {
  const id = useId();
  const anchorRef = useRef<HTMLSpanElement | null>(null);
  const tipRef = useRef<HTMLSpanElement | null>(null);
  const [open, setOpen] = useState(false);
  const [place, setPlace] = useState<Placement>("top");
  const [style, setStyle] = useState<CSSProperties>({
    position: "fixed",
    left: 0,
    top: 0,
    opacity: 0,
    visibility: "hidden",
  });

  const recompute = useCallback(() => {
    const anchor = anchorRef.current;
    const tip = tipRef.current;
    if (!anchor || !tip) return;
    const rect = anchor.getBoundingClientRect();
    const tipW = tip.offsetWidth;
    const tipH = tip.offsetHeight;

    const preferred: Placement =
      side === "auto" ? (rect.top < 160 ? "bottom" : "top") : (side as Placement);
    const resolved = pickPlacement(rect, tipW, tipH, preferred);

    let left = 0;
    let top = 0;
    if (resolved === "top" || resolved === "bottom") {
      left = rect.left + rect.width / 2 - tipW / 2;
      top = resolved === "top" ? rect.top - tipH - GAP : rect.bottom + GAP;
      left = Math.max(VIEWPORT_PAD, Math.min(left, window.innerWidth - tipW - VIEWPORT_PAD));
    } else if (resolved === "left") {
      left = rect.left - tipW - GAP;
      top = rect.top + rect.height / 2 - tipH / 2;
    } else {
      left = rect.right + GAP;
      top = rect.top + rect.height / 2 - tipH / 2;
    }
    top = Math.max(VIEWPORT_PAD, Math.min(top, window.innerHeight - tipH - VIEWPORT_PAD));

    setPlace(resolved);
    setStyle({ position: "fixed", left, top, opacity: 1, visibility: "visible" });
  }, [side]);

  useLayoutEffect(() => {
    if (!open) return;
    recompute();
    const onMove = () => recompute();
    window.addEventListener("scroll", onMove, true);
    window.addEventListener("resize", onMove);
    return () => {
      window.removeEventListener("scroll", onMove, true);
      window.removeEventListener("resize", onMove);
    };
  }, [open, recompute]);

  if (!text) return <>{children}</>;

  return (
    <>
      <span
        ref={anchorRef}
        className="tooltip-wrap"
        tabIndex={0}
        aria-describedby={open ? id : undefined}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
      >
        {children}
      </span>
      {open &&
        createPortal(
          <span
            ref={tipRef}
            id={id}
            role="tooltip"
            className={`tooltip tooltip--${place}`}
            style={style}
          >
            {text}
          </span>,
          document.body,
        )}
    </>
  );
}
