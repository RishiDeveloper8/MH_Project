// main.js - handles forms and fetch calls for all pages
document.addEventListener('DOMContentLoaded', ()=> {
  // Dashboard: fetch summary and handle add transaction
  if (document.querySelector('#txnForm')) {
    loadSummary();
    document.querySelector('#txnForm').addEventListener('submit', async (e)=>{
      e.preventDefault();
      const type = document.getElementById('txnType').value;
      const amount = document.getElementById('txnAmount').value;
      const description = document.getElementById('txnDesc').value;
      const res = await fetch('/api/transaction', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({type, amount, description})
      });
      const j = await res.json();
      if (j.success) {
        document.getElementById('txnForm').reset();
        setTotals(j.totals);
        alert('Transaction added');
      } else {
        alert(j.error || 'Error');
      }
    });
  }

  // Transactions page: pagination + chart
  if (document.querySelector('#txnTableBody')) {
    window.txnPage = 1;
    loadTxnPage(1);
    document.getElementById('nextBtn').addEventListener('click', ()=> loadTxnPage(window.txnPage+1));
    document.getElementById('prevBtn').addEventListener('click', ()=> loadTxnPage(Math.max(1, window.txnPage-1)));
    loadChart();
  }

  // Bills page
  if (document.querySelector('#billForm')) {
    // prefill date to today
    const d = new Date().toISOString().slice(0,10); document.getElementById('billDate').value = d;
    loadBills();
    document.getElementById('billForm').addEventListener('submit', async (e)=>{
      e.preventDefault();
      const bill_type = document.getElementById('billType').value;
      const amount = document.getElementById('billAmount').value;
      const date = document.getElementById('billDate').value;
      const time_period = document.getElementById('billPeriod').value;
      const priority = document.getElementById('billPriority').value;
      const res = await fetch('/api/bill', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({bill_type, amount, date, time_period, priority})
      });
      const j = await res.json();
      if (j.success) {
        alert('Bill added');
        loadBills();
        document.getElementById('billForm').reset();
      } else alert(j.error || 'Error');
    });
  }

  // Goals page
  if (document.querySelector('#goalForm')) {
    loadGoals();
    document.getElementById('goalForm').addEventListener('submit', async (e)=>{
      e.preventDefault();
      const name = document.getElementById('goalName').value;
      const months = document.getElementById('goalMonths').value;
      const amount = document.getElementById('goalAmount').value;
      const res = await fetch('/api/goal', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({name, months, amount})
      });
      const j = await res.json();
      if (j.success) {
        alert('Goal added');
        loadGoals();
      } else alert(j.error || 'Error');
    });
  }

  // Learning page
  if (document.querySelector('#learningForm')) {
    loadLearning();
    document.getElementById('learningForm').addEventListener('submit', async (e)=>{
      e.preventDefault();
      const type = document.getElementById('learningType').value;
      const name = document.getElementById('learningName').value;
      const content = document.getElementById('learningContent').value;
      const image = document.getElementById('learningImage').value;
      const code = document.getElementById('learningCode').value;
      const res = await fetch('/api/learning', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({type, name, content, image, code})
      });
      const j = await res.json();
      if (j.success) {
        alert('Content added');
        loadLearning();
        document.getElementById('learningForm').reset();
      } else alert(j.error || 'Error');
    });
  }

  // Advisor page (simple local chat mock)
  if (document.querySelector('#personalBtn')) {
    document.getElementById('personalBtn').addEventListener('click', ()=> openChat('personal'));
    document.getElementById('tradingBtn').addEventListener('click', ()=> openChat('trading'));
  }
});

async function loadSummary(){
  const res = await fetch('/api/summary');
  if (!res.ok) return;
  const j = await res.json();
  setTotals(j);
}

function setTotals(t) {
  document.getElementById('totalIncome').textContent = t.total_income.toFixed(2);
  document.getElementById('totalExpense').textContent = t.total_expense.toFixed(2);
  document.getElementById('netBalance').textContent = t.net_balance.toFixed(2);
}

// Transactions pagination
async function loadTxnPage(page=1){
  const res = await fetch(`/api/transactions?page=${page}`);
  const j = await res.json();
  const tbody = document.getElementById('txnTableBody');
  tbody.innerHTML = '';
  j.items.forEach(it=>{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${it.type}</td><td>${it.amount.toFixed(2)}</td><td>${it.description}</td><td>${new Date(it.timestamp).toLocaleString()}</td>`;
    tbody.appendChild(tr);
  });
  window.txnPage = j.page;
  document.getElementById('pageInfo').textContent = `Page ${j.page} of ${j.total_pages}`;
}

// Chart: uses Chart.js if present, else simple bars text fallback
async function loadChart(){
  const res = await fetch('/api/chart-data');
  const j = await res.json();
  // create simple chart using canvas if Chart.js not included. (For hackathon minimal)
  const canvas = document.getElementById('mainChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  // clear
  ctx.clearRect(0,0,canvas.width,canvas.height);
  // draw simple bars for expense and net (not pretty but functional)
  const labels = j.labels.slice(-20); // last 20 for space
  const exp = j.expense.slice(-20);
  const net = j.net_balance.slice(-20);
  // Draw expense bars (red) and net line (yellow)
  const w = canvas.width; const h = canvas.height;
  const barW = Math.max(6, Math.floor(w / labels.length / 2));
  const maxExp = Math.max(1, Math.max(...exp));
  // expense
  exp.forEach((v,i)=>{
    const x = i * (w/labels.length) + 10;
    const bh = (v / maxExp) * (h*0.5);
    ctx.fillStyle = 'rgba(255,80,80,0.9)';
    ctx.fillRect(x, h - bh - 30, barW, bh);
  });
  // net (dots+line)
  ctx.strokeStyle = 'rgb(240,200,50)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  net.forEach((v,i)=>{
    const x = i * (w/labels.length) + 10 + barW;
    const y = h - ( (v - Math.min(...net)) / (Math.max(...net) - Math.min(...net) + 1) * (h*0.6) ) - 40;
    if (i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
  });
  ctx.stroke();
}

// Bills functions
async function loadBills(){
  const res = await fetch('/api/bills');
  const j = await res.json();
  const upEl = document.getElementById('upcomingBills');
  const allEl = document.getElementById('allBills');
  upEl.innerHTML = ''; allEl.innerHTML = '';
  j.upcoming.forEach(b=>{
    const card = createBillCard(b, true);
    upEl.appendChild(card);
  });
  j.all.forEach(b=>{
    const card = createBillCard(b, false);
    allEl.appendChild(card);
  });
}
function createBillCard(b, isUpcoming){
  const div = document.createElement('div');
  div.className = 'card';
  div.innerHTML = `<h4>${b.bill_type}</h4><p>Amount: ${b.amount.toFixed(2)}</p><p>Next Due: ${b.next_due}</p><p>Period: ${b.time_period}</p>`;
  const btn = document.createElement('button');
  btn.textContent = 'Paid';
  btn.addEventListener('click', async ()=>{
    if (!confirm('Mark as paid?')) return;
    const res = await fetch(`/api/bill/${b.id}/paid`, {method:'POST'});
    const r = await res.json();
    if (r.success) { alert('Marked paid'); loadBills(); } else alert('Error');
  });
  const del = document.createElement('button');
  del.textContent = 'Delete';
  del.addEventListener('click', async ()=>{
    if (!confirm('Are you sure to delete this bill?')) return;
    const res = await fetch(`/api/bill/${b.id}`, {method:'DELETE'});
    const r = await res.json();
    if (r.success) { alert('Deleted'); loadBills(); } else alert('Error');
  });
  div.appendChild(btn); div.appendChild(del);
  return div;
}

// Goals
async function loadGoals(){
  const res = await fetch('/api/goals');
  const j = await res.json();
  const grid = document.getElementById('goalsGrid');
  grid.innerHTML = '';
  j.goals.forEach(g=>{
    const card = document.createElement('div'); card.className = 'card';
    let contributedTotal = g.contributions.reduce((s,c)=>s + (c.contributed_amount||0), 0);
    const remaining = g.target_amount - contributedTotal;
    card.innerHTML = `<h4>${g.name}</h4><p>Target: ${g.target_amount.toFixed(2)}</p><p>Remaining: ${remaining.toFixed(2)}</p>`;
    // months grid
    const monthsDiv = document.createElement('div');
    monthsDiv.style.display='flex'; monthsDiv.style.gap='6px'; monthsDiv.style.flexWrap='wrap';
    g.contributions.forEach(c=>{
      const mbtn = document.createElement('button');
      mbtn.textContent = `M${c.month_index}${c.contributed? ' ✓': ''}`;
      mbtn.disabled = c.contributed;
      mbtn.addEventListener('click', async ()=>{
        const res = await fetch(`/api/goal/${g.id}/contribute`, {method:'POST',headers:{'Content-Type':'application/json'},body: JSON.stringify({month_index: c.month_index})});
        const r = await res.json();
        if (r.success) loadGoals(); else alert('Error');
      });
      monthsDiv.appendChild(mbtn);
    });
    card.appendChild(monthsDiv);
    grid.appendChild(card);
  });
}

// Learning
async function loadLearning(){
  const res = await fetch('/api/learning');
  if (!res.ok) return;
  const j = await res.json();
  const list = document.getElementById('learningList');
  list.innerHTML = '';
  j.items.forEach(it=>{
    const card = document.createElement('div'); card.className='card';
    card.innerHTML = `<h4>${it.name}</h4><p>Type: ${it.type}</p><p>${it.content}</p>`;
    list.appendChild(card);
  });
}

// Advisor chat simple mock (no external LLM integration in this minimal repo)
function openChat(mode){
  document.getElementById('chatBlock').style.display = 'block';
  const win = document.getElementById('chatWindow');
  win.innerHTML = `<div><em>Chat mode: ${mode}. This is a mock chat for the hackathon. Integrate Groq/LLM as needed.</em></div>`;
  const form = document.getElementById('chatForm');
  form.removeEventListener('submit', submitChat);
  form.addEventListener('submit', submitChat);
  function submitChat(e){
    e.preventDefault();
    const msg = document.getElementById('chatInput').value;
    if(!msg) return;
    const p = document.createElement('div'); p.textContent = 'You: ' + msg; win.appendChild(p);
    // mock reply
    const r = document.createElement('div'); r.textContent = 'Advisor: This is a placeholder reply. Integrate LLM for real answers.'; win.appendChild(r);
    document.getElementById('chatInput').value = '';
    win.scrollTop = win.scrollHeight;
  }
}
