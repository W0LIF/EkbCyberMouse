import type { ReactNode } from "react";
import { Tooltip } from "./Tooltip";

export interface StatusProps {
  children: string;
}

export function Status({ children }: StatusProps) {
  const key = children.toLowerCase().replace(" ", "-");
  return (
    <Tooltip text={`Статус наряда: ${children}`}>
      <span className={`status status-${key}`}>{children}</span>
    </Tooltip>
  );
}
