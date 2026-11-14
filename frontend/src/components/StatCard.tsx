export default function StatCard({ label, value, hint }: {label: string; value?: number | string; hint?: string}) {
  return <div className="stat-card"><strong>{value ?? '—'}</strong><span>{label}</span>{hint && <small>{hint}</small>}</div>;
}
