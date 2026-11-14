export interface BrandMarkProps {
  size?: number;
  className?: string;
}

export function BrandMark({ size = 76, className = "" }: BrandMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Основной фиолетовый элемент — фирменный знак Ростелекома */}
      <path
        d="M50 4 L86 46 L86 88 L50 54 Z"
        fill="#7C3AED"
      />
      {/* Оранжевый акцент */}
      <path
        d="M50 66 L86 66 L86 88 Z"
        fill="#FF6B00"
      />
    </svg>
  );
}
