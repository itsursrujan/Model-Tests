import { useStore } from '../store/useStore'

export function Header() {
  const status = useStore((state: any) => state.status)

  return (
    <header className="fixed top-0 left-0 right-0 h-14 bg-black/80 backdrop-blur-md border-b border-white/5 flex items-center justify-between px-6 z-[1000]">
      <div className="flex items-center gap-3">
        <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse shadow-[0_0_8px_var(--primary-glow)]" />
        <span className="text-[10px] font-black tracking-[0.2em] uppercase text-white/90">Scan Image</span>
      </div>

      <div className="flex items-center gap-2">
        <div className="w-6 h-6 rounded-full border border-primary/30 flex items-center justify-center">
            <div className="w-1 h-1 rounded-full bg-primary shadow-[0_0_10px_var(--primary-glow)]" />
        </div>
      </div>

      <div className="flex items-center gap-6">

        <div className="flex items-center gap-2">
            <span className="text-[9px] font-black tracking-widest text-white/30 uppercase">{status}</span>
        </div>
      </div>
    </header>
  )
}
