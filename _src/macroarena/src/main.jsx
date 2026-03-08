import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import MacroArena from './MacroArena'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <MacroArena />
  </StrictMode>
)
