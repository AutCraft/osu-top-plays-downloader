const fs = require('node:fs');
const path = require('node:path');
const { pipeline } = require('node:stream/promises');
const { Readable } = require('node:stream');
const readline = require('node:readline/promises');

const MIRRORS = [
  { name: 'Catboy', url: (id) => `https://catboy.best/d/${id}` },
  { name: 'Sayobot', url: (id) => `https://dl.sayobot.cn/beatmaps/download/novideo/${id}` },
  { name: 'Nerinyan', url: (id) => `https://api.nerinyan.moe/d/${id}?noVideo=true` },
];

const HEADERS = { 'User-Agent': 'Mozilla/5.0' };

function sanitizeFilename(filename) {
  const clean = filename.replace(/[<>:"/\\|?*\x00-\x1f]+/g, '_').replace(/^[. ]+|[. ]+$/g, '');
  return clean || 'beatmap';
}

async function resolveUserId(rawUser) {
  const trimmed = rawUser.trim();
  const urlMatch = trimmed.match(/\/(?:users|u)\/(\d+)/);
  if (urlMatch) return parseInt(urlMatch[1], 10);
  if (/^\d+$/.test(trimmed)) return parseInt(trimmed, 10);

  // Username lookup via profile redirect
  const res = await fetch(`https://osu.ppy.sh/users/${encodeURIComponent(trimmed)}`, {
    headers: HEADERS,
    redirect: 'follow',
  });
  const match = res.url.match(/\/(?:users|u)\/(\d+)/);
  if (match) return parseInt(match[1], 10);
  throw new Error(`Could not resolve user ID for: '${trimmed}'`);
}

async function fetchMaps(userId, count, mode = 1) {
  const endpoint = mode === 1 ? 'beatmapsets/most_played' : 'scores/best';
  const maps = [];
  let offset = 0;

  while (maps.length < count) {
    const limit = Math.min(100, count - maps.length);
    const url = `https://osu.ppy.sh/users/${userId}/${endpoint}?offset=${offset}&limit=${limit}`;
    const res = await fetch(url, { headers: HEADERS });
    if (!res.ok) {
      console.log(`API returned HTTP ${res.status}`);
      break;
    }
    const batch = await res.json();
    if (!Array.isArray(batch) || batch.length === 0) break;
    maps.push(...batch);
    offset += batch.length;
    if (batch.length < limit) break;
  }

  return maps;
}

function isValidZip(filePath) {
  try {
    const fd = fs.openSync(filePath, 'r');
    const buf = Buffer.alloc(4);
    fs.readSync(fd, buf, 0, 4, 0);
    fs.closeSync(fd);
    return buf[0] === 0x50 && buf[1] === 0x4b && buf[2] === 0x03 && buf[3] === 0x04;
  } catch {
    return false;
  }
}

async function downloadBeatmapset(setId, title, outputDir = './songs') {
  const safeTitle = sanitizeFilename(title);
  const filename = `${setId} ${safeTitle}.osz`;
  const targetPath = path.join(outputDir, filename);

  if (fs.existsSync(targetPath) && fs.statSync(targetPath).size > 1024) {
    console.log(`Already downloaded: ${filename}`);
    return true;
  }

  const tempPath = targetPath + '.tmp';
  for (const mirror of MIRRORS) {
    const url = mirror.url(setId);
    try {
      console.log(`  Downloading from ${mirror.name}...`);
      const res = await fetch(url, { headers: HEADERS });
      if (!res.ok || !res.body) continue;

      await pipeline(Readable.fromWeb(res.body), fs.createWriteStream(tempPath));

      if (fs.existsSync(tempPath) && fs.statSync(tempPath).size > 1024 && isValidZip(tempPath)) {
        if (fs.existsSync(targetPath)) {
          fs.unlinkSync(targetPath);
        }
        fs.renameSync(tempPath, targetPath);
        console.log(`  Saved: ${filename}`);
        return true;
      }
    } catch {
      // try next mirror
    } finally {
      if (fs.existsSync(tempPath)) {
        try {
          fs.unlinkSync(tempPath);
        } catch {}
      }
    }
  }

  console.log(`  Failed to download mapset ${setId} from all mirrors.`);
  return false;
}

async function runSelfCheck() {
  console.log('Running self-check...');
  if (sanitizeFilename('test: *?/"<>| name. ') !== 'test_ _ name') throw new Error('sanitizeFilename failed');
  if (sanitizeFilename('夜に駆ける') !== '夜に駆ける') throw new Error('unicode sanitizeFilename failed');
  const uid = await resolveUserId('2');
  if (uid !== 2) throw new Error('resolveUserId failed');
  console.log('Self-check passed!');
}

async function main() {
  if (process.argv.includes('--test')) {
    await runSelfCheck();
    return;
  }

  fs.mkdirSync('./songs', { recursive: true });

  let rawUser = '';
  let numberOfMaps = 10;
  let mode = 1;

  if (process.argv.length > 2) {
    rawUser = process.argv[2];
    numberOfMaps = process.argv[3] ? parseInt(process.argv[3], 10) : 10;
    mode = process.argv[4] ? parseInt(process.argv[4], 10) : 1;
  } else {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });

    rawUser = (await rl.question('Enter User ID, Profile URL, or Username: ')).trim();
    const numStr = (await rl.question('Enter number of maps to download (default 10): ')).trim();
    numberOfMaps = numStr ? parseInt(numStr, 10) : 10;
    const modeStr = (await rl.question('Choose mode [1: Most Played (default), 2: Top Plays (Best pp)]: ')).trim();
    mode = modeStr === '2' ? 2 : 1;

    rl.close();
  }

  let userId;
  try {
    userId = await resolveUserId(rawUser);
  } catch (err) {
    console.error(`Error: ${err.message}`);
    return;
  }

  const modeLabel = mode === 1 ? 'Most Played' : 'Top Plays (Best pp)';
  console.log(`\nFetching ${numberOfMaps} ${modeLabel} for user ID ${userId}...`);
  const rawMaps = await fetchMaps(userId, numberOfMaps, mode);

  if (!rawMaps || rawMaps.length === 0) {
    console.log('No beatmaps found.');
    return;
  }

  // Deduplicate beatmapsets
  const seen = new Set();
  const mapsets = [];
  for (const item of rawMaps) {
    const setInfo = item.beatmapset;
    if (setInfo && !seen.has(setInfo.id)) {
      seen.add(setInfo.id);
      mapsets.push({ id: setInfo.id, title: setInfo.title });
    }
  }

  const totalDifficulties = rawMaps.length;
  console.log(`Found ${mapsets.length} unique beatmapsets (${totalDifficulties} total difficulties/plays) to download.\n`);

  let success = 0;
  for (let idx = 0; idx < mapsets.length; idx++) {
    const { id: sid, title } = mapsets[idx];
    console.log(`[${idx + 1}/${mapsets.length}] Beatmapset ${sid}: ${title}`);
    if (await downloadBeatmapset(sid, title)) {
      success++;
    }
  }

  console.log(`\nDone! Downloaded ${success}/${mapsets.length} (${totalDifficulties} difficulties) beatmapsets into './songs/'.`);
}

main().catch(console.error);
