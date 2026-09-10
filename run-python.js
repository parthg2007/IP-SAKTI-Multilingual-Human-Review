import { spawn } from 'node:child_process'
import { backendDir, findPython } from './python-runtime.js'

const child = spawn(findPython(), process.argv.slice(2), { cwd: backendDir, stdio: 'inherit' })
child.on('error', (error) => { console.error(error.message); process.exitCode = 1 })
child.on('exit', (code) => { process.exitCode = code ?? 1 })
