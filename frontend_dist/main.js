async function loadSchema(){
  const res = await fetch('/schema');
  const schema = await res.json();
  renderForm(schema);
}

function renderForm(schema){
  const app = document.getElementById('app');
  let stepIndex = 0;
  const form = {};
  const msgDiv = document.createElement('div');
  function showStep(){
    app.innerHTML = '';
    const step = schema.steps[stepIndex];
    const h = document.createElement('div');
    h.innerHTML = `<strong>Step ${stepIndex+1} / ${schema.steps.length}: ${step.heading}</strong>`;
    app.appendChild(h);
    step.fields.forEach(f => {
      const label = document.createElement('label');
      label.textContent = (f.label || f.name || f.id) + (f.required ? ' *' : '');
      const input = document.createElement('input');
      input.name = f.name || f.id;
      input.placeholder = f.placeholder || '';
      input.value = form[input.name] || '';
      input.oninput = (e)=>{ form[input.name]=e.target.value; };
      app.appendChild(label);
      app.appendChild(input);
      if(f.inferred_validation && f.inferred_validation.description){
        const small = document.createElement('small');
        small.style.color='#666';
        small.textContent = f.inferred_validation.description;
        app.appendChild(small);
      }
    });
    const btnDiv = document.createElement('div');
    btnDiv.style.marginTop='10px';
    if(stepIndex>0){
      const back = document.createElement('button');
      back.textContent='Back'; back.className='btn';
      back.onclick = ()=>{ stepIndex--; showStep(); };
      btnDiv.appendChild(back);
    }
    const next = document.createElement('button');
    next.textContent = stepIndex < schema.steps.length-1 ? 'Next' : 'Submit';
    next.className='btn';
    next.onclick = async ()=>{
      if(stepIndex < schema.steps.length-1){ stepIndex++; showStep(); return; }
      // submit
      try{
        const resp = await fetch('/submit', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({payload: form})});
        const data = await resp.json();
        if(!resp.ok) throw data;
        msgDiv.textContent = 'Saved. id: ' + data.id; msgDiv.style.color='green';
      }catch(e){ msgDiv.textContent = JSON.stringify(e); msgDiv.style.color='red'; }
    };
    btnDiv.appendChild(next);
    app.appendChild(btnDiv);
    app.appendChild(msgDiv);
  }
  showStep();
}

loadSchema();
