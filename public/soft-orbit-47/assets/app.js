(()=>{
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  let currentAudio=null;
  $$('audio').forEach(audio=>{
    audio.setAttribute('playsinline','');
    audio.addEventListener('play',()=>{ if(currentAudio&&currentAudio!==audio) currentAudio.pause(); currentAudio=audio; });
  });
  $$('[data-sound-check]').forEach(button=>button.addEventListener('click',async()=>{
    const target=$(button.dataset.soundCheck);
    const state=$('.sound-state');
    if(!target){ if(state) state.textContent='Audio file missing'; return; }
    try{ target.currentTime=0; await target.play(); if(state) state.textContent='Sound enabled ✓'; button.textContent='Replay test sound'; }
    catch(error){ if(state) state.textContent='Tap the native play control below ↘'; console.warn('Audio playback blocked',error); }
  }));
  $$('[data-meter]').forEach(button=>button.addEventListener('click',()=>{
    const count=Number(button.dataset.meter), display=$('.meter-display');
    if(!display)return;
    display.innerHTML=Array.from({length:count},(_,i)=>`<span class="meter-beat ${i===0?'strong':''}">${i+1}</span>`).join('');
    $$('[data-meter]').forEach(b=>b.classList.toggle('active',b===button));
  }));
  $$('.cell').forEach(cell=>cell.addEventListener('click',()=>cell.classList.toggle('on')));
  $$('[data-preset]').forEach(button=>button.addEventListener('click',()=>{
    const pattern=(button.dataset.preset||'').split('').map(Number);
    const grid=$(button.dataset.grid||'.rhythm-grid'); if(!grid)return;
    $$('.cell',grid).forEach((cell,i)=>cell.classList.toggle('on',Boolean(pattern[i])));
    $$('[data-preset]').forEach(b=>b.classList.toggle('active',b===button));
  }));
  $$('[data-demo-grid]').forEach(button=>button.addEventListener('click',()=>{
    const grid=$(button.dataset.demoGrid); if(!grid)return;
    const cells=$$('.cell',grid); let i=0; button.disabled=true;
    const timer=setInterval(()=>{ cells.forEach(c=>c.classList.remove('pulse')); cells[i]?.classList.add('pulse'); i++; if(i>=cells.length){clearInterval(timer);button.disabled=false;} },250);
  }));
  const reveal=()=>$$('[data-reveal]').forEach(el=>{const y=el.getBoundingClientRect().top;if(y<innerHeight*.9)el.classList.add('revealed')});
  addEventListener('scroll',reveal,{passive:true}); reveal();
  $$('[data-celebrate]').forEach(el=>el.addEventListener('click',()=>{
    for(let i=0;i<24;i++){const c=document.createElement('i');c.className='confetti';c.style.left=`${Math.random()*100}vw`;c.style.top='-20px';c.style.background=['#eaff33','#ff6b56','#3157ff','#ff9fe4'][i%4];c.style.setProperty('--x',`${(Math.random()-.5)*300}px`);document.body.append(c);setTimeout(()=>c.remove(),1600)}
  }));
})();
