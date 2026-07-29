(() => {
  'use strict';
  const KEY = 'niblet-learning-lab-v1';
  const fresh = () => ({
    version: 1, screen: 0, startedAt: Date.now(), updatedAt: Date.now(), hiddenCount: 0,
    screens: {}, ratings: {}, choices: {}, order: null, formats: {
      animation: {plays:0,replays:0,maxTime:0,completed:false},
      daw: {plays:0,replays:0,maxTime:0,completed:false}
    },
    formatChecks: {animation:{played:false,answer:null,correct:null,latency:null},daw:{played:false,answer:null,correct:null,latency:null}},
    participation: {requiredPlayed:false,requiredAnswer:null,requiredLatency:null,optionalPlayed:false,optionalAnswer:null,optionalLatency:null},
    result: null
  });
  let state;
  try { state = {...fresh(), ...JSON.parse(localStorage.getItem(KEY) || '{}')}; } catch (_) { state = fresh(); }
  state.formats = {...fresh().formats, ...(state.formats || {})};
  state.formatChecks = {...fresh().formatChecks, ...(state.formatChecks || {})};
  state.participation = {...fresh().participation, ...(state.participation || {})};
  state.order ||= Math.random() < 0.5 ? ['animation','daw'] : ['daw','animation'];
  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => [...r.querySelectorAll(s)];
  const save = () => { state.updatedAt = Date.now(); localStorage.setItem(KEY, JSON.stringify(state)); };
  function applyTrialOrder() {
    state.order.forEach((kind,index) => {
      const section = $(`[data-format="${kind}"]`).closest('.screen');
      section.dataset.screen = String(index + 1);
      $('.trial-head .kicker',section).textContent = `Format trial 0${index + 1} / 02`;
    });
  }
  applyTrialOrder();

  function showScreen(n) {
    const previous = state.screen;
    const now = Date.now();
    state.screens[previous] = (state.screens[previous] || 0) + Math.max(0, now - (state.screenStartedAt || now));
    state.screen = Math.max(0, Math.min(6, Number(n)));
    state.screenStartedAt = now;
    $$('.screen').forEach(s => s.classList.toggle('active', Number(s.dataset.screen) === state.screen));
    $('#progressBar').style.width = `${(state.screen / 6) * 100}%`;
    window.scrollTo({top:0, behavior:'smooth'});
    if (state.screen === 6) renderResult();
    save();
  }

  const captions = [
    [0,'A note is a target, not just a name.'],[6,'A4 vibrates 440 times each second.'],[13,'When the sounds settle together, you are centered.'],
    [21,'Faster vibration rises above the target: sharp.'],[30,'Slower vibration falls below the target: flat.'],[40,'Compare direction: above, below, or centered.'],
    [49,'This attempt sits above the target. It is sharp.'],[57,'This trace falls below the line. The voice is flat.'],[64,'A tuner shows the same relationship.']
  ];
  function cueAt(t) { let text=captions[0][1]; for (const [time,caption] of captions) if (t>=time) text=caption; return text; }
  function pitchState(t) {
    if (t < 18) return 0;
    if (t < 29) return 1;
    if (t < 39) return -1;
    if (t < 48) return 0;
    if (t < 56) return 1;
    if (t < 63) return -1;
    return 0;
  }
  function updateAnimation(t, playing) {
    $('#captionA').textContent = cueAt(t);
    const p = pitchState(t), orb=$('#animationOrb');
    orb.style.top = `calc(${p===1?'24%':p===-1?'76%':'50%'} - 29px)`;
    orb.style.background = p===1?'var(--pink)':p===-1?'var(--coral)':'var(--cyan)';
    $('.animation-cinema').classList.toggle('playing', playing);
  }
  function updateDaw(t) {
    $('#captionB').textContent = cueAt(t);
    const p=pitchState(t), top=p===1?20:p===-1?67:43;
    $('#voiceNote').style.top=`${top}%`;
    $('#tunerNeedle').style.transform=`rotate(${p*42}deg)`;
    $('#tunerReadout').textContent = p===1?'A♯4 · +37 cents':p===-1?'A♭4 · −32 cents':'A4 · 0 cents';
    $('#dawPlayhead').style.left=`${2+(t/69.4)*96}%`;
  }
  function unlockRating(kind) {
    const box = kind==='animation' ? $('#ratingA') : $('#ratingB');
    box.classList.remove('locked');
    box.firstElementChild.textContent='Rate the experience you actually had.';
    maybeEnableRating(box);
  }
  function wireAudio(id, kind, update) {
    const audio=$(id), metric=state.formats[kind];
    audio.addEventListener('play', () => {
      if (audio.currentTime < 2 && metric.maxTime > 10) metric.replays++;
      metric.plays++; metric.lastStartedAt=Date.now(); save(); update(audio.currentTime,true);
    });
    audio.addEventListener('pause', () => { metric.pauses=(metric.pauses||0)+1; save(); update(audio.currentTime,false); });
    audio.addEventListener('seeking', () => { metric.seeks=(metric.seeks||0)+1; save(); });
    audio.addEventListener('timeupdate', () => {
      metric.maxTime=Math.max(metric.maxTime,audio.currentTime); update(audio.currentTime,!audio.paused);
      if (metric.maxTime>=45) unlockRating(kind);
      if (Math.floor(audio.currentTime)%5===0) save();
    });
    audio.addEventListener('ended', () => { metric.completed=true; metric.maxTime=audio.duration; unlockRating(kind); save(); });
    if (metric.maxTime>=45 || metric.completed) unlockRating(kind);
    update(0,false);
  }

  function buildScales() {
    $$('.rating-row').forEach(row => {
      const key=row.dataset.rating, scale=$('.scale',row);
      for(let i=1;i<=5;i++) {
        const b=document.createElement('button'); b.type='button'; b.textContent=i; b.setAttribute('aria-label',`${i} out of 5`);
        if(state.ratings[key]===i)b.classList.add('selected');
        b.addEventListener('click',()=>{state.ratings[key]=i;$$('button',scale).forEach(x=>x.classList.toggle('selected',x===b));maybeEnableRating(row.closest('.rating'));save();});
        scale.appendChild(b);
      }
    });
  }
  function maybeEnableRating(box) {
    if(box.classList.contains('locked'))return;
    const keys=$$('.rating-row',box).map(r=>r.dataset.rating);
    const kind=box.id==='ratingA'?'animation':'daw';
    $('[data-next]',box).disabled=!(keys.every(k=>state.ratings[k]) && state.formatChecks[kind].answer);
  }

  $$('[data-next]').forEach(btn=>btn.addEventListener('click',()=>showScreen(state.screen+1)));
  $$('[data-choice]').forEach(btn=>{
    const key=btn.dataset.choice;
    if(state.choices[key]===btn.dataset.value)btn.classList.add('selected');
    btn.addEventListener('click',()=>{
      state.choices[key]=btn.dataset.value;
      $$(`[data-choice="${key}"]`).forEach(x=>x.classList.toggle('selected',x===btn));
      $('[data-screen="3"] [data-next]').disabled=false; save();
    });
  });
  $('#formatNote').value=state.choices.formatNote||'';
  $('#formatNote').addEventListener('input',e=>{state.choices.formatNote=e.target.value;save();});
  if(state.choices.formatPreference)$('[data-screen="3"] [data-next]').disabled=false;

  let audioCtx, toneStarted={};
  function tone(freq,start,duration=.72,gain=.13){
    const osc=audioCtx.createOscillator(),g=audioCtx.createGain(); osc.type='sine';osc.frequency.value=freq;g.gain.setValueAtTime(.0001,start);g.gain.exponentialRampToValueAtTime(gain,start+.03);g.gain.exponentialRampToValueAtTime(.0001,start+duration);osc.connect(g).connect(audioCtx.destination);osc.start(start);osc.stop(start+duration+.05);
  }
  // Parallel neutral checks: equal pitch distance, direction swapped between formats.
  const firstDirection = state.order[0] === 'animation' ? 'sharp' : 'flat';
  const checkDirections = {
    [state.order[0]]: firstDirection,
    [state.order[1]]: firstDirection === 'sharp' ? 'flat' : 'sharp'
  };
  $$('[data-format-check]').forEach(check => {
    const kind=check.dataset.formatCheck, metric=state.formatChecks[kind], answers=$('.check-answers',check);
    if(metric.answer){answers.classList.add('ready');$$('[data-answer]',answers).forEach(b=>b.classList.toggle('selected',b.dataset.answer===metric.answer));$('.check-feedback',check).textContent=metric.correct?'Correct — recorded separately from your preference.':`This attempt was ${checkDirections[kind]}.`;}
    $('.play-check',check).addEventListener('click',async()=>{
      audioCtx ||= new (window.AudioContext||window.webkitAudioContext)();await audioCtx.resume();metric.played=true;metric.startedAt=performance.now();
      const now=audioCtx.currentTime+.05;tone(440,now);tone(checkDirections[kind]==='sharp'?466.16:415.30,now+1.05);answers.classList.remove('ready');setTimeout(()=>answers.classList.add('ready'),1700);save();
    });
    $$('[data-answer]',answers).forEach(btn=>btn.addEventListener('click',()=>{
      metric.answer=btn.dataset.answer;metric.correct=metric.answer===checkDirections[kind];metric.latency=metric.startedAt?Math.round(performance.now()-metric.startedAt):null;
      $$('[data-answer]',answers).forEach(b=>b.classList.toggle('selected',b===btn));$('.check-feedback',check).textContent=metric.correct?'Correct — recorded separately from your preference.':`This attempt was ${checkDirections[kind]}.`;
      maybeEnableRating(check.closest('.rating'));save();
    }));
  });
  $$('[data-tone-trial]').forEach(btn=>btn.addEventListener('click',async()=>{
    const kind=btn.dataset.toneTrial;
    audioCtx ||= new (window.AudioContext||window.webkitAudioContext)(); await audioCtx.resume();
    toneStarted[kind]=performance.now(); state.participation[`${kind}Played`]=true;
    const now=audioCtx.currentTime+.05; tone(440,now); tone(kind==='required'?466.16:415.30,now+1.05);
    const set=$(`[data-answer-set="${kind}"]`); set.classList.remove('ready');
    setTimeout(()=>set.classList.add('ready'),1700); save();
  }));
  $$('[data-answer-set]').forEach(set=>$$('[data-answer]',set).forEach(btn=>btn.addEventListener('click',()=>{
    const kind=set.dataset.answerSet, answer=btn.dataset.answer, correct=kind==='required'?'sharp':'flat';
    state.participation[`${kind}Answer`]=answer; state.participation[`${kind}Correct`]=answer===correct;
    state.participation[`${kind}Latency`]=toneStarted[kind]?Math.round(performance.now()-toneStarted[kind]):null;
    $$('button',set).forEach(x=>x.classList.toggle('selected',x===btn));
    $(`#${kind}Feedback`).textContent=answer===correct?'Correct — you tracked the direction.':`The attempt was ${correct}. The direction matters more than the note name.`;
    if(kind==='required'){$('#optionalZone').classList.remove('locked');$('[data-screen="4"]>[data-next]').disabled=false;}
    save();
  })));
  if(state.participation.requiredAnswer){$('#optionalZone').classList.remove('locked');$('[data-screen="4"]>[data-next]').disabled=false;}

  $$('[data-single]').forEach(set=>{
    const key=set.dataset.single;
    $$('button',set).forEach(btn=>{
      if(state.choices[key]===btn.dataset.value)btn.classList.add('selected');
      btn.addEventListener('click',()=>{state.choices[key]=btn.dataset.value;$$('button',set).forEach(x=>x.classList.toggle('selected',x===btn));validateContract();save();});
    });
  });
  $$('[data-multi]').forEach(set=>{
    const key=set.dataset.multi; state.choices[key] ||= [];
    $$('button',set).forEach(btn=>{
      if(state.choices[key].includes(btn.dataset.value))btn.classList.add('selected');
      btn.addEventListener('click',()=>{const v=btn.dataset.value,a=state.choices[key];a.includes(v)?a.splice(a.indexOf(v),1):a.push(v);btn.classList.toggle('selected');validateContract();save();});
    });
  });
  function validateContract(){ $('[data-screen="5"] [data-next]').disabled=!(state.choices.lessonMinutes&&state.choices.ending&&(state.choices.mechanisms||[]).length); }
  validateContract();

  function scoreFormat(kind){return ['Attention','Clarity','More'].reduce((s,k)=>s+(state.ratings[kind+k]||0),0)+(state.choices.formatPreference===kind?2:0)+(state.formatChecks[kind].correct?4:0);}
  function resultData(){
    const a=scoreFormat('animation'),d=scoreFormat('daw'),pref=state.choices.formatPreference;
    const bothChecks=state.formatChecks.animation.answer&&state.formatChecks.daw.answer;
    const format=!bothChecks||pref==='adaptive'||Math.abs(a-d)<=3?'Adaptive narrated animation + DAW':a>d?'Narrated animation':'DAW-guided demonstration';
    const participated=!!state.participation.optionalPlayed;
    const interaction=participated?'Required micro-checkpoints + optional bonus':'Brief required checkpoints, clean stopping points';
    const minutes=state.choices.lessonMinutes==='8'?'7–10 minutes':`${state.choices.lessonMinutes||'?'} minutes`;
    const confidence=(state.formats.animation.maxTime>=45&&state.formats.daw.maxTime>=45&&Object.keys(state.ratings).length===6&&bothChecks)?'Provisional · one task today':'Incomplete · engagement signal only';
    return {format,interaction,minutes,mechanisms:state.choices.mechanisms||[],confidence,scores:{animation:a,daw:d},learningChecks:state.formatChecks,order:state.order,formatPreference:pref,ratings:state.ratings,behavior:{formats:state.formats,participation:state.participation,hiddenCount:state.hiddenCount},note:state.choices.formatNote||'',ending:state.choices.ending,generatedAt:new Date().toISOString()};
  }
  function renderResult(){
    const r=resultData();state.result=r;save();
    $('#resultTitle').textContent='A format hypothesis—not a box.';$('#resultFormat').textContent=r.format;
    const checkSummary=`Neutral checks: animation ${r.learningChecks.animation.correct?'correct':'incorrect'}; DAW ${r.learningChecks.daw.correct?'correct':'incorrect'}. Order: ${r.order.join(' → ')}.`;
    $('#resultWhy').textContent=`Animation scored ${r.scores.animation}; DAW scored ${r.scores.daw}. ${checkSummary} Appeal and learning evidence remain separate in the export.`;
    $('#resultParticipation').textContent=r.interaction;$('#resultParticipationWhy').textContent=r.behavior.participation.optionalPlayed?'You chose to continue after the required checkpoint.':'You completed the required checkpoint without opting into the extra trial.';
    $('#resultContract').textContent=`${r.minutes} · ${r.ending==='bonus'?'optional bonus':r.ending==='adaptive'?'adaptive extension':'clean ending'}`;
    $('#resultMechanisms').textContent=r.mechanisms.length?r.mechanisms.join(' · '):'No mechanisms selected';$('#resultConfidence').textContent=r.confidence;
    const compact=btoa(unescape(encodeURIComponent(JSON.stringify(r))));
    $('#exportText').value=`NIBLET-LAB-V1:${compact}`;
  }
  $('[data-export-results]').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('#exportText').value);$('#copyState').textContent='Copied. Paste this code into our Telegram chat.';}catch(_){$('#exportText').select();document.execCommand('copy');$('#copyState').textContent='Copied. Paste it into Telegram.';}});
  $('#downloadResults').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(state.result,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='niblet-learning-lab.json';a.click();URL.revokeObjectURL(a.href);});
  $('#reviewLab').addEventListener('click',()=>showScreen(0));
  $('#resetLab').addEventListener('click',()=>{if(confirm('Erase this lab run and start over?')){localStorage.removeItem(KEY);location.reload();}});
  document.addEventListener('visibilitychange',()=>{if(document.hidden){state.hiddenCount++;save();}});

  buildScales();wireAudio('#audioA','animation',updateAnimation);wireAudio('#audioB','daw',updateDaw);
  showScreen(state.screen||0);
})();
