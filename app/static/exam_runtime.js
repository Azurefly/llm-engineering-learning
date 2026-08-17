(()=>{
  const root=document.getElementById('timedExam');
  if(!root)return;
  const form=document.getElementById('examForm');
  const timer=document.getElementById('examTimer');
  const saveState=document.getElementById('saveState');
  const submit=document.getElementById('submitExam');
  const attemptId=root.dataset.attemptId;
  let remaining=parseInt(root.dataset.remaining||'0',10);
  let dirty=false;
  let saving=false;
  let expired=false;

  const lang=document.documentElement.lang==='en'?'en':'zh';
  const text={
    saving:lang==='en'?'Saving…':'保存中…',
    saved:lang==='en'?'Draft saved':'草稿已保存',
    failed:lang==='en'?'Autosave failed':'自动保存失败',
    expired:lang==='en'?'Time expired. Submitting…':'考试时间到，正在自动交卷…'
  };

  function collect(){
    const answers={};
    form.querySelectorAll('[name^="q_"]').forEach(el=>{
      const qid=el.name.slice(2);
      if(el.type==='checkbox'){
        if(!Array.isArray(answers[qid]))answers[qid]=[];
        if(el.checked)answers[qid].push(el.value);
      }else if(el.type==='radio'){
        if(el.checked)answers[qid]=el.value;
        else if(!(qid in answers))answers[qid]='';
      }else{
        answers[qid]=el.value;
      }
    });
    return answers;
  }

  async function autosave(force=false){
    if(expired||saving||(!dirty&&!force))return;
    saving=true;
    saveState.textContent=text.saving;
    try{
      const r=await fetch(`/exam-runtime/${attemptId}/autosave`,{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({answers:collect()}),keepalive:true
      });
      if(r.status===409){
        const data=await r.json().catch(()=>({}));
        expired=true;
        if(data.redirect)location.href=data.redirect;
        return;
      }
      if(!r.ok)throw new Error('save failed');
      dirty=false;
      saveState.textContent=text.saved;
    }catch(e){
      saveState.textContent=text.failed;
    }finally{
      saving=false;
    }
  }

  async function expire(){
    if(expired)return;
    expired=true;
    submit.disabled=true;
    saveState.textContent=text.expired;
    try{
      await autosave(true);
      const r=await fetch(`/exam-runtime/${attemptId}/expire`,{method:'POST'});
      const data=await r.json();
      location.href=data.redirect||`/exam-v2/attempt/${attemptId}/result`;
    }catch(e){
      location.href=`/exam-v2/attempt/${attemptId}`;
    }
  }

  function drawTimer(){
    const m=Math.floor(Math.max(remaining,0)/60).toString().padStart(2,'0');
    const s=(Math.max(remaining,0)%60).toString().padStart(2,'0');
    timer.textContent=`${m}:${s}`;
    root.classList.toggle('time-warning',remaining<=300&&remaining>60);
    root.classList.toggle('time-danger',remaining<=60);
  }

  form.addEventListener('input',()=>{dirty=true;clearTimeout(form._saveTimer);form._saveTimer=setTimeout(()=>autosave(),900);});
  form.addEventListener('change',()=>{dirty=true;autosave();});
  form.addEventListener('submit',()=>{expired=true;submit.disabled=true;submit.textContent=lang==='en'?'Submitting…':'提交中…';});
  window.addEventListener('beforeunload',()=>{if(dirty)autosave(true);});
  setInterval(()=>autosave(),10000);
  drawTimer();
  setInterval(()=>{if(expired)return;remaining-=1;drawTimer();if(remaining<=0)expire();},1000);
})();
