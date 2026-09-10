import { useEffect, useState } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Chat from './pages/Chat.jsx'
import ThemeToggle from './components/ThemeToggle.jsx'
import Landing from './pages/Landing.jsx'
import { brandTheme } from './theme.js'

const App = () => {
  const [theme, setTheme] = useState("dark")

  useEffect(() => {
    try {
      localStorage.setItem('ip-sakti-theme', theme)
    } catch {
      // Theme switching still works when browser storage is unavailable.
    }
  }, [theme])

  return (
    <div className={`${brandTheme} ${theme === 'dark' ? 'dark scheme-dark' : 'scheme-light'} min-h-dvh bg-[var(--lp-bg)] text-[var(--lp-ink)]`}>
    <BrowserRouter>
      <ThemeToggle theme={theme} onToggle={() => setTheme((current) => current === 'dark' ? 'light' : 'dark')} />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/chat" element={<Chat />} />
      </Routes>
    </BrowserRouter>
    </div>
  )
}

export default App
