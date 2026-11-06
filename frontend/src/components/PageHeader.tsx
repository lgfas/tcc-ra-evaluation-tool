import type { ReactNode } from 'react';

export default function PageHeader({ title, eyebrow, badge, actions }: {
  title: string; eyebrow?: ReactNode; badge?: ReactNode; actions?: ReactNode;
}) {
  return <header className="page-header">
    <div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <div className="title-row"><h1>{title}</h1>{badge}</div>
    </div>
    {actions && <div className="actions">{actions}</div>}
  </header>;
}
