'use strict';
const $ = id => document.getElementById(id);
let editingId = null;
let tasks = [];
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const niceDate = value => value ? new Date(`${value}T12:00:00`).toLocaleDateString(undefined, {month:'short',day:'numeric',year:'numeric'}) : 'No deadline';
async function api(path, options = {}) {
  const res = await fetch(path, {headers:{'Content-Type':'application/json'}, ...options});
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}
function notify(message = '') { $('message').textContent = message; }
async function refresh() {
  try {
    const params = new URLSearchParams();
    for (const key of ['status','priority']) if ($(key).value) params.set(key,$(key).value);
    if ($('search').value.trim()) params.set('q',$('search').value.trim());
    const [result, summary] = await Promise.all([api('/api/tasks?' + params), api('/api/summary')]);
    tasks = result.tasks;
    $('total').textContent = summary.total;
    $('completed').textContent = summary.completed;
    $('dueToday').textContent = summary.due_today;
    $('overdue').textContent = summary.overdue;
    $('count').textContent = tasks.length;
    render();
    notify();
  } catch(e) { notify(e.message); }
}
function render() {
  if (!tasks.length) {
    $('tasks').innerHTML = '<div class="empty"><div class="empty-icon">✦</div><strong>No tasks found</strong><div>Add a task or adjust your filters to get started.</div></div>';
    return;
  }
  $('tasks').innerHTML = tasks.map(t => `<article class="task ${t.status === 'done' ? 'done' : ''}">
    <input class="task-check" type="checkbox" data-action="toggle" data-id="${t.id}" ${t.status === 'done' ? 'checked' : ''} aria-label="Mark ${escapeHtml(t.title)} complete">
    <div class="task-info"><div class="task-title">${escapeHtml(t.title)}</div><div class="task-meta"><span>▤ ${escapeHtml(t.course || 'General')}</span><span>◷ ${niceDate(t.due_date)}</span><span>${t.status === 'in_progress' ? 'In progress' : t.status === 'done' ? 'Completed' : 'To do'}</span>${t.notes ? `<span title="${escapeHtml(t.notes)}">Notes added</span>` : ''}</div></div>
    <span class="tag ${t.priority}">${escapeHtml(t.priority)}</span>
    <div class="actions"><button class="icon-btn" data-action="edit" data-id="${t.id}" aria-label="Edit ${escapeHtml(t.title)}">✎</button><button class="icon-btn" data-action="delete" data-id="${t.id}" aria-label="Delete ${escapeHtml(t.title)}">✕</button></div>
  </article>`).join('');
}
function openForm(task = null) {
  editingId = task?.id ?? null;
  $('taskForm').reset();
  $('dialogTitle').textContent = task ? 'Edit task' : 'New task';
  if (task) for (const key of ['title','course','notes','due_date','priority','status']) $('taskForm').elements[key].value = task[key] ?? '';
  $('taskDialog').showModal();
  $('taskForm').elements.title.focus();
}
$('newTask').addEventListener('click', () => openForm());
$('closeDialog').addEventListener('click', () => $('taskDialog').close());
$('cancel').addEventListener('click', () => $('taskDialog').close());
$('taskForm').addEventListener('submit', async e => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.currentTarget));
  data.due_date ||= null;
  const save = $('save');
  save.disabled = true;
  try {
    await api(editingId ? `/api/tasks/${editingId}` : '/api/tasks', {method: editingId ? 'PATCH' : 'POST', body:JSON.stringify(data)});
    $('taskDialog').close();
    await refresh();
  } catch(err) { notify(err.message); alert(err.message); }
  finally { save.disabled = false; }
});
$('tasks').addEventListener('click', async e => {
  const button = e.target.closest('button[data-action]');
  if (!button) return;
  const task = tasks.find(t => t.id === Number(button.dataset.id));
  if (!task) return;
  if (button.dataset.action === 'edit') return openForm(task);
  if (button.dataset.action === 'delete' && confirm(`Delete "${task.title}"?`)) {
    try { await api(`/api/tasks/${task.id}`, {method:'DELETE'}); await refresh(); }
    catch(err) { notify(err.message); }
  }
});
$('tasks').addEventListener('change', async e => {
  if (!e.target.matches('[data-action="toggle"]')) return;
  const id = Number(e.target.dataset.id);
  try { await api(`/api/tasks/${id}`, {method:'PATCH',body:JSON.stringify({status:e.target.checked ? 'done' : 'todo'})}); await refresh(); }
  catch(err) { notify(err.message); await refresh(); }
});
let searchTimer;
$('search').addEventListener('input', () => {clearTimeout(searchTimer); searchTimer = setTimeout(refresh,220);});
for (const id of ['status','priority']) $(id).addEventListener('change', refresh);
refresh();
