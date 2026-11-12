export function moveItem<T>(items: T[], index: number, direction: -1 | 1): T[] {
  const result = [...items];
  const target = index + direction;
  if (target >= 0 && target < result.length) [result[index], result[target]] = [result[target], result[index]];
  return result;
}

export default function MoveControls({ label, index, count, disabled = false, onMove }: {
  label: string; index: number; count: number; disabled?: boolean; onMove: (direction: -1 | 1) => void;
}) {
  return <span className="move-controls">
    <button type="button" className="secondary" aria-label={`Mover ${label} para cima`} disabled={disabled || index === 0} onClick={() => onMove(-1)}>↑</button>
    <button type="button" className="secondary" aria-label={`Mover ${label} para baixo`} disabled={disabled || index === count - 1} onClick={() => onMove(1)}>↓</button>
  </span>;
}
