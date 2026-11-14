export interface ChipsProps {
  items: string[];
  selected?: string;
  onSelect?: (item: string) => void;
}

export function Chips({ items, selected, onSelect }: ChipsProps) {
  return (
    <div className="chips">
      {items.map((item) => (
        <button
          className={selected === item ? "selected" : ""}
          onClick={() => onSelect?.(item)}
          key={item}
        >
          {item}
        </button>
      ))}
    </div>
  );
}
