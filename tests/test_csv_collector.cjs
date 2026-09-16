'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const {webcrypto} = require('node:crypto');
const {gunzipSync} = require('node:zlib');
const source = fs.readFileSync(require('node:path').join(__dirname, '../scripts/collect_csv_reference.js'), 'utf8');

async function browser({robots='User-agent: *\nCrawl-delay: 10', responses=[], origin='https://www.csv-bibel.de', locked=false}={}) {
  let now=100000;
  const rows=new Map(), storage=new Map(), requests=[];
  const db={createObjectStore(){}, transaction(){
    const tx={};
    tx.objectStore=()=>Object.fromEntries(Object.entries({
      get:key=>rows.get(key), put:value=>{rows.set(value.key,value);return value.key;},
      count:()=>rows.size,getAll:()=>[...rows.values()],getAllKeys:()=>[...rows.keys()].sort()
    }).map(([key,fn])=>[key,(...args)=>{const request={result:fn(...args)};queueMicrotask(()=>tx.oncomplete());return request;}]));
    return tx;
  }};
  class Clock extends Date { static now(){return now;} }
  const context={window:{},location:{origin},navigator:{locks:{async request(name,options,fn){
    if(locked)return fn(null);locked=true;try{return await fn({name});}finally{locked=false;}
  }}},indexedDB:{open(){
    const request={result:db};queueMicrotask(()=>{request.onupgradeneeded();request.onsuccess();});return request;
  }},localStorage:{getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)},
  setTimeout:(fn,ms)=>{now+=ms;queueMicrotask(fn);},Date:Clock,
  Blob,Response,TextEncoder,CompressionStream,Uint8Array,crypto:webcrypto,AbortSignal,
  btoa:binary=>Buffer.from(binary,'binary').toString('base64'),
  DOMParser:class {parseFromString(html){return {querySelector:selector=>html.includes(selector.slice(1))?{}:null};}},
  fetch:async path=>{
    requests.push({path,time:now});
    const value=path==='/robots.txt'?{status:200,body:robots}:(responses.shift()||{status:200,body:'bible-verse-text bible-book-1'});
    return {ok:value.status===200,status:value.status,url:origin+path,headers:new Headers(),text:async()=>value.body};
  }, URL, Bible:{BookChapters:{},BookUrlPaths:{}}};
  await vm.runInNewContext(source,context);
  return {api:context.window.akribosCSV,rows,requests};
}
const chapters=[{book:1,chapter:1,path:'/bibel/1-mose-1'},{book:1,chapter:2,path:'/bibel/1-mose-2'}];

test('serial requests obey robots delay; cache resumes without chapter requests', async()=>{
  const b=await browser({robots:'User-agent: *\nCrawl-delay: 15'});
  let status=await b.api.start(chapters);
  assert.equal(status.error,null);assert.equal(status.cached,2);assert.equal(status.done,2);
  assert.deepEqual(b.requests.map(r=>r.time),[100000,115000,130000]);
  const first=b.rows.get('01.001');
  assert.equal(gunzipSync(Buffer.from(first.html_gzip_base64,'base64')).toString(),'bible-verse-text bible-book-1');
  assert.match(first.sha256,/^[a-f0-9]{64}$/);
  status=await b.api.start(chapters);
  assert.equal(status.done,2);assert.equal(b.requests.length,4);
  assert.equal(b.requests[3].path,'/robots.txt');
});
for(const status of [403,429,503]) test(`HTTP ${status} stops with no retry or incomplete cache`,async()=>{
  const b=await browser({responses:[{status,body:'blocked'}]});
  const result=await b.api.start(chapters);
  assert.match(result.error,new RegExp(`HTTP ${status}`));assert.equal(result.running,false);
  assert.equal(result.cached,0);assert.equal(b.requests.length,2);
});
test('successful HTTP carrying a challenge is not cached as Bible data',async()=>{
  const b=await browser({responses:[{status:200,body:'<html>Challenge</html>'}]});
  assert.match((await b.api.start(chapters)).error,/Missing Bible content/);
  assert.equal(b.rows.size,0);
});
test('robots disallow stops all chapter requests',async()=>{
  const b=await browser({robots:'User-agent: *\nDisallow: /bibel/'});
  assert.match((await b.api.start(chapters)).error,/Disallow/);assert.equal(b.requests.length,1);
});
test('only expected origin and chapter paths are accepted',async()=>{
  await assert.rejects(browser({origin:'https://other.example'}),/Open csv-bibel.de/);
  const b=await browser();
  const result=await b.api.start([{book:1,chapter:1,path:'https://other.example/bibel/1-mose-1'}]);
  assert.match(result.error,/Invalid chapter/);assert.equal(b.requests.length,1);
});
test('another tab holding the acquisition lock prevents all requests',async()=>{
  const b=await browser({locked:true});
  await assert.rejects(b.api.start(chapters),/Another tab/);
  assert.equal(b.requests.length,0);
});
