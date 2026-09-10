import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'

// A field of connected points, with a soft spotlight and cursor repulsion.
export default function InteractiveBackground() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const context = canvas.getContext('2d')
    if (!context) return

    const media = gsap.matchMedia()
    media.add({ moving: '(prefers-reduced-motion: no-preference)', still: '(prefers-reduced-motion: reduce)' }, ({ conditions }) => {
      let width = 0
      let height = 0
      let points = []
      let color = '76, 107, 72'
      let gold = '156, 116, 45'
      let animationTime = 0
      const pointer = { x: 0, y: 0, active: false }
      const glow = { x: 0, y: 0, trailX: 0, trailY: 0, opacity: 0 }
      const finePointer = window.matchMedia('(pointer: fine)')
      const interactionRadius = 240

      const drawGlow = (x, y, radius, rgb, opacity) => {
        const gradient = context.createRadialGradient(x, y, 0, x, y, radius)
        gradient.addColorStop(0, `rgba(${rgb}, ${opacity})`)
        gradient.addColorStop(0.4, `rgba(${rgb}, ${opacity * 0.45})`)
        gradient.addColorStop(1, `rgba(${rgb}, 0)`)
        context.fillStyle = gradient
        context.fillRect(x - radius, y - radius, radius * 2, radius * 2)
      }

      const draw = (time = animationTime, step = 0) => {
        context.clearRect(0, 0, width, height)
        const following = 1 - Math.pow(0.82, step)
        const trailing = 1 - Math.pow(0.94, step)
        const interacting = pointer.active && conditions.moving
        glow.x += (pointer.x - glow.x) * following
        glow.y += (pointer.y - glow.y) * following
        glow.trailX += (glow.x - glow.trailX) * trailing
        glow.trailY += (glow.y - glow.trailY) * trailing
        glow.opacity += ((interacting ? 1 : 0) - glow.opacity) * following

        if (glow.opacity > 0.005) {
          drawGlow(glow.x, glow.y, 280, color, 0.18 * glow.opacity)
          drawGlow(glow.trailX, glow.trailY, 150, gold, 0.12 * glow.opacity)
        }

        const positions = points.map((point) => {
          const x = point.x + Math.sin(time * 0.16 + point.phase) * 13
          const y = point.y + Math.cos(time * 0.12 + point.phase) * 13
          const dx = x - pointer.x
          const dy = y - pointer.y
          const distance = Math.hypot(dx, dy)
          const influence = interacting ? Math.max(0, 1 - distance / interactionRadius) : 0
          const push = influence * influence * 105
          const targetX = distance > 0 ? dx / distance * push : 0
          const targetY = distance > 0 ? dy / distance * push : 0
          // Ease back into place instead of snapping when the cursor moves away.
          point.offsetX += (targetX - point.offsetX) * following
          point.offsetY += (targetY - point.offsetY) * following
          return { x: x + point.offsetX, y: y + point.offsetY, influence }
        })

        positions.forEach((point, index) => {
          context.beginPath()
          context.arc(point.x, point.y, 1.5 + point.influence * 2, 0, Math.PI * 2)
          context.fillStyle = `rgba(${point.influence > 0.45 ? gold : color}, ${0.42 + point.influence * 0.5})`
          context.fill()
          for (let next = index + 1; next < positions.length; next++) {
            const other = positions[next]
            const distance = Math.hypot(point.x - other.x, point.y - other.y)
            if (distance < 165) {
              context.beginPath()
              context.moveTo(point.x, point.y)
              context.lineTo(other.x, other.y)
              context.strokeStyle = `rgba(${color}, ${(1 - distance / 165) * (0.2 + point.influence * 0.3)})`
              context.stroke()
            }
          }
        })

        // Limit cursor connections so the background stays clear around text.
        if (interacting) {
          positions
            .map((point) => ({ ...point, distance: Math.hypot(point.x - glow.x, point.y - glow.y) }))
            .filter((point) => point.distance < interactionRadius)
            .sort((a, b) => a.distance - b.distance)
            .slice(0, 7)
            .forEach((point) => {
            context.beginPath()
            context.moveTo(point.x, point.y)
            context.lineTo(glow.x, glow.y)
            context.strokeStyle = `rgba(${color}, ${(1 - point.distance / interactionRadius) * 0.5 * glow.opacity})`
            context.stroke()
            })
        }
      }

      const resize = () => {
        width = canvas.clientWidth
        height = canvas.clientHeight
        const ratio = Math.min(window.devicePixelRatio || 1, 1.5)
        canvas.width = width * ratio
        canvas.height = height * ratio
        context.setTransform(ratio, 0, 0, ratio, 0, 0)
        const count = width < 600 ? 24 : Math.min(112, Math.max(72, Math.round(width * height / 14000)))
        points = Array.from({ length: count }, (_, index) => ({
          x: ((index * 0.6180339) % 1) * width,
          y: ((index * 0.4142136) % 1) * height,
          phase: index * 1.7,
          offsetX: 0,
          offsetY: 0,
        }))
        draw()
      }
      const themeRoot = canvas.closest('.scheme-dark, .scheme-light')
      const updateColor = () => {
        color = themeRoot?.classList.contains('dark') ? '167, 192, 145' : '76, 107, 72'
        gold = themeRoot?.classList.contains('dark') ? '215, 185, 119' : '156, 116, 45'
        draw()
      }
      const onPointerMove = (event) => {
        if (!finePointer.matches || event.pointerType === 'touch') return
        if (!pointer.active) {
          glow.x = glow.trailX = event.clientX
          glow.y = glow.trailY = event.clientY
        }
        pointer.x = event.clientX
        pointer.y = event.clientY
        pointer.active = true
      }
      const resetPointer = () => { pointer.active = false }
      const tick = (time, deltaTime) => {
        animationTime = time
        draw(time, Math.min(deltaTime, 40) / (1000 / 60))
      }
      const onVisibility = () => {
        gsap.ticker.remove(tick)
        if (document.hidden) { resetPointer(); glow.opacity = 0 }
        if (conditions.moving && !document.hidden) gsap.ticker.add(tick)
      }

      const resizeObserver = new ResizeObserver(resize)
      const themeObserver = new MutationObserver(updateColor)
      resizeObserver.observe(canvas)
      if (themeRoot) themeObserver.observe(themeRoot, { attributes: true, attributeFilter: ['class'] })
      updateColor()
      resize()
      onVisibility()
      if (conditions.moving) window.addEventListener('pointermove', onPointerMove, { passive: true })
      document.addEventListener('pointerleave', resetPointer)
      window.addEventListener('blur', resetPointer)
      document.addEventListener('visibilitychange', onVisibility)
      return () => {
        gsap.ticker.remove(tick)
        resizeObserver.disconnect()
        themeObserver.disconnect()
        window.removeEventListener('pointermove', onPointerMove)
        document.removeEventListener('pointerleave', resetPointer)
        window.removeEventListener('blur', resetPointer)
        document.removeEventListener('visibilitychange', onVisibility)
      }
    })
    return () => media.revert()
  }, [])

  return <canvas ref={canvasRef} aria-hidden="true" className="pointer-events-none fixed inset-0 h-dvh w-full opacity-95" />
}
