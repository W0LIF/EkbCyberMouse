import type { ReactNode } from "react";

export interface ButtonProps {
  children?: ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "purple" | "danger";
  onClick?: () => void;
  icon?: ReactNode;
  type?: "button" | "submit";
  disabled?: boolean;
}

export function Button({
  children,
  variant = "primary",
  onClick,
  icon,
  type = "button",
  disabled = false,
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`btn btn-${variant}`}
    >
      {icon}
      {children}
    </button>
  );
}
