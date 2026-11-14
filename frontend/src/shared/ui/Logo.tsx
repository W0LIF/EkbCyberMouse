export interface LogoProps {
  compact?: boolean;
}

export function Logo({ compact = false }: LogoProps) {
  return (
    <div className="logo">
      <span className="logo-mark">
        <i />
        <i />
        <i />
      </span>
      {!compact && (
        <span>
          <b>Ростелеком</b>
          <small>Диспетчеризация · Екб</small>
        </span>
      )}
    </div>
  );
}
