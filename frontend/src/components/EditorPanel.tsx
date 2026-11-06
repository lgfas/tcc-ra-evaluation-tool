import { useEffect, useId, useRef, type ReactNode } from 'react';

// Native dialog handles the focus trap; restore focus after React re-enables the opener.
export default function EditorPanel({ title, children, onClose, busy = false }: {
  title: string; children: ReactNode; onClose: () => void; busy?: boolean;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const node = dialog.current;
    const opener = document.activeElement;
    node?.showModal();
    return () => {
      node?.close();
      requestAnimationFrame(() => {
        if (!node?.open && opener instanceof HTMLElement && opener.isConnected) opener.focus();
      });
    };
  }, []);
  return <dialog ref={dialog} className="editor-panel" aria-labelledby={titleId}
    onCancel={event => { event.preventDefault(); if (!busy) onClose(); }}>
    <div className="editor-header"><h2 id={titleId}>{title}</h2>
      <button type="button" className="icon-button secondary" aria-label="Fechar painel" disabled={busy} onClick={onClose}>×</button>
    </div>
    {children}
  </dialog>;
}
