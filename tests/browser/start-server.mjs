import { spawn } from 'node:child_process';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import process from 'node:process';

const TAU_BIN = '/workspace/tau/.venv/bin/tau';
const HOST = '127.0.0.1';
const PORT = '8765';

const SHUTDOWN_GRACE_MS = 3000;

const tempRoot = await mkdtemp(join(tmpdir(), 'tau-playwright-'));
const workspaceDir = join(tempRoot, 'workspace');
const databasePath = join(tempRoot, 'tau.sqlite3');

const fixtureFiles = [
  {
    relativePath: 'README.md',
    content: '# Tau Browser Fixture\\n\\nSafe UTF-8 fixture workspace for Playwright harness.\\n',
  },
  {
    relativePath: 'notes/welcome.txt',
    content: 'Hello from Tau browser tests. UTF-8 sample: café, naïve, São Tomé, 日本語.\\n',
  },
  {
    relativePath: 'docs/checklist.md',
    content: '- [ ] Open Tau web UI\\n- [ ] Validate page render\\n- [ ] Run smoke flows\\n',
  },
];

let cleanedUp = false;
let shuttingDown = false;
let requestedShutdown = false;
let exiting = false;
let shutdownTimer;
let fatalSeen = false;

async function seedWorkspace() {
  await mkdir(workspaceDir, { recursive: true });

  for (const fixture of fixtureFiles) {
    const targetPath = join(workspaceDir, fixture.relativePath);
    await mkdir(dirname(targetPath), { recursive: true });
    await writeFile(targetPath, fixture.content, 'utf8');
  }
}

async function cleanup() {
  if (cleanedUp) {
    return;
  }

  cleanedUp = true;
  await rm(tempRoot, { recursive: true, force: true });
}

function setupEnv() {
  const env = { ...process.env };
  delete env.TAU_WEB_AUTH_TOKEN;

  const pythonPathPrefix = '/workspace/tau/src';
  env.PYTHONPATH = env.PYTHONPATH
    ? `${pythonPathPrefix}:${env.PYTHONPATH}`
    : pythonPathPrefix;

  const pathPrefix = '/workspace/tau/.venv/bin';
  const inheritedPath = env.PATH ?? env.Path;
  env.PATH = inheritedPath ? `${pathPrefix}:${inheritedPath}` : pathPrefix;

  return env;
}

function childIsRunning() {
  return child.exitCode === null && child.signalCode === null;
}

function signalChild(signal) {
  if (!childIsRunning()) {
    return true;
  }

  const { pid } = child;
  if (typeof pid !== 'number') {
    return false;
  }

  try {
    process.kill(pid, signal);
    return true;
  } catch (error) {
    if (error && error.code !== 'ESRCH') {
      console.warn(`[start-server] failed to signal pid ${pid}:`, error);
    }

    return false;
  }
}

async function exitWrapper(code) {
  if (exiting) {
    return;
  }

  exiting = true;

  if (shutdownTimer) {
    clearTimeout(shutdownTimer);
  }

  try {
    await cleanup();
  } catch (error) {
    console.error('[start-server] cleanup error:', error);
  }

  process.exit(code);
}

function beginShutdown(signal = 'SIGTERM', requested = false) {
  if (requested) {
    requestedShutdown = true;
  }

  if (shuttingDown) {
    return;
  }

  shuttingDown = true;
  signalChild(signal);

  shutdownTimer = setTimeout(() => {
    if (childIsRunning()) {
      signalChild('SIGKILL');
    }

    void exitWrapper(requestedShutdown ? 0 : 1);
  }, SHUTDOWN_GRACE_MS);
  shutdownTimer.unref();
}

function fatal(error) {
  if (fatalSeen) {
    return;
  }

  fatalSeen = true;
  console.error('[start-server] fatal error:', error);
  beginShutdown('SIGTERM', false);

  if (!childIsRunning()) {
    void exitWrapper(1);
  }
}

await seedWorkspace();

const child = spawn(
  TAU_BIN,
  [
    'web',
    '--host',
    HOST,
    '--port',
    PORT,
    '--cwd',
    workspaceDir,
    '--database',
    databasePath,
  ],
  {
    stdio: 'ignore',
    env: setupEnv(),
    shell: false,
    detached: false,
  },
);

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    beginShutdown(signal, true);
  });
}

process.on('uncaughtException', (error) => {
  fatal(error);
});

process.on('unhandledRejection', (reason) => {
  fatal(reason);
});

child.on('error', (error) => {
  console.error('[start-server] child process error:', error);
  void exitWrapper(1);
});

child.on('exit', async (code, signal) => {
  if (requestedShutdown) {
    await exitWrapper(0);
    return;
  }

  if (signal) {
    await exitWrapper(1);
    return;
  }

  await exitWrapper(code ?? 1);
});
