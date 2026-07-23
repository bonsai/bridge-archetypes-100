// beam-art.js - Beginner-friendly structural mechanics art
// Self-contained, no backend needed for static GH Pages

const canvas = document.getElementById('beamCanvas');
const ctx = canvas.getContext('2d');

// Master data
const materials = {
  sugi2: { E: 10000, fb: 12, name: 'スギ2級', color: '#d4a574' },
  hinoki: { E: 12000, fb: 14, name: 'ヒノキ', color: '#c9a96e' },
  matsu: { E: 11000, fb: 13, name: 'マツ', color: '#b8956a' },
  steel: { E: 200000, fb: 210, name: '鋼SM400', color: '#789' },
  rc: { E: 30000, fb: 18, name: 'RC', color: '#999' },
};

// State
let state = {
  L: 4000,  // mm
  b: 200,
  h: 300,
  P: 0,
  mat: 'sugi2',
};

// DOM refs
const ids = ['L','h','b','P','material'];
const els = {};
ids.forEach(id => { els[id] = document.getElementById(id); });

function compute(){
  const L = state.L, b = state.b, h = state.h, P = state.P;
  const mat = materials[state.mat];
  const I = b * h**3 / 12;
  const Z = b * h**2 / 6;
  const A = b * h;
  const E = mat.E;

  // Cantilever analytical
  const Mmax = P * L;
  const sigma = Mmax / Z;
  const delta = P * L**3 / (3 * E * I);
  const tau = 3 * P / (2 * A);
  const ratio = sigma / mat.fb;

  return { sigma, delta, tau, ratio, Z, mat, Mmax };
}

function stressColor(ratio){
  if (ratio <= 0.3) return { r: 78, g: 205, b: 196 };  // teal (low)
  if (ratio <= 0.6) return { r: 255, g: 230, b: 109 }; // yellow
  if (ratio <= 0.9) return { r: 255, g: 107, b: 107 }; // salmon
  if (ratio <= 1.0) return { r: 255, g: 50, b: 50 };   // red warning
  return { r: 255, g: 0, b: 0 }; // critical flashing
}

function draw(){
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const { sigma, delta, ratio, Z, mat, Mmax } = compute();

  // Geometry layout
  const mx = 60, my = 80;
  const cw = W - mx * 2, ch = H - my * 2;

  // Scale x: L fits in cw
  const xscale = cw / state.L;
  // Beam height in pixels (exaggerated for visibility)
  const beamH_px = Math.min(state.h * 0.15, 60);
  const cy = H / 2;

  // Deflection scale (amplify for visual)
  const maxDef = state.L * 0.15; // max visual deflection px
  const realDefRatio = Math.min(delta / (state.L * 0.3), 1);
  const defPx = realDefRatio * maxDef;

  // Stress color
  const sc = stressColor(ratio);
  const stressStr = `rgb(${sc.r},${sc.g},${sc.b})`;

  const N = 60;
  const xs = Array.from({length: N+1}, (_, i) => i * state.L / N);

  // Draw undeformed reference (dotted)
  ctx.strokeStyle = 'rgba(150,150,180,0.3)';
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(mx, cy - beamH_px/2);
  ctx.lineTo(mx + state.L*xscale, cy - beamH_px/2);
  ctx.lineTo(mx + state.L*xscale, cy + beamH_px/2);
  ctx.lineTo(mx, cy + beamH_px/2);
  ctx.closePath();
  ctx.stroke();
  ctx.setLineDash([]);

  // Fixed support (wall at left)
  ctx.fillStyle = '#556';
  ctx.fillRect(mx-12, cy - beamH_px*2, 10, beamH_px*4);
  // Hatching
  ctx.strokeStyle = '#778';
  ctx.lineWidth = 1;
  for(let i=-3; i<=3; i++){
    ctx.beginPath();
    ctx.moveTo(mx-12, cy + i*beamH_px*0.5);
    ctx.lineTo(mx-3, cy + i*beamH_px*0.5 + 3);
    ctx.stroke();
  }

  // Draw deformed beam as gradient strip
  for(let i=0; i<N; i++){
    const x0 = mx + xs[i]*xscale;
    const x1 = mx + xs[i+1]*xscale;
    const d0 = (xs[i]/state.L)**2 * (3 - xs[i]/state.L) * defPx;
    const d1 = (xs[i+1]/state.L)**2 * (3 - xs[i+1]/state.L) * defPx;

    const top0 = cy - beamH_px/2 + d0;
    const top1 = cy - beamH_px/2 + d1;
    const bot0 = cy + beamH_px/2 + d0;
    const bot1 = cy + beamH_px/2 + d1;

    const segRatio = ratio * (1 - xs[i]/state.L); // stress varies along x
    const segColor = stressColor(segRatio);
    ctx.fillStyle = `rgba(${segColor.r},${segColor.g},${segColor.b},0.75)`;
    ctx.beginPath();
    ctx.moveTo(x0, top0);
    ctx.lineTo(x1, top1);
    ctx.lineTo(x1, bot1);
    ctx.lineTo(x0, bot0);
    ctx.closePath();
    ctx.fill();
  }

  // Neutron (stress fiber) lines
  const nf = 5;
  for(let fi=0; fi<nf; fi++){
    const yoff = (fi - nf/2) * (beamH_px / nf);
    ctx.beginPath();
    ctx.strokeStyle = `rgba(255,255,255,${0.15 + fi*0.05})`;
    ctx.lineWidth = 1;
    for(let i=0; i<=N; i++){
      const x = mx + xs[i]*xscale;
      const d = (xs[i]/state.L)**2 * (3 - xs[i]/state.L) * defPx;
      const y = cy + yoff + d;
      if(i===0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  // Load arrow
  const tipX = mx + state.L * xscale;
  const tipY = cy + beamH_px/2 + defPx + 10;
  ctx.strokeStyle = '#fff';
  ctx.fillStyle = '#fff';
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.moveTo(tipX, tipY);
  ctx.lineTo(tipX, tipY + 40);
  ctx.stroke();
  // Arrow head
  ctx.beginPath();
  ctx.moveTo(tipX-8, tipY+32);
  ctx.lineTo(tipX, tipY+40);
  ctx.lineTo(tipX+8, tipY+32);
  ctx.stroke();

  // Load text
  ctx.font = 'bold 13px sans-serif';
  ctx.fillText(`${(state.P/1000).toFixed(1)} kN`, tipX+14, tipY+28);

  // Scale annotation
  ctx.fillStyle = '#778';
  ctx.font = '11px sans-serif';
  ctx.fillText(`たわみ倍率 ×${(maxDef / (delta||1)).toFixed(1)}`, mx, H-15);

  // Stress bar on right side
  const barW = 12, barH = 120;
  const barX = W - 30, barY = (H - barH)/2;
  // Background
  ctx.fillStyle = '#222';
  ctx.fillRect(barX, barY, barW, barH);
  // Fill
  const fillH = Math.min(ratio, 1) * barH;
  const grad = ctx.createLinearGradient(barX, barY+barH, barX, barY);
  grad.addColorStop(0, '#4ecdc4');
  grad.addColorStop(0.5, '#ffe66d');
  grad.addColorStop(1, '#ff0000');
  ctx.fillStyle = grad;
  ctx.fillRect(barX, barY + barH - fillH, barW, fillH);

  if (ratio > 1) {
    // Critical flash
    ctx.strokeStyle = `rgba(255,0,0,${0.5 + 0.5*Math.sin(Date.now()/200)})`;
    ctx.lineWidth = 3;
    ctx.strokeRect(barX-2, barY-2, barW+4, barH+4);
  }

  // Update stats
  document.getElementById('sigmaDisp').textContent = sigma.toFixed(1);
  document.getElementById('fbDisp').textContent = mat.fb;
  document.getElementById('ratioDisp').textContent = ratio.toFixed(2);
  document.getElementById('deltaDisp').textContent = (delta*1000).toFixed(2);
  document.getElementById('ZDisp').textContent = (Z/1e6).toFixed(2);

  const sumoCount = Math.floor(state.P / 9.81 / 150);
  document.getElementById('sumoDisp').textContent = sumoCount;

  const resultCard = document.getElementById('resultCard');
  const resultDisp = document.getElementById('resultDisp');
  if (ratio > 1) {
    resultCard.classList.add('fractured');
    resultDisp.textContent = '💥 破断';
    document.getElementById('fractureOverlay').classList.add('show');
  } else if (ratio > 0.9) {
    resultCard.classList.remove('fractured');
    resultDisp.textContent = '⚠️ 危険';
    document.getElementById('fractureOverlay').classList.remove('show');
  } else {
    resultCard.classList.remove('fractured');
    resultDisp.textContent = '✅ OK';
    document.getElementById('fractureOverlay').classList.remove('show');
  }

  // Sumo garden
  const garden = document.getElementById('sumoGarden');
  const targetCount = Math.max(0, sumoCount);
  const currentCount = garden.children.length;
  if (currentCount < targetCount) {
    for(let i=currentCount; i<targetCount; i++){
      const div = document.createElement('div');
      div.className = 'sumo-figure';
      div.textContent = '🥋';
      div.style.animationDelay = `${Math.random()*0.5}s`;
      garden.appendChild(div);
    }
  } else if (currentCount > targetCount) {
    while(garden.children.length > targetCount) {
      garden.removeChild(garden.lastChild);
    }
  }
  document.getElementById('sumoText').textContent =
    targetCount > 0 ? `合計 ${targetCount} 人 × 150kg = ${(targetCount*150/1000).toFixed(1)}t` : '力士を増やして橋に挑戦！';
}

// Event binding
function updateState(){
  state.L = parseFloat(els.L.value) * 1000;
  state.h = parseInt(els.h.value);
  state.b = parseInt(els.b.value);
  state.P = parseInt(els.P.value);
  state.mat = els.material.value;

  document.getElementById('Lval').textContent = (state.L/1000).toFixed(1) + ' m';
  document.getElementById('hval').textContent = state.h + ' mm';
  document.getElementById('bval').textContent = state.b + ' mm';
  document.getElementById('Pval').textContent = state.P;

  draw();
}

ids.forEach(id => {
  els[id].addEventListener('input', updateState);
});

// Animation loop
function animate(){
  draw();
  requestAnimationFrame(animate);
}

updateState();
animate();
