#!/usr/bin/env node
/**
 * SIH-Project: Unified Development Gateway
 * Concurrently starts the FastAPI backend and Vite React frontend
 * with unified colored console logging and coordinated shutdown.
 */

import { spawn, spawnSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { findPython } from './python-runtime.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const backendDir = path.join(__dirname, 'backend');
const frontendDir = path.join(__dirname, 'frontend');
const npmExec = process.platform === 'win32' ? 'npm.cmd' : 'npm';

function ensureFrontendDependencies() {
  const viteBin = path.join(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js');
  const viteCheck = fs.existsSync(viteBin) && spawnSync(process.execPath, [viteBin, '--version'], { cwd: frontendDir, stdio: 'ignore' }).status === 0;
  if (viteCheck) return;
  console.log(`${YELLOW}[FRONTEND] Installing frontend dependencies...${RESET}`);
  const npmCli = process.env.npm_execpath;
  const install = npmCli
    ? spawnSync(process.execPath, [npmCli, 'install', '--include=optional'], { cwd: frontendDir, stdio: 'inherit' })
    : spawnSync(npmExec, ['install', '--include=optional'], { cwd: frontendDir, stdio: 'inherit', shell: process.platform === 'win32' });

  if (install.status !== 0) {
    console.error(`${RED}[FRONTEND] Dependency installation failed.${RESET}`);
    process.exit(1);
  }
}


// Terminal ANSI Colors
const CYAN = '\x1b[36m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const RED = '\x1b[31m';
const BOLD = '\x1b[1m';
const RESET = '\x1b[0m';

console.log('\n' + '='.repeat(70));
console.log(`${BOLD}🌿 SIH-Project: Full-Stack Gateway${RESET}`);
console.log('='.repeat(70));
console.log(`${CYAN}> Backend:  http://127.0.0.1:8000 (API & Docs at /docs)${RESET}`);
console.log(`${GREEN}> Frontend: http://localhost:5173 (Web Application)${RESET}`);
console.log(`${YELLOW}> Press Ctrl+C at any time to stop all services.${RESET}\n`);

ensureFrontendDependencies();

// 1. Launch FastAPI Backend
const backendProc = spawn(findPython(), ['run.py'], {
  cwd: backendDir,
  env: { ...process.env, PYTHONUNBUFFERED: '1' },
  stdio: ['inherit', 'pipe', 'pipe']
});

// 2. Launch Vite Frontend
const frontendBin = path.join(frontendDir, 'node_modules', 'vite', 'bin', 'vite.js');
const frontendProc = spawn(process.execPath, [frontendBin], {
  cwd: frontendDir,
  env: { ...process.env },
  stdio: ['inherit', 'pipe', 'pipe']
});

function pipeOutput(stream, prefix, color) {
  let buffer = '';
  stream.on('data', (chunk) => {
    buffer += chunk.toString();
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (line.trim()) {
        console.log(`${color}${prefix}${RESET} ${line}`);
      }
    }
  });
  stream.on('end', () => {
    if (buffer.trim()) {
      console.log(`${color}${prefix}${RESET} ${buffer}`);
    }
  });
}

pipeOutput(backendProc.stdout, '[BACKEND] ', CYAN);
pipeOutput(backendProc.stderr, '[BACKEND] ', RED);
pipeOutput(frontendProc.stdout, '[FRONTEND]', GREEN);
pipeOutput(frontendProc.stderr, '[FRONTEND]', YELLOW);

let shuttingDown = false;
function shutdown() {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log(`\n${YELLOW}Shutting down all services...${RESET}`);
  backendProc.kill('SIGTERM');
  frontendProc.kill('SIGTERM');
  setTimeout(() => {
    try { backendProc.kill('SIGKILL'); } catch (e) {}
    try { frontendProc.kill('SIGKILL'); } catch (e) {}
    console.log(`${GREEN}All services stopped cleanly. Goodbye!${RESET}`);
    process.exit(0);
  }, 800);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

backendProc.on('exit', (code) => {
  if (!shuttingDown && code !== 0 && code !== null) {
    console.log(`${RED}Backend exited unexpectedly with code ${code}${RESET}`);
    shutdown();
  }
});

frontendProc.on('exit', (code) => {
  if (!shuttingDown && code !== 0 && code !== null) {
    console.log(`${RED}Frontend exited unexpectedly with code ${code}${RESET}`);
    shutdown();
  }
});

for (const child of [backendProc, frontendProc]) {
  child.on('error', (error) => { console.error(error.message); shutdown(); });
}
