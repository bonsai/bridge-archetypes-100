const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

// UI refs
const ids = ['L','b','h','E','fb','P','support'];
const els = {};
ids.forEach(id => els[id] = document.getElementById(id));
const msg = {sigmaMax:1,tauMax:1,deltaMax:1,reqH:1,ratio:1,Pval:1,fracture:1,sigmaGauge:1,beamType:1,dispL:1,dispH:1,dispFb:1,sumoInfo:1};
for(const k in msg) msg[k] = document.getElementById(k);

let current = null;
let archetypes = [];

// Load archetypes
fetch('/archetypes').then(r=>r.json()).then(data=>{
    archetypes = data;
    const sel = document.getElementById('archetype');
    data.forEach(a=>{
        const opt = document.createElement('option');
        opt.value = a.id;
        opt.textContent = a.name;
        sel.appendChild(opt);
    });
    loadArchetype(data[0].id);
});

function loadArchetype(id){
    fetch('/archetypes/'+id).then(r=>r.json()).then(d=>{
        if(d.L_mm) document.getElementById('L').value = d.L_mm;
        if(d.b_mm) document.getElementById('b').value = d.b_mm;
        if(d.h_mm) document.getElementById('h').value = d.h_mm;
        if(d.E_MPa) document.getElementById('E').value = d.E_MPa;
        if(d.fb_MPa) document.getElementById('fb').value = d.fb_MPa;
        fetchSolve();
    });
}
document.getElementById('archetype').addEventListener('change', e=>loadArchetype(e.target.value));

function fetchSolve(){
    const body = {
        archetype_id: document.getElementById('archetype').value,
        L_mm: +els.L.value, b_mm: +els.b.value, h_mm: +els.h.value,
        E_MPa: +els.E.value, fb_MPa: +els.fb.value, P_N: +els.P.value,
        support: els.support.value
    };
    fetch('/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
    .then(r=>r.json()).then(d=>{current=d;render();});
}

function stressColor(ratio){
    // ratio 0..1 -> green, 1..1.5 -> yellow->red, >1.5 deep red
    if(ratio<=1){
        const t=ratio;
        return `rgb(${Math.round(t*255)},255,${Math.round((1-t)*150)})`;
    } else if(ratio<=1.5){
        const t=(ratio-1)/0.5;
        return `rgb(255,${Math.round(255*(1-t))},0)`;
    } else {
        return '#ff0000';
    }
}

function render(){
    if(!current) return;
    const d=current;
    msg.sigmaMax.textContent = d.sigma_max_MPa.toFixed(2);
    msg.tauMax.textContent = d.tau_max_MPa.toFixed(3);
    msg.deltaMax.textContent = d.delta_max_mm.toFixed(2);
    msg.reqH.textContent = d.required_h_mm.toFixed(1);
    msg.ratio.textContent = d.sigma_ratio.toFixed(2);
    msg.Pval.textContent = els.P.value;

    // gauge
    const g = msg.sigmaGauge;
    const pct = Math.min(d.sigma_ratio*100, 100);
    g.style.width = pct+'%';
    g.className = 'gauge-fill' + (d.sigma_ratio>1?' danger':d.sigma_ratio>0.8?' warn':'');

    // fracture
    msg.fracture.classList.toggle('show', d.fractured);

    // beam type display
    msg.beamType.textContent = els.support.value==='cantilever'?'片持ち梁':'単純支持梁';
    msg.dispL.textContent = els.L.value;
    msg.dispH.textContent = els.h.value;
    msg.dispFb.textContent = els.fb.value;

    // sumo
    const sumoKg = d.sumo_weight_kg;
    const count = Math.floor(sumoKg);
    msg.sumoInfo.textContent = `🥋 相撲力士 ${count}人分 (${count*150}kg相当)`;

    // CANVAS
    const W=canvas.width, H=canvas.height;
    ctx.clearRect(0,0,W,H);

    // margins
    const mx=80, my=80;
    const cw=W-mx*2, ch=H-my*2;
    const Lmm = +els.L.value, hmm = +els.h.value;

    // coordinate: x from mx, y center at H/2, scale
    const xscale = cw / Lmm;
    const yscale = Math.min(ch/(hmm*3), 400/hmm); // keep visible
    const centerY = H/2;

    // Draw undeformed beam outline
    ctx.strokeStyle='rgba(100,80,60,0.4)';
    ctx.lineWidth=2;
    ctx.setLineDash([4,4]);
    ctx.beginPath();
    ctx.moveTo(mx, centerY - hmm/2 * yscale);
    ctx.lineTo(mx + Lmm*xscale, centerY - hmm/2 * yscale);
    ctx.lineTo(mx + Lmm*xscale, centerY + hmm/2 * yscale);
    ctx.lineTo(mx, centerY + hmm/2 * yscale);
    ctx.closePath();
    ctx.stroke();
    ctx.setLineDash([]);

    // Support symbol
    if(els.support.value==='cantilever'){
        // fixed wall at x=0
        ctx.fillStyle='#888';
        ctx.fillRect(mx-15, centerY-hmm*yscale*1.5, 12, hmm*yscale*3);
        // hash lines
        ctx.strokeStyle='#aaa';
        for(let i=-3;i<=3;i++){
            ctx.beginPath();
            ctx.moveTo(mx-15, centerY + i*hmm*yscale*0.4);
            ctx.lineTo(mx-3, centerY + i*hmm*yscale*0.4 + 4);
            ctx.stroke();
        }
    } else {
        // simple supports at x=0 and x=L
        for(const xpos of [0, Lmm]){
            const px = mx + xpos*xscale;
            ctx.fillStyle='#888';
            ctx.beginPath();
            ctx.moveTo(px-8, centerY + hmm/2*yscale + 5);
            ctx.lineTo(px+8, centerY + hmm/2*yscale + 5);
            ctx.lineTo(px, centerY + hmm/2*yscale - 8);
            ctx.closePath();
            ctx.fill();
        }
    }

    // Deformed beam (filled strips per x segment with stress color)
    const N = d.x.length;
    const x = d.x, sigma = d.sigma, delta = d.delta;
    // magnify deflection for visibility
    const dm = Math.max(...delta);
    const defScale = dm > 0.01 ? (hmm*0.8*yscale / dm) : 0;

    for(let i=0;i<N-1;i++){
        const x0=mx+x[i]*xscale, x1=mx+x[i+1]*xscale;
        const d0=delta[i]*defScale, d1=delta[i+1]*defScale;
        const top0=centerY - hmm/2*yscale + d0;
        const top1=centerY - hmm/2*yscale + d1;
        const bot0=centerY + hmm/2*yscale + d0;
        const bot1=centerY + hmm/2*yscale + d1;

        const ratio = Math.max(0, sigma[i]/d.fb_MPa);
        ctx.fillStyle = stressColor(Math.min(ratio, 2));
        ctx.beginPath();
        ctx.moveTo(x0, top0);
        ctx.lineTo(x1, top1);
        ctx.lineTo(x1, bot1);
        ctx.lineTo(x0, bot0);
        ctx.closePath();
        ctx.fill();
    }

    // Stroke deformed centerline
    ctx.strokeStyle=d.fractured?'#ff3333':'#fff';
    ctx.lineWidth=d.fractured?3:1.5;
    ctx.beginPath();
    for(let i=0;i<N;i++){
        const px=mx+x[i]*xscale;
        const py=centerY + delta[i]*defScale;
        if(i===0) ctx.moveTo(px,py);
        else ctx.lineTo(px,py);
    }
    ctx.stroke();

    // Load arrow with sumo icon
    const loadX = els.support.value==='cantilever' ? mx+Lmm*xscale : mx+Lmm/2*xscale;
    const loadY = centerY + hmm/2*yscale + 10;
    // arrow
    ctx.strokeStyle='#fff';
    ctx.fillStyle='#fff';
    ctx.lineWidth=2;
    ctx.beginPath();
    ctx.moveTo(loadX, loadY);
    ctx.lineTo(loadX, loadY+40);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(loadX-6, loadY+32);
    ctx.lineTo(loadX, loadY+40);
    ctx.lineTo(loadX+6, loadY+32);
    ctx.stroke();
    ctx.font='bold 14px sans-serif';
    ctx.fillText(`${els.P.value}N`, loadX+10, loadY+24);

    // Sumo icon position
    const sumoEl = document.getElementById('sumo');
    sumoEl.style.left = (canvas.getBoundingClientRect().left + loadX - 20) + 'px';
    sumoEl.style.bottom = (H - loadY - 40) + 'px';
    sumoEl.textContent = d.fractured ? '💥' : (d.sumo_weight_kg >= 1 ? '🥋' : '');
    sumoEl.style.opacity = d.sumo_weight_kg > 0.1 ? 0.9 : 0.2;

    // If fractured, draw crack
    if(d.fractured){
        ctx.strokeStyle='#ff0000';
        ctx.lineWidth=4;
        const cx = mx + Lmm*xscale*0.7;
        const cy = centerY + Math.max(...delta)*defScale;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx+20, cy-15);
        ctx.lineTo(cx+35, cy-5);
        ctx.lineTo(cx+50, cy-20);
        ctx.stroke();
    }

    // Scale annotation
    ctx.fillStyle='#888';
    ctx.font='11px sans-serif';
    ctx.fillText(`たわみ倍率 ×${defScale.toFixed(1)}`, mx, H-10);
}

// events
els.P.addEventListener('input', ()=>{msg.Pval.textContent=els.P.value;fetchSolve();});
['L','b','h','E','fb','support'].forEach(id=>els[id].addEventListener('change',fetchSolve));

// autoplay
let autoDir=1;
document.getElementById('autoplay').addEventListener('click',()=>{
    if(autoTimer){clearInterval(autoTimer);autoTimer=null;return;}
    els.P.value=0; fetchSolve();
    autoTimer = setInterval(()=>{
        let v = +els.P.value + autoDir*200;
        if(v>80000){autoDir=-1;v=80000;}
        if(v<0){autoDir=1;v=0;}
        els.P.value=v;
        fetchSolve();
        if(current && current.fractured && autoDir>0){
            // pause at fracture
            clearInterval(autoTimer); autoTimer=null;
        }
    }, 80);
});

fetchSolve();
