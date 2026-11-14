import type { ReactNode } from "react";

export interface PageIntroProps {
  eyebrow?: string;
  eyebrowTone?: "green" | "warn" | "purple";
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  live?: boolean;
}

export function PageIntro({
  eyebrow,
  eyebrowTone = "green",
  title,
  subtitle,
  actions,
  live,
}: PageIntroProps) {
  return (
    <div className="page-intro">
      <div>
        {eyebrow && <div className={`eyebrow ${eyebrowTone}`}>{eyebrow}</div>}
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {live && (
        <div className="live">
          <i /> Данные в реальном времени
        </div>
      )}
      {actions}
    </div>
  );
}
