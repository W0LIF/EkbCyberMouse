export interface LogoProps {
  compact?: boolean;
  variant?: "light" | "dark";
}

export function Logo({ compact = false }: LogoProps) {
  return (
    <div className={`logo ${compact ? "logo-compact" : ""}`}>
      <img
        src="/rostel.png"
        alt="Ростелеком"
        className="logo-img"
      />
    </div>
  );
}
