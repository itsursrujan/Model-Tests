import { useEffect, useRef } from 'react'
import { useStore } from '../store/useStore'

const HEX_CHARS = '0123456789ABCDEF01'
const FONT_SIZE = 13
const COLUMN_WIDTH = 18
const FPS = 30 

export function DigitalRain() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const theme = useStore((s: any) => s.theme)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d', { alpha: false })! 

    let columns: { y: number; speed: number; chars: string[] }[] = []
    let animId: number
    let lastTime = 0

    const init = () => {
      const W = window.innerWidth
      const H = window.innerHeight
      canvas.width = W
      canvas.height = H

      const colCount = Math.floor(W / COLUMN_WIDTH)
      columns = Array.from({ length: colCount }, () => ({
        y: Math.random() * -H,
        speed: 0.6 + Math.random() * 1.2,
        chars: Array.from({ length: 25 }, () => HEX_CHARS[Math.floor(Math.random() * HEX_CHARS.length)]),
      }))
    }

    const draw = (time: number) => {
      animId = requestAnimationFrame(draw)
      const delta = time - lastTime
      if (delta < 1000 / FPS) return
      lastTime = time

      const W = canvas.width
      const H = canvas.height
      const isDark = true // Default to dark for this test project
      
      ctx.fillStyle = '#0a0a0a'
      ctx.globalAlpha = 0.15
      ctx.fillRect(0, 0, W, H)
      ctx.globalAlpha = 1.0

      ctx.font = `${FONT_SIZE}px "JetBrains Mono", monospace`

      for (let i = 0; i < columns.length; i++) {
        const col = columns[i]
        const x = i * COLUMN_WIDTH + COLUMN_WIDTH / 2

        for (let j = 0; j < col.chars.length; j++) {
          const charY = col.y - j * FONT_SIZE
          if (charY < -FONT_SIZE || charY > H + FONT_SIZE) continue

          const isHead = j === 0
          let alpha = isHead ? 0.7 : Math.max(0, 0.12 - j * 0.005)
          if (alpha <= 0) continue

          ctx.fillStyle = isHead ? '#ffffff' : '#00f2ff'
          ctx.globalAlpha = alpha
          ctx.fillText(col.chars[j], x, charY)
        }
        col.y += col.speed * FONT_SIZE * 0.25
        if (col.y - col.chars.length * FONT_SIZE > H) col.y = -20
      }
    }

    init()
    animId = requestAnimationFrame(draw)
    window.addEventListener('resize', init)
    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', init)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none fixed inset-0 z-[1] will-change-transform"
      style={{ opacity: 0.12 }}
    />
  )
}
