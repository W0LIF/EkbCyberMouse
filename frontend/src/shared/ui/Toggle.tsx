export interface ToggleProps {
  active: boolean;
  onClick: () => void;
}

export function Toggle({ active, onClick }: ToggleProps) {
  return (
    <button className={`toggle ${active ? "on" : ""}`} onClick={onClick} role="switch">
      <i />
    </button>
  );
}
