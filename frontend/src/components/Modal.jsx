import { useEffect, useRef } from 'react'

export default function Modal({ label, onClose, busy = false, children, wide = false }) {
  const ref = useRef(null)
  useEffect(() => {
    const dialog = ref.current
    dialog.showModal()
    return () => dialog.close()
  }, [])
  return <dialog ref={ref} aria-label={label} className={`research-modal ${wide ? 'research-modal-wide' : ''}`}
    onCancel={(event) => { event.preventDefault(); if (!busy) onClose() }}
    onClick={(event) => { if (!busy && event.target === event.currentTarget) onClose() }}>
    <div className="research-modal-body">{children}</div>
  </dialog>
}
