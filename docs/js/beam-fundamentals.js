// beam-fundamentals.js - Drag + spring-bounce cantilever beam simulator
const canvas = document.getElementById('beamCanvas');
const ctx = canvas.getContext('2d');

// ===== MATERIALS =====
const materials = {
  sugi2:  { E: 10000, fb: 12,  name: 'スギ2級', color: '#d4a574', desc: '木造建築で最も一般的' },
  hinoki: { E: 12000, fb: 14,  name: 'ヒノキ',  color: '#c9a96e', desc: '高級材・耐水性良好' },
  matsu:  { E: 11000, fb: 13,  name: 'マツ',    color: '#b8956a', desc: '構造用集成材の原料' },
  steel:  { E: 200000,fb: 210, name: '鋼SM400', color: '#789',   desc: '鉄骨構造・高強度' },
  pipe:   { E: 200000,fb: 160, name: '鉄単管パイプφ48.6', color: '#a0a8b8', desc: '仮設足場・柔軟性重視', isPipe: true },
  rc:     { E: 30000, fb: 18,  name: 'RC',      color: '#999',   desc: '鉄筋コンクリート' },
};

// ===== STATE =====
let state = {
  L: 4000,
  b: 200,
  h: 300,
  mat: 'sugi2',
  deflection: 0,
  vel: 0,
  isDragging: false,
  isBroken: false,
  time: 0,
};

// Spring-mass constants
const MASS = 80;
const DAMPING = 0.06;
let dragY0 = 0; // where drag started

// DOM
const els = {};
['L','h','b','material'].forEach(id => els[id] = document.getElementById(id));

// ===== PHYSICS =====
function getStiffness() {
  const mat = materials[state.mat];
  const I = state.b * state.h**3 / 12;
  return 3 * mat.E * I / state.L**3;
}

function computeFromDeflection(delta) {
  const mat = materials[state.mat];
  const E = mat.E;
  const I = state.b * state.h**3 / 12;
  const Z = state.b * state.h**2 / 6;
  const A = state.b * state.h;
  const P = 3 * E * I * Math.abs(delta) / state.L**3;
  const sign = delta >= 0 ? 1 : -1;
  const Mmax = P * state.L;
  const sigma = Mmax / Z;
  const ratio = sigma / mat.fb;
  return { sigma, delta, ratio, Z, mat, Mmax, P: P * sign };
}

// ===== COLOR =====
function stressColor(ratio) {
  if (state.isBroken) return { r: 60, g: 40, b: 40 };
  if (ratio <= 0.3) return { r: 78,  g: 205, b: 196 };
  if (ratio <= 0.6) return { r: 255, g: 230, b: 109 };
  if (ratio <= 0.85) return { r: 255, g: 150, b: 80 };
  if (ratio <= 1.0) return { r: 255, g: 60,  b: 60 };
  return { r: 255, g: 0, b: 0 };
}

// ===== DRAW =====
function draw() {
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);
  const { sigma, delta, ratio, Z, mat, P } = computeFromDeflection(state.deflection);

  const mx = 80, cy = H/2;
  const cw = W - mx*2 - 50;
  const xscale = cw / state.L;

  // visual deflection (scaled for display)
  const maxVisDef = state.L * 0.15;
  const visRatio = Math.min(Math.abs(delta) / (state.L*0.3), 1);
  const defPx = visRatio * maxVisDef * (delta >= 0 ? 1 : -1);

  const beamH_px = Math.min(state.h * 0.12, 50);
  const N = 50;

  // ---- Reference undeformed ----
  ctx.strokeStyle = 'rgba(150,150,180,0.3)';
  ctx.setLineDash([4,4]);
  ctx.lineWidth = 1;
  ctx.strokeRect(mx, cy-beamH_px/2, state.L*xscale, beamH_px);
  ctx.setLineDash([]);

  // ---- Fixed wall ----
  ctx.fillStyle = state.isBroken ? '#533' : '#556';
  ctx.fillRect(mx-14, cy-beamH_px*2.5, 12, beamH_px*5);
  ctx.strokeStyle = state.isBroken ? '#933' : '#778';
  for(let i=-4; i<=4; i++){
    ctx.beginPath(); ctx.moveTo(mx-14, cy+i*beamH_px*0.5); ctx.lineTo(mx-4, cy+i*beamH_px*0.5+4); ctx.stroke();
  }

  // ---- Deformed beam ----
  const sc = stressColor(Math.abs(ratio));
  const xs = Array.from({length:N+1},(_,i)=>i*state.L/N);

  for(let i=0; i<N; i++){
    const x0=mx+xs[i]*xscale, x1=mx+xs[i+1]*xscale;
    const f0=(xs[i]/state.L)**2*(3-xs[i]/state.L)/2;
    const f1=(xs[i+1]/state.L)**2*(3-xs[i+1]/state.L)/2;
    const d0=f0*defPx, d1=f1*defPx;
    const r=Math.abs(ratio)*(xs[i]/state.L);
    const c=stressColor(r);

    // Pulsate near fracture
    let alpha = 0.8;
    if(r>0.8 && !state.isBroken) alpha = 0.6 + 0.4*Math.abs(Math.sin(state.time*0.012));

    ctx.fillStyle = `rgba(${c.r},${c.g},${c.b},${alpha})`;
    ctx.beginPath();
    ctx.moveTo(x0, cy-beamH_px/2+d0);
    ctx.lineTo(x1, cy-beamH_px/2+d1);
    ctx.lineTo(x1, cy+beamH_px/2+d1);
    ctx.lineTo(x0, cy+beamH_px/2+d0);
    ctx.closePath();
    ctx.fill();
  }

  // ---- Crack if broken ----
  if(state.isBroken){
    const cx=mx+state.L*xscale*0.35;
    ctx.strokeStyle='#ff1111'; ctx.lineWidth=3;
    ctx.beginPath(); ctx.moveTo(cx,cy-beamH_px*0.8); ctx.lineTo(cx+12,cy-beamH_px*0.3);
    ctx.lineTo(cx-7,cy+beamH_px*0.1); ctx.lineTo(cx+10,cy+beamH_px*0.7); ctx.stroke();
    ctx.fillStyle='#ff0000'; ctx.font='bold 22px sans-serif';
    ctx.fillText('CRACK', cx-25, cy-beamH_px);
  }

  // ---- Tip handle / load ----
  const tipX=mx+state.L*xscale;
  const tipY=cy+defPx;
  ctx.font='22px sans-serif';
  ctx.fillText(state.isDragging ? '👆' : '👇', tipX+5, tipY);
  ctx.fillStyle='#fff'; ctx.font='bold 13px sans-serif';
  ctx.fillText(`${(Math.abs(P)/1000).toFixed(1)} kN`, tipX+35, tipY+5);

  // ---- Stress bar ----
  drawStressBar(W-38, 30, 16, 160, Math.abs(ratio));

  // ---- DOM update ----
  document.getElementById('sigmaDisp').textContent = sigma.toFixed(1);
  document.getElementById('fbDisp').textContent = mat.fb;
  document.getElementById('ratioDisp').textContent = Math.abs(ratio).toFixed(2);
  document.getElementById('deltaDisp').textContent = Math.abs(delta).toFixed(2);
  document.getElementById('ZDisp').textContent = (Z/1e6).toFixed(2);
  document.getElementById('PDisp').textContent = Math.abs(P).toFixed(0);

  const rc=document.getElementById('resultCard');
  const rd=document.getElementById('resultDisp');
  if(state.isBroken){ rc.classList.add('fractured'); rd.textContent='💥 破断'; }
  else if(Math.abs(ratio)>0.85){ rc.classList.remove('fractured'); rd.textContent='⚠️ 危険'; }
  else{ rc.classList.remove('fractured'); rd.textContent='✅ OK'; }

  const fo=document.getElementById('fractureOverlay');
  if(Math.abs(ratio)>0.9 && !state.isBroken){
    fo.style.display='block';
    fo.style.background=`rgba(255,0,0,${0.03+0.08*Math.abs(Math.sin(state.time*0.018))})`;
  } else if(state.isBroken){
    fo.style.display='block'; fo.style.background='rgba(255,0,0,0.15)';
  } else {
    fo.style.display='none';
  }

  state.time += 16;
}

function drawStressBar(x,y,w,h,ratio){
  ctx.fillStyle='#1a1a2a'; ctx.fillRect(x-2,y-2,w+4,h+4);
  const g=ctx.createLinearGradient(x,y+h,x,y);
  g.addColorStop(0,'#4ecdc4'); g.addColorStop(0.5,'#ffe66d');
  g.addColorStop(0.85,'#ff6b6b'); g.addColorStop(1,'#ff0000');
  ctx.fillStyle=g; ctx.fillRect(x,y,w,h);
  const fill=Math.min(ratio,1)*h;
  ctx.fillStyle='rgba(0,0,0,0.55)'; ctx.fillRect(x,y,w,h-fill);

  // fb line marker
  ctx.strokeStyle='#fff'; ctx.setLineDash([2,2]); ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(x-4,y+h); ctx.lineTo(x+w+4,y+h); ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle='#bbb'; ctx.font='9px sans-serif';
  ctx.fillText('fb', x-18, y+h+3);

  // Range labels
  ctx.fillText('安全', x+w+4, y+h);
  ctx.fillText('注意', x+w+4, y+h*0.4);
  ctx.fillText('破断', x+w+4, y+9);
}

// ===== PHYSICS STEP =====
function physicsStep(){
  if(state.isDragging) return;
  const k = state.isBroken ? getStiffness()*0.05 : getStiffness();
  const z = state.isBroken ? 0.008 : DAMPING;
  const c = 2*z*Math.sqrt(k*MASS);
  const fGrav = MASS*9.81; // gravity always pulls down
  const fSpring = -k*state.deflection;
  const fDamp = -c*state.vel;
  const a = (fGrav+fSpring+fDamp)/MASS;
  state.vel += a*0.016;
  state.deflection += state.vel*0.016;

  // Floor constraint (beam can't go through ground)
  if(state.deflection > state.L*0.5){ state.deflection=state.L*0.5; state.vel*=-0.3; }

  // Fracture check
  if(!state.isBroken){
    const {ratio} = computeFromDeflection(state.deflection);
    if(ratio>1.0){ state.isBroken=true; state.vel+=(Math.random()-0.5)*800; }
  }
}

// ===== INPUT =====
function getPos(e){
  const r=canvas.getBoundingClientRect();
  const ex=e.touches?e.touches[0].clientX:e.clientX;
  const ey=e.touches?e.touches[0].clientY:e.clientY;
  return { x:(ex-r.left)*(canvas.width/r.width), y:(ey-r.top)*(canvas.height/r.height) };
}
function isNearTip(pos){
  const W=canvas.width, H=canvas.height;
  const mx=80, cy=H/2;
  const cw=W-mx*2-50;
  const x=cw/state.L;
  const {delta}=computeFromDeflection(state.deflection);
  const vd=(Math.min(Math.abs(delta)/(state.L*0.3),1))*state.L*0.15*(delta>=0?1:-1);
  const tx=mx+state.L*x, ty=cy+vd;
  return Math.hypot(pos.x-tx, pos.y-ty) < 70;
}

function startDrag(e){
  const p=getPos(e);
  if(isNearTip(p)){ state.isDragging=true; state.vel=0; dragY0=p.y; }
}
function moveDrag(clientY){
  if(!state.isDragging) return;
  const r=canvas.getBoundingClientRect();
  const y=(clientY-r.top)*(canvas.height/r.height);
  const cy=canvas.height/2;
  const defPx=y-cy;
  const cw=canvas.width-80*2-50;
  const xscale=cw/state.L;
  const deltaMm=defPx/(xscale*0.5);
  state.deflection=Math.max(-state.L*0.3, Math.min(state.L*0.5, deltaMm));
}
function endDrag(){ state.isDragging=false; }

canvas.addEventListener('mousedown', e=>startDrag(e));
canvas.addEventListener('touchstart', e=>{e.preventDefault(); startDrag(e);}, {passive:false});
canvas.addEventListener('mousemove', e=>moveDrag(e.clientY));
canvas.addEventListener('touchmove', e=>{e.preventDefault(); moveDrag(e.touches[0].clientY);}, {passive:false});
canvas.addEventListener('mouseup', endDrag);
canvas.addEventListener('mouseleave', endDrag);
canvas.addEventListener('touchend', endDrag);

// ===== CONTROLS =====
function updateState(){
  state.L=parseFloat(els.L.value)*1000;
  state.h=parseInt(els.h.value);
  state.b=parseInt(els.b.value);
  state.mat=els.material.value;
  state.isBroken=false; state.deflection=0; state.vel=0;

  document.getElementById('Lval').textContent=(state.L/1000).toFixed(1)+' m';
  document.getElementById('hval').textContent=state.h+' mm';
  document.getElementById('bval').textContent=state.b+' mm';

  const m=materials[state.mat];
  const de=document.getElementById('matDesc');
  const pn=document.getElementById('pipeNote');
  if(de) de.textContent=m.desc;
  if(pn) pn.style.display=m.isPipe?'block':'none';
}
['L','h','b','material'].forEach(id=>els[id].addEventListener('input',updateState));

// ===== LOOP =====
function loop(){ physicsStep(); draw(); requestAnimationFrame(loop); }
updateState(); loop();
