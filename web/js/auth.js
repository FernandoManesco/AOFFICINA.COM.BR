// aOfficina — sessão, proteção de página, utilitários de formatação.
function salvarSessao(r) {
  localStorage.setItem('token', r.token);
  localStorage.setItem('nome', r.nome);
  localStorage.setItem('nivel', String(r.nivel));
  localStorage.setItem('oficina_id', r.oficina_id == null ? '' : String(r.oficina_id));
  localStorage.setItem('primeiro_acesso', r.primeiro_acesso ? '1' : '0');
}
function _claims() {
  const t = localStorage.getItem('token');
  if (!t) return null;
  try { return JSON.parse(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))); } catch (_) { return null; }
}
function protegerPagina() {
  const c = _claims();
  if (!c || (c.exp && c.exp * 1000 < Date.now())) { localStorage.removeItem('token'); location.href = '/index.html'; return false; }
  return true;
}
function exigirNivel(n) {
  if (getNivel() > n) { mostrarAlerta('Sem permissão para esta tela', 'warning'); setTimeout(() => location.href = '/pages/dashboard.html', 1200); return false; }
  return true;
}
function getNivel() { return parseInt(localStorage.getItem('nivel') || '99', 10); }
function getNome() { return localStorage.getItem('nome') || ''; }
function getOficinaId() { const v = localStorage.getItem('oficina_id'); return v ? parseInt(v, 10) : null; }
function logout() { localStorage.clear(); location.href = '/index.html'; }

// ---- formatação ----
function formatarMoeda(cent) { return (Number(cent || 0) / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }); }
function paraCentavos(txt) { const n = parseFloat(String(txt || '0').replace(/\./g, '').replace(',', '.')); return Math.round((isNaN(n) ? 0 : n) * 100); }
function formatarData(iso) { if (!iso) return ''; const d = new Date(iso); return isNaN(d) ? String(iso) : d.toLocaleDateString('pt-BR'); }
function formatarDataHora(iso) { if (!iso) return ''; const d = new Date(iso); return isNaN(d) ? String(iso) : d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }); }
function formatarPlaca(p) { if (!p) return ''; p = p.toUpperCase(); return p.length === 7 ? p.slice(0, 3) + '-' + p.slice(3) : p; }
function formatarDoc(d) {
  if (!d) return '';
  if (d.length === 11) return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  if (d.length === 14) return d.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
  return d;
}
function formatarFone(f) { if (!f) return ''; const d = f.replace(/\D/g, ''); return d.length === 11 ? d.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3') : d.length === 10 ? d.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3') : f; }
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }

// ---- toast ----
function mostrarAlerta(msg, tipo = 'success') {
  let c = document.querySelector('.toast-container');
  if (!c) { c = document.createElement('div'); c.className = 'toast-container position-fixed top-0 end-0 p-3'; document.body.appendChild(c); }
  const el = document.createElement('div');
  el.className = 'toast align-items-center text-bg-' + tipo + ' border-0';
  el.setAttribute('role', 'alert');
  el.innerHTML = '<div class="d-flex"><div class="toast-body"></div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';
  el.querySelector('.toast-body').textContent = msg;
  c.appendChild(el);
  const t = new bootstrap.Toast(el, { delay: tipo === 'danger' ? 6000 : 3000 });
  t.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}
