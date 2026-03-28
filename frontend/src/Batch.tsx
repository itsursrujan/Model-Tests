import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { Layers, Upload, CheckCircle, FileText, X, Zap, Key, AlertTriangle } from 'lucide-react'
import { stegoApi } from '@/services/api'
import { useStore } from '@/store/useStore'

function PowerBar({ progress, active }: { progress: number; active: boolean }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="flex gap-1 h-12 items-end">
        {[...Array(10)].map((_, i) => {
          const threshold = (i / 9) * 100
          const isActive = active && progress >= threshold
          return (
            <motion.div
              key={i}
              className={`w-1 rounded-sm transition-all duration-300 ${isActive ? 'bg-primary shadow-[0_0_8px_var(--primary-glow)]' : 'bg-[var(--border)]'}`}
              animate={{ height: isActive ? '100%' : '30%', opacity: isActive ? [0.7, 1, 0.8] : 0.2 }}
              transition={isActive ? { repeat: Infinity, duration: 0.25 } : {}}
            />
          )
        })}
      </div>
      <div className="font-mono text-xs font-black text-primary tracking-tighter">
        {active ? `${progress.toFixed(0)}%` : 'BATCH_IDLE'}
      </div>
    </div>
  )
}

export function Batch() {
  const [files, setFiles] = useState<File[]>([])
  const [secret, setSecret] = useState<File | null>(null)
  const [mode, setMode] = useState<'hide' | 'extract' | 'scan'>('hide')
  const [password, setPassword] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [isSuccess, setIsSuccess] = useState(false)
  const [batchResults, setBatchResults] = useState<any[] | null>(null)
  const [method, setMethod] = useState<'lsb' | 'adaptive'>('lsb')
  const setStatus = useStore(s => s.setStatus)

  const onDropFiles = useCallback((f: File[]) => { setFiles(p => [...p, ...f].slice(0, 50)); setError(null) }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop: onDropFiles, accept: { 'image/*': [] } })
  const { getRootProps: getSecretProps, getInputProps: getSecretInputProps } = useDropzone({ onDrop: f => setSecret(f[0]), multiple: false })

  const handleBatch = async () => {
    if (files.length === 0 || (mode === 'hide' && !secret)) return

    let promptMsg = ''
    if (mode === 'hide') promptMsg = `Batch embedding will process ${files.length} files. Estimated cost: ${files.length * 2} credits. Continue?`
    else if (mode === 'extract') promptMsg = `Batch extraction will process ${files.length} files. Estimated cost: ${files.length * 2} credits. Continue?`
    else promptMsg = `Batch scan will process ${files.length} images. Estimated cost: ${files.length * 2} credits. Continue?`

    if (!window.confirm(promptMsg)) return

    setIsProcessing(true); setStatus('PROCESSING'); setError(null); setIsSuccess(false); setProgress(0); setBatchResults(null)
    
    const timer = setInterval(() => {
        setProgress(p => (p < 98 ? p + Math.random() * 5 : p))
    }, 200)

    const fd = new FormData()
    
    try {
      if (mode === 'scan') {
        files.forEach(f => fd.append('images', f))
        const res = await stegoApi.batchAnalyze(fd)
        clearInterval(timer); setProgress(100)
        setBatchResults(res.data.data.results)
        setIsSuccess(true)
        setStatus('SECURE')
      } else {
        fd.append('mode', mode)
        fd.append('method', method)
        if (mode === 'hide') { 
            fd.append('password', password)
            files.forEach(f => fd.append('covers', f))
            fd.append('secret', secret!) 
        } else { 
            // The backend expects 'batch_keys' for bulk extraction
            fd.append('batch_keys', password)
            files.forEach(f => fd.append('stegos', f)) 
        }
        
        const res = await stegoApi.batch(fd)
        clearInterval(timer); setProgress(100)
        const url = window.URL.createObjectURL(new Blob([res.data]))
        const link = document.createElement('a'); link.href = url
        link.setAttribute('download', `deepsteg_batch_${mode}.zip`)
        document.body.appendChild(link); link.click(); link.remove()
        window.URL.revokeObjectURL(url)
        setTimeout(() => { setIsSuccess(true); setStatus('SECURE') }, 500)
      }
    } catch (e: any) {
      clearInterval(timer)
      setError(e?.response?.data?.error || e?.message || 'Batch operation aborted.')
      setStatus('READY')
    } finally { setIsProcessing(false) }
  }

  return (
    <div className={`h-full flex flex-col gap-2 max-w-7xl mx-auto overflow-hidden ${window.innerWidth > 768 ? 'cursor-none' : 'cursor-auto'}`}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-black tracking-tighter uppercase text-[var(--fg)] glow-text leading-none">Batch Process</h2>
          <p className="text-[var(--fg-dim)]/80 text-xs font-bold tracking-wide mt-1">Process multiple files at once</p>
        </div>
        <div className="flex bg-[var(--bg-sidebar)] p-1.5 rounded-2xl border border-[var(--border)] gap-1">
          {(['hide', 'extract', 'scan'] as const).map(m => (
            <button key={m} onClick={() => { setMode(m); setError(null); setIsSuccess(false); setBatchResults(null) }}
              className={`px-5 py-3 rounded-xl text-[10px] font-black tracking-[0.3em] uppercase transition-all ${mode === m ? 'bg-primary text-black shadow-[0_0_20px_var(--primary-glow)]' : 'text-[var(--fg-dim)]/30 hover:text-[var(--fg-dim)]/60'}`}
            >
              {m === 'hide' ? 'Embed' : m === 'extract' ? 'Extract' : 'Scan'}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 min-h-0 grid grid-cols-1 xl:grid-cols-3 gap-3">
        {/* Dropzone Area */}
        <div className="xl:col-span-2 flex flex-col gap-3 min-h-0">
          <div {...getRootProps()} className={`relative h-28 border border-dashed rounded-3xl flex flex-col items-center justify-center transition-all ${isDragActive ? 'border-primary bg-primary/10' : 'border-[var(--border)] bg-[var(--bg-sidebar)] hover:border-primary/40 group'}`}>
            <input {...getInputProps()} />
            <Layers className={`h-8 w-8 mb-2 transition-all ${isDragActive ? 'text-primary scale-110' : 'text-[var(--fg-dim)]/20 group-hover:text-[var(--fg-dim)]/40'}`} />
            <p className="text-base font-bold tracking-tight uppercase text-[var(--fg)] transition-colors">
              Upload Images
            </p>
            <p className="text-xs text-[var(--fg-dim)]/50 tracking-wide mt-2 font-bold">Up to 50 images at once</p>
          </div>

          <AnimatePresence>
            {files.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-[var(--bg-card)] border border-[var(--border)] rounded-3xl p-4 flex-1 min-h-0 flex flex-col gap-3">
                <div className="flex items-center justify-between shrink-0">
                  <div className="flex items-center gap-2"><Zap className="h-4 w-4 text-primary" /><span className="text-[10px] font-bold tracking-wide text-[var(--fg)] uppercase">Files Ready ({files.length})</span></div>
                  <button onClick={() => { setFiles([]); setBatchResults(null); setIsSuccess(false); setStatus('READY'); }} className="text-[9px] text-red-500/40 hover:text-red-500 font-bold uppercase tracking-wide transition-colors">Remove All</button>
                </div>
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 overflow-y-auto flex-1 pr-2">
                  {files.map((file, i) => (
                    <div key={i} className="flex items-center gap-3 bg-[var(--fg)]/[0.02] rounded-xl p-3 border border-[var(--border)] group">
                      <FileText className="h-4 w-4 text-[var(--fg-dim)]/20 shrink-0 group-hover:text-primary transition-colors" />
                      <span className="text-[10px] font-black italic text-[var(--fg-dim)]/50 truncate uppercase tracking-tighter">{file.name}</span>
                      <button onClick={() => setFiles(p => p.filter((_, j) => j !== i))} className="ml-auto text-[var(--fg-dim)]/20 hover:text-red-500 hover:bg-red-500/10 p-0.5 rounded-full transition-all">
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Configuration */}
        <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-3xl p-4 flex flex-col gap-3 min-h-0">
          {mode === 'hide' && (
            <div className="space-y-4">
              <div className="space-y-2 px-2">
                <label className="text-[9px] font-bold tracking-wide text-[var(--fg-dim)]/40 uppercase">Encoding Method</label>
                <div className="grid grid-cols-2 gap-2">
                  {(['lsb', 'adaptive'] as const).map(m => (
                    <button key={m} onClick={() => setMethod(m)}
                      className={`py-2.5 rounded-xl text-[9px] font-black tracking-widest uppercase transition-all border ${method === m ? 'bg-primary/20 border-primary/40 text-primary shadow-[0_0_15px_var(--primary-glow)]' : 'bg-[var(--bg-sidebar)] border-[var(--border)] text-[var(--fg-dim)] hover:text-[var(--fg)]'}`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[9px] font-bold tracking-wide text-[var(--fg)] uppercase px-2">Secret File</label>
                <div {...getSecretProps()} className="relative h-24 border border-dashed rounded-2xl flex items-center justify-center border-[var(--border)] bg-[var(--bg-sidebar)] hover:border-accent/40 transition-all cursor-pointer">
                  <input {...getSecretInputProps()} />
                  {secret ? (
                    <div className="text-center group w-full h-full flex flex-col items-center justify-center relative">
                      <button 
                        onClick={(e) => { e.stopPropagation(); setSecret(null); }}
                        className="absolute top-2 right-2 p-1 rounded-full bg-red-500/20 border border-red-500/40 text-red-500 hover:text-white hover:bg-red-500 transition-all z-10"
                      >
                        <X className="h-3 w-3" />
                      </button>
                      <CheckCircle className="h-6 w-6 text-accent mx-auto mb-2" />
                      <p className="text-[10px] font-black text-[var(--fg)] italic truncate max-w-[150px] px-2 uppercase tracking-tighter">{secret.name}</p>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3 opacity-30 text-[var(--fg)]"><Upload className="h-5 w-5" /><p className="text-[10px] font-bold uppercase tracking-wide">Upload File</p></div>
                  )}
                </div>
              </div>
            </div>
          )}

          {mode !== 'scan' && (
            <div className="space-y-3">
                <label className="text-[9px] font-bold tracking-wide text-[var(--fg)] uppercase px-2">Password</label>
                {mode === 'hide' ? (
                <div className="relative group">
                    <Key className="absolute left-5 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--fg-dim)]/30 group-focus-within:text-primary transition-colors" />
                    <input type="password" placeholder="Encryption password"
                    className="w-full bg-[var(--bg-sidebar)] border border-[var(--border)] rounded-2xl py-3 pl-14 pr-6 text-sm font-medium tracking-normal focus:outline-none focus:border-primary/40 transition-all font-mono text-[var(--fg)] placeholder:text-[var(--fg-dim)]/20"
                    value={password} onChange={e => setPassword(e.target.value)}
                    />
                </div>
                ) : (
                <textarea placeholder={'Key 1\nKey 2\nKey 3...'}
                    className="w-full bg-[var(--bg-sidebar)] border border-[var(--border)] rounded-2xl py-3 px-5 text-sm font-medium focus:outline-none focus:border-primary/40 transition-all font-mono text-[var(--fg)] placeholder:text-[var(--fg-dim)]/20 resize-none h-20 tracking-normal"
                    value={password} onChange={e => setPassword(e.target.value)}
                />
                )}
            </div>
          )}

          <div className="flex-1 flex flex-col items-center justify-center py-4 text-center min-h-0">
            <AnimatePresence mode="wait">
                {isProcessing ? (
                    <div className="space-y-4">
                        <PowerBar progress={progress} active={true} />
                        <p className="text-[10px] font-bold text-primary animate-pulse tracking-wide">Processing files...</p>
                    </div>
                 ) : batchResults ? (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="w-full h-full flex flex-col gap-3 min-h-0">
                        <div className="flex items-center justify-between px-2 shrink-0">
                            <span className="text-[10px] font-bold uppercase text-primary/60 tracking-wide">Scan Results</span>
                            <CheckCircle className="h-4 w-4 text-primary" />
                        </div>
                        <div className="flex-1 overflow-y-auto rounded-2xl bg-[var(--bg-sidebar)] border border-[var(--border)] p-2 space-y-1">
                            {batchResults.map((r, i) => (
                                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-[var(--fg)]/[0.03] border border-[var(--border)] group hover:bg-[var(--fg)]/5 transition-colors">
                                    <div className="flex flex-col items-start truncate pr-4">
                                        <span className="text-[10px] font-black italic text-[var(--fg)] truncate w-full uppercase">{r.filename}</span>
                                        <span className="text-[8px] text-[var(--fg-dim)]/30 uppercase font-bold tracking-tighter">{r.heuristic}</span>
                                    </div>
                                    <div className={`px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-tighter ${r.verdict === 'CLEAN' ? 'text-green-500 bg-green-500/10 border border-green-500/20' : 'text-red-500 bg-red-500/10 border border-red-500/20 shadow-[0_0_10px_rgba(239,68,68,0.1)]'}`}>
                                        {r.verdict}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                 ) : isSuccess ? (
                    <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="flex items-center gap-3 text-primary bg-primary/10 border border-primary/20 rounded-2xl p-5">
                        <CheckCircle className="h-6 w-6" />
                        <span className="text-[10px] font-bold uppercase tracking-wide">Batch Complete — File Downloaded</span>
                    </motion.div>
                 ) : error ? (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-start gap-3 text-red-500 bg-red-500/10 border border-red-500/20 rounded-2xl p-5 text-left">
                        <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
                        <p className="text-[10px] font-bold uppercase tracking-wide leading-relaxed">Error: {error}</p>
                    </motion.div>
                 ) : (
                    <div className="opacity-10"><Layers className="h-10 w-10 mx-auto" /></div>
                 )}
            </AnimatePresence>
          </div>

          <button 
            disabled={files.length === 0 || (mode === 'hide' && !secret) || isProcessing} 
            onClick={handleBatch}
            style={{ color: '#000000' }}
            className="w-full bg-primary disabled:bg-primary/20 font-black tracking-[0.2em] text-[13px] uppercase rounded-2xl py-3 shadow-[0_0_30px_var(--primary-glow)] hover:opacity-90 transition-all active:scale-[0.98] lg:cursor-none"
          >
            {isProcessing ? 'Processing...' : 'Start Processing'}
          </button>
        </div>
      </div>
    </div>
  )
}
