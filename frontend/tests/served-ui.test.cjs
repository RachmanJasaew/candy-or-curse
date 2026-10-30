const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const script = fs.readFileSync('dist/index.html', 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
function setup(transcription) {
  let stopped = false;
  const elements = new Map();
  const context = vm.createContext({
    window: {location:{pathname:'/',origin:'https://test.local'}, MediaRecorder:true},
    document: {getElementById(id) {
      if (!elements.has(id)) elements.set(id,{innerHTML:'',play:()=>Promise.resolve()});
      return elements.get(id);
    }},
    localStorage: {getItem:()=>null,setItem(){}}, console, Blob, FormData,
    navigator:{mediaDevices:{getUserMedia:async()=>({getTracks:()=>[{stop(){stopped=true;}}]})}},
    setInterval(){},setTimeout(){},clearTimeout(){},
    fetch: async (url, options) => {
      if (url==='/api/health') return new Promise(()=>{});
      assert.equal(url,'/api/voice/transcribe');
      const audio = options.body.get('audio');
      assert.equal(audio.type,'audio/mp4');
      assert.equal(audio.name,'recording.mp4');
      return transcription;
    },
    MediaRecorder: class {
      static isTypeSupported(type) { return type==='audio/mp4'; }
      constructor(stream,options) { this.stream=stream; this.mimeType=options.mimeType; }
      start(){}
      stop(){this.ondataavailable({data:new Blob(['voice'])});this.stopPromise=this.onstop();}
    },
  });
  vm.runInContext(script,context);
  vm.runInContext(`state.sessionId='sess_test';state.session={session_id:'sess_test',dietary_profile:{parsed_restrictions:[]},chat_history:[]};state.voiceConfigured=true;`,context);
  return {context, stopped:()=>stopped, elements};
}
test('microphone preserves Safari MP4 and requires review before sending',async()=>{
  const {context,stopped}=setup({ok:true,json:async()=>({text:'Test transcript',provider:'scribe_v1'})});
  await context.window.toggleRecording();
  assert.equal(vm.runInContext('state.isRecording',context),true);
  await context.window.toggleRecording();
  await vm.runInContext('state.mediaRecorder.stopPromise',context);
  assert.equal(vm.runInContext('state.chatDraft',context),'Test transcript');
  assert.equal(vm.runInContext('state.session.chat_history.length',context),0);
  assert.equal(stopped(),true);
});
test('transcription errors leave the profile and draft unchanged',async()=>{
  const {context}=setup({ok:false,json:async()=>({detail:'Voice transcription failed.'})});
  await context.window.toggleRecording();await context.window.toggleRecording();
  await vm.runInContext('state.mediaRecorder.stopPromise',context);
  assert.equal(vm.runInContext('state.chatDraft',context),'');
  assert.match(vm.runInContext('state.error',context),/failed/);
  assert.equal(vm.runInContext('state.session.dietary_profile.parsed_restrictions.length',context),0);
});
test('mobile camera stream survives rendering and only one scan can be in flight',()=>{
  const {context,elements}=setup({});
  vm.runInContext("state.mode='mobile';state.cameraActive=true;state.cameraStream={camera:true};render();",context);
  assert.equal(elements.get('cameraPreview').srcObject.camera,true);
  vm.runInContext('state.busy=true;runScan({});',context);
  assert.equal(vm.runInContext('state.busy',context),true);
});
