import { useEffect, useRef, type ReactNode } from "react";

export default function EvidenceDialog({
  children,
  onClose,
}: {
  children: ReactNode;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    const trigger =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const previousOverflow = document.body.style.overflow;
    element?.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      element?.close();
      document.body.style.overflow = previousOverflow;
      trigger?.focus();
    };
  }, []);

  return (
    <dialog
      ref={dialog}
      className="evidence-drawer"
      aria-label="Source evidence"
      onCancel={onClose}
      style={{
        margin: "0 0 0 auto",
        maxWidth: "100vw",
        maxHeight: "100dvh",
        height: "100dvh",
        color: "inherit",
      }}
    >
      {children}
    </dialog>
  );
}
