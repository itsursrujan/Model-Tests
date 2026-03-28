import { useState, useCallback, Suspense, useEffect, memo, Component } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { Canvas } from '@react-three/fiber'
import { Scanner3D } from './three/Scanner3D'
import { Search, Activity, BarChart, X, FileText, ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react'
import { analyzeImage } from "./services/api"
import { useStore } from './store/useStore'

// Error Boundary to prevent Canvas crashes from blanking the whole page
class CanvasErrorBoundary extends Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: any) {
    super(props)
    this.state = { hasError: false }
  }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex items-center justify-center h-full text-white/40 text-xs font-bold uppercase tracking-widest bg-black/20 rounded-3xl">
          3D Renderer unavailable
        </div>
      )
    }
    return this.props.children
  }
}

// ───────────────────────── Helpers ─────────────────────────

/** Safely format a score to 0–100%. NEVER returns NaN or undefined. */
function safeScoreDisplay(score: any): string {
  if (score === null || score === undefined) return '50.00'
  const num = Number(score)
  if (isNaN(num) || !isFinite(num)) return '50.00'
  return (Math.max(0, Math.min(1, num)) * 100).toFixed(2)
}

/** Get verdict color class */
function getVerdictStyle(verdict: string) {
  switch (verdict) {
    case 'Clean':
      return 'bg-[#00FF9C]/10 border-[#00FF9C]/30 text-[#00FF9C] shadow-[0_0_20px_rgba(0,255,156,0.1)]'
    case 'STEGO':
    case 'Suspicious':
      return 'bg-red-500/10 border-red-500/30 text-red-500 shadow-[0_0_20px_rgba(255,59,59,0.2)]'
    case 'Moderate Risk':
      return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400 shadow-[0_0_20px_rgba(255,200,0,0.1)]'
    default:
      return 'bg-white/10 border-white/30 text-white/70'
  }
}

function isCleanVerdict(verdict: string) {
  return verdict === 'Clean'
}

// ───────────────────────── Power Bar ─────────────────────────
function PowerBar({ progress, active }: { progress: number; active: boolean }) {
  const displayPct = Math.round(progress)
  const flickerPct = active
    ? Math.max(0, Math.min(99, displayPct + Math.floor(Math.random() * 4 - 1)))
    : displayPct

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="flex gap-1.5 h-14 items-end">
        {[...Array(12)].map((_, i) => {
          const threshold = (i / 11) * 100
          const isActive = active && progress >= threshold
          return (
            <motion.div
              key={i}
              className={`w-1.5 rounded-sm ${isActive ? 'bg-primary' : 'bg-white/10'}`}
              animate={{
                height: isActive ? '100%' : '18%',
                boxShadow: isActive ? '0 0 10px var(--primary-glow)' : 'none',
                opacity: isActive ? [0.75, 1, 0.8] : 0.2,
              }}
              transition={isActive ? { repeat: Infinity, duration: 0.3, ease: 'easeInOut' } : { duration: 0.3 }}
            />
          )
        })}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="font-mono text-xl font-black text-primary" style={{ textShadow: '0 0 12px var(--primary-glow)' }}>
          {active ? flickerPct : '—'}
        </span>
        {active && <span className="font-mono text-xs font-bold text-primary/60">%</span>}
        <span className="font-mono text-[9px] font-black text-white/40 tracking-widest ml-1">
          {active ? 'SCANNING' : 'STANDBY'}
        </span>
      </div>
    </div>
  )
}

export const Analyze = memo(function Analyze() {
  // --- States ---
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  
  // Internal animation state for progress bar
  const [progress, setProgress] = useState(0);
  const [showRing, setShowRing] = useState(false);
  const setStatus = useStore((state: any) => state.setStatus);

  // --- Handlers ---
  const isImageFile = (file: File) => file.type.startsWith('image/');

  const handleFileChange = (file: File) => {
    setSelectedFile(file);
    // Only generate preview for images
    if (isImageFile(file)) {
      setPreview(URL.createObjectURL(file));
    } else {
      setPreview(file.name); // Store filename as placeholder for non-images
    }
    setResult(null);
    setProgress(0);
    setShowRing(false);
    setStatus('READY');
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles?.[0]) handleFileChange(acceptedFiles[0]);
  }, []);

  const { getRootProps, getInputProps } = useDropzone({ 
    onDrop, 
    accept: {
      'image/*': [],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    multiple: false 
  });

  const handleClear = () => {
    setSelectedFile(null);
    setPreview(null);
    setResult(null);
    setLoading(false);
    setProgress(0);
    setShowRing(false);
    setStatus('READY');
  };

  // Determine if the current file is an image (for preview rendering)
  const isCurrentImage = selectedFile ? isImageFile(selectedFile) : false;

  const handleScan = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setStatus('ANALYZING');
    setProgress(0);
    setShowRing(false);

    // Simulated progress build-up for visual effect
    const timer = setInterval(() => {
        setProgress(p => {
          if (p < 90) return p + (2.0 + Math.random() * 2);
          return p;
        });
    }, 100);

    try {
        const res = await analyzeImage(selectedFile);
        clearInterval(timer);
        setProgress(100);
        
        // Artificial delay for result animation
        setTimeout(() => {
          setResult(res);
          const isCompromised = !isCleanVerdict(res.verdict);
          setStatus(isCompromised ? 'COMPROMISED' : 'SECURE');
          setLoading(false);
          setShowRing(true);
          setTimeout(() => setShowRing(false), 2000);
        }, 500);
    } catch (err) {
        console.error(err);
        clearInterval(timer);
        setLoading(false);
        setStatus('READY');
    }
  };

  return (
    <div className="flex flex-col gap-8 w-full mx-auto cursor-none">
        {/* Header Row */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between w-full">
            <div>
              <h2 className="text-xl sm:text-2xl font-black tracking-tighter uppercase text-white glow-text leading-none">AI Forensics</h2>
              <p className="text-xs font-bold tracking-wide mt-1 text-white/40">Steganography analyzer — Images, PDF, DOCX, TXT</p>
            </div>
            {preview && (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={handleClear}
                className="mt-4 sm:mt-0 px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-[9px] sm:text-[10px] font-black tracking-widest uppercase text-red-400 hover:bg-red-500/20 transition-all flex items-center justify-center gap-2"
              >
                <X className="h-3 w-3" /> Clear File
              </motion.button>
            )}
        </div>

      <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-5 gap-8 mt-4">
        {/* LEFT PANEL: PREVIEW CONTAINER */}
        <div className="md:col-span-3 flex flex-col gap-6 min-h-0 order-2 md:order-1">
          {!preview && (
            <div {...getRootProps()} className="lg:cursor-none">
              <input {...getInputProps()} accept="image/*,.pdf,.docx,.txt" />
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white/5 border border-dashed border-white/10 rounded-3xl p-12 flex flex-col items-center justify-center transition-all hover:bg-white/10 group min-h-[280px]"
              >
                <Search className="h-10 w-10 mb-4 text-white/40 group-hover:scale-110 transition-transform" />
                <p className="text-sm font-bold tracking-wide uppercase text-white/40 group-hover:text-white transition-colors">Upload File to Scan</p>
                <p className="text-[10px] font-bold tracking-widest uppercase text-white/20 mt-2">Image · PDF · DOCX · TXT</p>
              </motion.div>
            </div>
          )}

          {/* Non-image file placeholder */}
          {preview && !isCurrentImage && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white/5 border border-white/10 rounded-3xl p-12 flex flex-col items-center justify-center min-h-[320px]"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-4">
                <FileText className="h-8 w-8 text-primary" />
              </div>
              <p className="text-sm font-black tracking-wide uppercase text-white/70">{selectedFile?.name}</p>
              <p className="text-[10px] font-bold text-white/30 mt-1 uppercase tracking-widest">
                {selectedFile?.name.split('.').pop()?.toUpperCase()} Document Ready
              </p>
            </motion.div>
          )}

          {preview && isCurrentImage && (
            <div className={`bg-white/5 border border-white/10 rounded-3xl overflow-hidden min-h-[320px] md:min-h-0 flex-1 relative transition-all duration-700 ${
              result 
                ? (!isCleanVerdict(result.verdict) 
                    ? 'shadow-[inset_0_0_60px_rgba(255,59,59,0.3)] border-red-500/50' 
                    : 'shadow-[inset_0_0_60px_rgba(0,255,156,0.3)] border-primary/50')
                : ''
            }`}>
              <CanvasErrorBoundary fallback={
                <div className="flex items-center justify-center h-full p-4">
                  <img src={preview} className="max-h-64 mx-auto rounded-lg shadow-2xl" />
                </div>
              }>
                <Suspense fallback={null}>
                  <Canvas camera={{ position: [0, 0, 15] }}>
                    <ambientLight intensity={0.5} />
                    <pointLight position={[10, 10, 10]} intensity={1} color="#00f2ff" />
                    <Scanner3D image={preview} scanning={loading} />
                  </Canvas>
                </Suspense>
              </CanvasErrorBoundary>

              {/* Glowing feedback ring */}
              <AnimatePresence>
                {showRing && result && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 1.02 }}
                    className={`absolute inset-0 z-[50] pointer-events-none rounded-3xl border-[3px] transition-colors duration-700 ${
                      !isCleanVerdict(result.verdict) ? 'border-red-500' : 'border-primary'
                    }`}
                    style={{
                      boxShadow: !isCleanVerdict(result.verdict)
                        ? 'inset 0 0 80px rgba(255,59,59,0.5), 0 0 40px rgba(255,59,59,0.3)' 
                        : 'inset 0 0 80px rgba(0,242,255,0.5), 0 0 40px rgba(0,242,255,0.3)'
                    }}
                  />
                )}
              </AnimatePresence>

              {loading && (
                  <div className="absolute top-8 left-8 z-[60]">
                      <PowerBar progress={progress} active={true} />
                  </div>
              )}
            </div>
          )}

          {/* SCAN BUTTON — only fires API on explicit click */}
          {preview && !result && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex justify-start relative z-[100] mt-6"
            >
                <button
                    id="scan-file-btn"
                    onClick={handleScan}
                    disabled={!selectedFile || loading}
                    style={{ backgroundColor: '#00f2ff', color: '#000000' }}
                    className="w-full sm:w-auto px-12 py-5 rounded-2xl font-black tracking-widest text-[11px] uppercase shadow-[0_0_40px_rgba(0,242,255,0.4)] transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed hover:brightness-110"
                >
                    {loading ? "Scanning..." : isCurrentImage ? "Scan Image" : "Scan Document"}
                </button>
            </motion.div>
          )}
        </div>

        {/* RIGHT PANEL: RESULTS DISPLAY */}
        <div className="md:col-span-2 flex flex-col justify-center gap-6 min-h-0 order-1 md:order-2">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                 className="bg-white/5 border border-white/10 rounded-3xl p-8 space-y-6"
              >
                {/* Verdict Badge */}
                <div>
                  <h4 className="text-[9px] font-bold tracking-wide uppercase mb-4 text-white/30">Analysis Result</h4>
                  <div className={`px-6 py-4 rounded-2xl border text-sm font-black tracking-widest uppercase text-center transition-all duration-500 ${getVerdictStyle(result.verdict)}`}>
                      {result.verdict || 'Unknown'}
                  </div>
                </div>

                <div className="h-px bg-white/10" />

                {/* Image-specific results */}
                {result.type === 'image' && (
                  <div className="space-y-4">
                    {/* AI Score */}
                    <div className="flex justify-between items-center bg-white/2 p-4 rounded-2xl border border-white/5">
                      <span className="text-[10px] font-bold uppercase text-white/40">AI Score</span>
                      <span className={`text-sm font-mono font-black ${
                        result.verdict === 'Clean' ? 'text-[#00FF9C]' : 
                        result.verdict === 'Moderate Risk' ? 'text-yellow-400' : 
                        'text-red-500'
                      }`}>
                        {safeScoreDisplay(result.ai_score)}%
                      </span>
                    </div>

                    {/* Signature Status */}
                    <div className="flex justify-between items-center bg-white/2 p-4 rounded-2xl border border-white/5">
                      <span className="text-[10px] font-bold uppercase text-white/40">Signature</span>
                      <span className={`text-xs font-mono font-black flex items-center gap-1.5 ${result.signature_detected ? 'text-red-500' : 'text-primary'}`}>
                        {result.signature_detected ? (
                          <><ShieldAlert className="h-3.5 w-3.5" /> DETECTED</>
                        ) : (
                          <><ShieldCheck className="h-3.5 w-3.5" /> NONE</>
                        )}
                      </span>
                    </div>
                  </div>
                )}

                {/* Document-specific results */}
                {result.type === 'document' && (
                  <div className="space-y-4">
                    {/* AI Score (Confidence for documents) */}
                    <div className="flex justify-between items-center bg-white/2 p-4 rounded-2xl border border-white/5">
                      <span className="text-[10px] font-bold uppercase text-white/40">AI Score</span>
                      <span className={`text-sm font-mono font-black ${!isCleanVerdict(result.verdict) ? 'text-red-500' : 'text-primary'}`}>
                        {safeScoreDisplay(result.confidence)}%
                      </span>
                    </div>

                    {/* Indicators */}
                    {result.indicators && result.indicators.length > 0 && (
                      <div className="bg-white/2 p-4 rounded-2xl border border-white/5">
                        <p className="text-[9px] font-bold text-white/20 uppercase mb-2 tracking-wide flex items-center gap-1.5">
                          <AlertTriangle className="h-3 w-3 text-yellow-400" /> Forensic Findings
                        </p>
                        <ul className="space-y-1">
                          {result.indicators.map((ind: string, idx: number) => (
                            <li key={idx} className="text-[11px] font-medium text-white/50 leading-relaxed">• {ind}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* File Context */}
                    <div className="flex justify-between items-center bg-white/2 p-4 rounded-2xl border border-white/5 px-4 py-2">
                       <span className="text-[10px] font-bold uppercase text-white/40">Context</span>
                       <span className="text-[10px] font-bold text-white/60 uppercase">{result.file_type || 'DOC'} ({result.confidence_level || 'low'} confidence)</span>
                    </div>
                  </div>
                )}

                {/* Analysis Log */}
                <div className="p-4 rounded-2xl bg-white/2 border border-white/5">
                  <p className="text-[9px] font-bold text-white/20 uppercase mb-2 tracking-wide">Analysis Log</p>
                  <p className="text-xs font-medium leading-relaxed text-white/60">
                    {result.details || result.reason || "Forensic sweep complete. Analysis executed successfully."}
                  </p>
                </div>
              </motion.div>
            ) : (
                <div className="space-y-6">
                  <div className="bg-white/5 border border-white/10 rounded-3xl p-6">
                    <h4 className="text-[10px] font-bold tracking-wide text-white/20 uppercase mb-6 flex items-center gap-2 border-b border-white/5 pb-4">
                      <Activity className="h-4 w-4 text-primary" /> System Status
                    </h4>
                    <div className="space-y-4">
                      {[
                        { label: 'AI CORE', val: 'V4.2_ONLINE', color: 'text-primary' },
                        { label: 'CALIBRATION', val: 'OPTIMAL', color: 'text-[#00FF9C]' },
                        { label: 'THREAT DB', val: 'SYNCED', color: 'text-primary' },
                      ].map((item, idx) => (
                        <div key={idx} className="flex justify-between items-center text-[10px] pb-4 border-b border-white/5 last:border-0 last:pb-0">
                           <span className="font-bold uppercase tracking-widest text-white/40">{item.label}</span>
                          <span className={`${item.color} font-mono font-black`}>{item.val}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white/5 border border-white/10 rounded-3xl p-6">
                    <h4 className="text-[10px] font-bold tracking-wide text-white/20 uppercase mb-6 flex items-center gap-2 border-b border-white/5 pb-4">
                      <BarChart className="h-4 w-4 text-primary" /> Monitoring
                    </h4>
                    <p className="text-xs text-white/20 font-bold leading-relaxed tracking-wide">
                        Neural network analyzer ready for ingestion. Upload a sample to initiate pixel-level forensics.
                    </p>
                  </div>
                </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
})
