#!/usr/bin/env node
// Zero-dependency local server for the wireframe-picker click-selection loop.
//
// Watches `content/` for HTML screens, serves the newest one to a normal
// (uncontrolled) browser tab, and records clicks sent back over a hand-rolled
// WebSocket connection to `state/events` as JSON lines. No npm dependencies:
// only Node built-ins, so `node pick-server.cjs` runs with nothing installed.

'use strict';

const crypto = require('crypto');
const fs = require('fs');
const http = require('http');
const path = require('path');

const WS_MAGIC = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';

function parseArgs(argv) {
  const args = {
    projectDir: null,
    open: false,
    port: 0,
    host: '127.0.0.1',
    urlHost: null,
    idleTimeoutMinutes: 240,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--project-dir') args.projectDir = argv[++i];
    else if (a === '--open') args.open = true;
    else if (a === '--port') args.port = Number(argv[++i]);
    else if (a === '--host') args.host = argv[++i];
    else if (a === '--url-host') args.urlHost = argv[++i];
    else if (a === '--idle-timeout-minutes') args.idleTimeoutMinutes = Number(argv[++i]);
  }
  return args;
}

function makeSessionDirs(projectDir) {
  const base = projectDir
    ? path.join(projectDir, '.squire', 'wireframe-picker')
    : path.join(require('os').tmpdir(), 'squire-wireframe-picker');
  const sessionId = `${process.pid}-${Date.now()}`;
  const sessionDir = path.join(base, sessionId);
  const screenDir = path.join(sessionDir, 'content');
  const stateDir = path.join(sessionDir, 'state');
  fs.mkdirSync(screenDir, { recursive: true });
  fs.mkdirSync(stateDir, { recursive: true });
  return { sessionDir, screenDir, stateDir };
}

function newestFile(dir, exts) {
  const entries = fs
    .readdirSync(dir)
    .filter((f) => exts.some((e) => f.endsWith(e)))
    .map((f) => {
      const full = path.join(dir, f);
      return { file: full, mtime: fs.statSync(full).mtimeMs };
    });
  if (entries.length === 0) return null;
  entries.sort((a, b) => b.mtime - a.mtime);
  return entries[0].file;
}

function frameTemplate() {
  return fs.readFileSync(path.join(__dirname, 'frame-template.html'), 'utf8');
}

function helperScript() {
  return fs.readFileSync(path.join(__dirname, 'helper.js'), 'utf8');
}

function renderScreen(screenDir) {
  const latest = newestFile(screenDir, ['.html']);
  const raw = latest
    ? fs.readFileSync(latest, 'utf8')
    : '<div class="section"><p class="subtitle">Waiting for the first screen…</p></div>';
  const trimmed = raw.trimStart();
  if (trimmed.startsWith('<!DOCTYPE') || trimmed.startsWith('<html')) {
    return raw.replace('</body>', `<script>${helperScript()}</script></body>`);
  }
  return frameTemplate()
    .replace('{{CONTENT}}', raw)
    .replace('{{HELPER_SCRIPT}}', helperScript());
}

function contentTypeFor(file) {
  const ext = path.extname(file).toLowerCase();
  return (
    {
      '.png': 'image/png',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.gif': 'image/gif',
      '.svg': 'image/svg+xml',
      '.html': 'text/html; charset=utf-8',
      '.css': 'text/css',
      '.js': 'text/javascript',
    }[ext] || 'application/octet-stream'
  );
}

function checkKey(reqUrl, headers, key) {
  const url = new URL(reqUrl, 'http://internal');
  if (url.searchParams.get('key') === key) return true;
  const cookie = headers.cookie || '';
  return cookie.split(';').some((c) => c.trim() === `spk=${key}`);
}

function appendEvent(stateDir, event) {
  fs.appendFileSync(path.join(stateDir, 'events'), JSON.stringify(event) + '\n');
}

// --- Hand-rolled WebSocket (RFC 6455), server side only, text frames only ---

function acceptKeyFor(clientKey) {
  return crypto
    .createHash('sha1')
    .update(clientKey + WS_MAGIC)
    .digest('base64');
}

function decodeFrames(buffer) {
  const messages = [];
  let offset = 0;
  while (offset + 2 <= buffer.length) {
    const b0 = buffer[offset];
    const b1 = buffer[offset + 1];
    const opcode = b0 & 0x0f;
    const masked = (b1 & 0x80) !== 0;
    let len = b1 & 0x7f;
    let pos = offset + 2;
    if (len === 126) {
      if (pos + 2 > buffer.length) break;
      len = buffer.readUInt16BE(pos);
      pos += 2;
    } else if (len === 127) {
      if (pos + 8 > buffer.length) break;
      len = Number(buffer.readBigUInt64BE(pos));
      pos += 8;
    }
    let maskKey = null;
    if (masked) {
      if (pos + 4 > buffer.length) break;
      maskKey = buffer.subarray(pos, pos + 4);
      pos += 4;
    }
    if (pos + len > buffer.length) break;
    const payload = Buffer.from(buffer.subarray(pos, pos + len));
    if (masked && maskKey) {
      for (let i = 0; i < payload.length; i++) payload[i] ^= maskKey[i % 4];
    }
    messages.push({ opcode, payload });
    offset = pos + len;
  }
  return { messages, rest: buffer.subarray(offset) };
}

function encodeTextFrame(text) {
  const payload = Buffer.from(text, 'utf8');
  const len = payload.length;
  let header;
  if (len < 126) {
    header = Buffer.from([0x81, len]);
  } else if (len < 65536) {
    header = Buffer.alloc(4);
    header[0] = 0x81;
    header[1] = 126;
    header.writeUInt16BE(len, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = 0x81;
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(len), 2);
  }
  return Buffer.concat([header, payload]);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const { sessionDir, screenDir, stateDir } = makeSessionDirs(args.projectDir);
  const key = crypto.randomBytes(16).toString('hex');
  const sockets = new Set();

  const server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://internal');

    if (url.pathname === '/') {
      if (!checkKey(req.url, req.headers, key)) {
        res.writeHead(403, { 'Content-Type': 'text/plain' });
        res.end('Missing or invalid session key');
        return;
      }
      res.writeHead(200, {
        'Content-Type': 'text/html; charset=utf-8',
        'Set-Cookie': `spk=${key}; Path=/; HttpOnly; SameSite=Strict`,
      });
      res.end(renderScreen(screenDir));
      return;
    }

    if (url.pathname.startsWith('/files/')) {
      if (!checkKey(req.url, req.headers, key)) {
        res.writeHead(403);
        res.end();
        return;
      }
      const rel = decodeURIComponent(url.pathname.slice('/files/'.length));
      const full = path.join(screenDir, rel);
      if (!full.startsWith(screenDir) || !fs.existsSync(full)) {
        res.writeHead(404);
        res.end('Not found');
        return;
      }
      res.writeHead(200, { 'Content-Type': contentTypeFor(full) });
      fs.createReadStream(full).pipe(res);
      return;
    }

    res.writeHead(404);
    res.end('Not found');
  });

  server.on('upgrade', (req, socket) => {
    if (!checkKey(req.url, req.headers, key)) {
      socket.destroy();
      return;
    }
    const clientKey = req.headers['sec-websocket-key'];
    if (!clientKey) {
      socket.destroy();
      return;
    }
    const accept = acceptKeyFor(clientKey);
    socket.write(
      'HTTP/1.1 101 Switching Protocols\r\n' +
        'Upgrade: websocket\r\n' +
        'Connection: Upgrade\r\n' +
        `Sec-WebSocket-Accept: ${accept}\r\n\r\n`
    );
    sockets.add(socket);
    let buffered = Buffer.alloc(0);
    socket.on('data', (chunk) => {
      buffered = Buffer.concat([buffered, chunk]);
      const { messages, rest } = decodeFrames(buffered);
      buffered = Buffer.from(rest);
      for (const msg of messages) {
        if (msg.opcode === 0x8) {
          socket.end();
          return;
        }
        if (msg.opcode === 0x1) {
          try {
            const event = JSON.parse(msg.payload.toString('utf8'));
            event.timestamp = event.timestamp || Date.now();
            appendEvent(stateDir, event);
          } catch (_err) {
            // Ignore malformed client payloads.
          }
        }
      }
    });
    socket.on('close', () => sockets.delete(socket));
    socket.on('error', () => sockets.delete(socket));
  });

  fs.watch(screenDir, () => {
    const frame = encodeTextFrame(JSON.stringify({ type: 'reload' }));
    for (const socket of sockets) {
      try {
        socket.write(frame);
      } catch (_err) {
        sockets.delete(socket);
      }
    }
  });

  server.listen(args.port, args.host, () => {
    const actualPort = server.address().port;
    const urlHost = args.urlHost || args.host;
    const info = {
      type: 'server-started',
      pid: process.pid,
      port: actualPort,
      url: `http://${urlHost}:${actualPort}/?key=${key}`,
      session_dir: sessionDir,
      screen_dir: screenDir,
      state_dir: stateDir,
    };
    fs.writeFileSync(path.join(stateDir, 'server-info'), JSON.stringify(info, null, 2));
    process.stdout.write(JSON.stringify(info) + '\n');

    if (args.open) {
      const opener =
        process.platform === 'darwin'
          ? { bin: 'open', args: [info.url] }
          : process.platform === 'win32'
          ? { bin: 'cmd', args: ['/c', 'start', '""', info.url] }
          : { bin: 'xdg-open', args: [info.url] };
      try {
        require('child_process').spawn(opener.bin, opener.args, { stdio: 'ignore', detached: true }).unref();
      } catch (_err) {
        // Non-fatal: the agent still has the URL to hand to the user.
      }
    }
  });

  const idleMs = args.idleTimeoutMinutes * 60 * 1000;
  let idleTimer = setTimeout(shutdown, idleMs);
  server.on('request', () => {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(shutdown, idleMs);
  });

  function shutdown() {
    fs.writeFileSync(path.join(stateDir, 'server-stopped'), String(Date.now()));
    server.close(() => process.exit(0));
    setTimeout(() => process.exit(0), 2000).unref();
  }

  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
}

main();
