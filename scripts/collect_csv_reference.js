/* Run on an ordinary, already open https://www.csv-bibel.de/bibel/... page.
 * Read-only reference acquisition: one request at a time, robots Crawl-delay,
 * persistent private browser cache; stop on every HTTP error or access block.
 * No cookies, credentials, challenge solvers or reference text belong in Git.
 */
(async () => {
  'use strict';
  if (location.origin !== 'https://www.csv-bibel.de') throw Error('Open csv-bibel.de first');
  if (window.akribosCSV?.running) throw Error('Collector already running');
  const db = await new Promise((resolve, reject) => {
    const request = indexedDB.open('akribos-csv-reference-v1', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('chapters', {keyPath:'key'});
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  const access = (mode, fn) => new Promise((resolve, reject) => {
    const tx = db.transaction('chapters', mode);
    const request = fn(tx.objectStore('chapters'));
    tx.oncomplete = () => resolve(request.result);
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error || Error('Cache transaction aborted'));
  });
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  let lastRequest = Number(localStorage.getItem('akribos-csv-last-request') || 0);
  let delay = 10000;
  const get = async path => {
    await sleep(Math.max(0, lastRequest + delay - Date.now()));
    if (api.stopped) throw Error('Stopped');
    lastRequest = Date.now();
    localStorage.setItem('akribos-csv-last-request', String(lastRequest));
    const response = await fetch(path, {signal:AbortSignal.timeout(45000)});
    if (!response.ok) throw Error(`HTTP ${response.status}: ${path}; retry-after=${response.headers.get('retry-after') || ''}`);
    if (new URL(response.url).origin !== location.origin) throw Error('Unexpected redirect');
    return response.text();
  };
  const api = window.akribosCSV = {
    running:false, stopped:false, error:null, done:0, total:0, current:null,
    stop() { this.stopped = true; },
    async status() { return {running:this.running, error:this.error, done:this.done, total:this.total, current:this.current, cached:await access('readonly', s=>s.count()), delayMs:delay}; },
    async records(offset=0, limit=5, excludedKeys=[]) {
      const excluded = new Set(excludedKeys);
      const keys = (await access('readonly', s=>s.getAllKeys())).filter(key=>!excluded.has(key));
      const records = [];
      for (const key of keys.slice(offset, offset+limit)) records.push(await access('readonly', s=>s.get(key)));
      return records;
    },
    async download() {
      const rows = await access('readonly', s=>s.getAll());
      const url = URL.createObjectURL(new Blob([JSON.stringify(rows)], {type:'application/json'}));
      const link = document.createElement('a'); link.href=url; link.download='chunk-browser.json'; link.click();
      setTimeout(()=>URL.revokeObjectURL(url), 60000);
    },
    async start(chapters=null) {
      if (!navigator.locks) throw Error('Browser Web Locks support is required');
      return navigator.locks.request('akribos-csv-reference-acquisition', {ifAvailable:true}, async lock => {
        if (!lock) throw Error('Another tab is already acquiring this reference');
        return this._collect(chapters);
      });
    },
    async _collect(chapters=null) {
      if (this.running) throw Error('Collector already running');
      this.running=true; this.stopped=false; this.error=null; this.done=0;
      try {
        const robots = await get('/robots.txt');
        if (/<html|challenge/i.test(robots)) throw Error('Access block instead of robots.txt');
        // Conservative: stop on any disallow; never work around site rules.
        if (/^Disallow:\s*\S+/im.test(robots)) throw Error('robots.txt contains Disallow; review rules before acquisition');
        const delays = Array.from(robots.matchAll(/^Crawl-delay:\s*(\d+(?:\.\d+)?)/gim), m=>Number(m[1])*1000);
        delay = Math.max(10000, ...delays);
        if (!chapters) {
          if (typeof Bible==='undefined' || !Bible.BookChapters || !Bible.BookUrlPaths) throw Error('No public book index');
          chapters=[];
          for (let book=1; book<=66; book++) {
            if (!Number.isInteger(Bible.BookChapters[book]) || !/^[a-z0-9-]+$/.test(Bible.BookUrlPaths[book])) throw Error('Invalid book index');
            for (let chapter=1; chapter<=Bible.BookChapters[book]; chapter++) chapters.push({book,chapter,path:`/bibel/${Bible.BookUrlPaths[book]}-${chapter}`});
          }
        }
        this.total=chapters.length;
        for (const item of chapters) {
          if (this.stopped) break;
          if (!Number.isInteger(item.book) || item.book<1 || item.book>66 || !Number.isInteger(item.chapter) || item.chapter<1 || !/^\/bibel\/[a-z0-9-]+-\d+$/.test(item.path)) throw Error('Invalid chapter');
          const key=String(item.book).padStart(2,'0')+'.'+String(item.chapter).padStart(3,'0');
          this.current=key;
          if (await access('readonly', s=>s.get(key))) { this.done++; continue; }
          const html=await get(item.path);
          const documentCopy=new DOMParser().parseFromString(html,'text/html');
          if (!documentCopy.querySelector('.bible-verse-text') || !documentCopy.querySelector('.bible-book-'+item.book)) throw Error(`Missing Bible content: ${item.path}`);
          const bytes=new TextEncoder().encode(html);
          const sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)), x=>x.toString(16).padStart(2,'0')).join('');
          const packed=new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer());
          let binary=''; for (const byte of packed) binary+=String.fromCharCode(byte);
          await access('readwrite', s=>s.put({key,book:item.book,chapter:item.chapter,url:location.origin+item.path,retrieved_at:new Date().toISOString(),sha256,html_gzip_base64:btoa(binary)}));
          this.done++;
        }
      } catch(error) { this.error=String(error); }
      finally { this.running=false; }
      return this.status();
    }
  };
  return api.status();
})();
