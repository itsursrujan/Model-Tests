import { Header } from './components/Header'
import { CustomCursor } from './components/CustomCursor'
import { DigitalRain } from './components/DigitalRain'
import { Analyze } from './Analyze'

function App() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#e0e0e0] flex flex-col pt-14 selection:bg-cyan-500/30">
      <CustomCursor />
      <DigitalRain />
      
      {/* Noise overlay */}
      <div className="fixed inset-0 pointer-events-none z-[2] opacity-[0.03] mix-blend-overlay bg-[url('https://grainy-gradients.vercel.app/noise.svg')]" />
      
      <Header />
      
      <main className="flex-1 p-8 flex flex-col items-center relative z-[10] overflow-y-auto">
        <div className="w-full max-w-[1400px]">
          <Analyze />
        </div>
      </main>

      {/* Decorative Matrix lines */}
      <div className="fixed inset-0 pointer-events-none z-0 opacity-10 flex justify-between px-10">
        {[...Array(12)].map((_, i) => (
           <div key={i} className="w-[1px] h-full bg-gradient-to-b from-transparent via-primary/50 to-transparent" />
        ))}
      </div>
    </div>
  )
}

export default App
