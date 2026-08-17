(() => {
  const canvas = document.getElementById('masteryRadar');
  if (!canvas) return;
  let items = [];
  try { items = JSON.parse(canvas.dataset.items || '[]'); } catch (_) { return; }
  if (!items.length) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  const cx = w / 2, cy = h / 2 + 8;
  const radius = Math.min(w, h) * 0.34;
  const axes = items.length;
  const point = (index, scale) => {
    const a = -Math.PI / 2 + index * Math.PI * 2 / axes;
    return [cx + Math.cos(a) * radius * scale, cy + Math.sin(a) * radius * scale];
  };
  ctx.clearRect(0, 0, w, h);
  ctx.lineWidth = 1;
  ctx.font = '12px system-ui, sans-serif';
  for (let level = 1; level <= 5; level++) {
    ctx.beginPath();
    for (let i = 0; i < axes; i++) {
      const [x,y] = point(i, level / 5);
      if (i === 0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    }
    ctx.closePath();
    ctx.strokeStyle = '#e5e5ec';
    ctx.stroke();
  }
  for (let i = 0; i < axes; i++) {
    const [x,y] = point(i, 1);
    ctx.beginPath(); ctx.moveTo(cx,cy); ctx.lineTo(x,y); ctx.strokeStyle='#ececf2'; ctx.stroke();
    const [lx,ly] = point(i, 1.17);
    ctx.fillStyle = '#77798a';
    ctx.textAlign = lx < cx - 8 ? 'right' : lx > cx + 8 ? 'left' : 'center';
    ctx.textBaseline = ly < cy ? 'bottom' : 'top';
    ctx.fillText(items[i].label, lx, ly);
  }
  ctx.beginPath();
  items.forEach((item, i) => {
    const [x,y] = point(i, Math.max(0, Math.min(100, Number(item.score) || 0)) / 100);
    if (i === 0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
  });
  ctx.closePath();
  ctx.fillStyle = 'rgba(99, 102, 241, .15)';
  ctx.strokeStyle = '#696bd9';
  ctx.lineWidth = 2;
  ctx.fill(); ctx.stroke();
  items.forEach((item, i) => {
    const [x,y] = point(i, Math.max(0, Math.min(100, Number(item.score) || 0)) / 100);
    ctx.beginPath(); ctx.arc(x,y,4,0,Math.PI*2); ctx.fillStyle='#696bd9'; ctx.fill();
  });
})();