// aOfficina — navbar, sidebar e rodapé padrão. Uso: <body data-pagina="clientes"> + montarLayout()
const MENU = [
  { grupo: 'Operação' },
  { id: 'dashboard', href: '/pages/dashboard.html', icone: 'bi-speedometer2', rotulo: 'Painel', nivel: 4 },
  { id: 'agenda', href: '/pages/agenda.html', icone: 'bi-calendar-week', rotulo: 'Agenda', nivel: 3 },
  { id: 'pedidos', href: '/pages/pedidos.html', icone: 'bi-clipboard2-check', rotulo: 'Orçamentos e Pedidos', nivel: 3 },
  { grupo: 'Cadastros' },
  { id: 'clientes', href: '/pages/clientes.html', icone: 'bi-people', rotulo: 'Clientes e Veículos', nivel: 3 },
  { id: 'pecas', href: '/pages/pecas.html', icone: 'bi-gear-wide-connected', rotulo: 'Peças', nivel: 3 },
  { id: 'servicos', href: '/pages/servicos.html', icone: 'bi-tools', rotulo: 'Mão de obra', nivel: 3 },
  { grupo: 'Configuração' },
  { id: 'oficinas', href: '/pages/oficinas.html', icone: 'bi-shop', rotulo: 'Oficinas e Recursos', nivel: 1 },
  { id: 'empresa', href: '/pages/empresa.html', icone: 'bi-building', rotulo: 'Empresa', nivel: 0 },
];

function montarLayout() {
  if (!protegerPagina()) return;
  const pagina = document.body.dataset.pagina || '';
  const nivel = getNivel();
  const nav = document.createElement('nav');
  nav.className = 'navbar navbar-expand navbar-dark navbar-ao px-3';
  nav.innerHTML = `
    <a class="navbar-brand d-flex align-items-center" href="/pages/dashboard.html"><img src="/img/aofficina-cobre.png" alt="aOfficina"></a>
    <button class="btn btn-sm btn-outline-light d-md-none me-2" id="btnMenu"><i class="bi bi-list"></i></button>
    <div class="ms-auto d-flex align-items-center gap-3">
      <span class="badge badge-oficina rounded-pill px-3 py-2" id="badgeUsuario"></span>
      <a class="nav-link" href="#" onclick="logout();return false;" title="Sair"><i class="bi bi-box-arrow-right"></i></a>
    </div>`;
  nav.querySelector('#badgeUsuario').textContent = getNome();

  const side = document.createElement('nav');
  side.className = 'sidebar-ao col-md-3 col-lg-2 d-none d-md-block';
  side.id = 'sidebar';
  side.innerHTML = MENU.filter(m => m.grupo || nivel <= m.nivel).map(m => m.grupo
    ? `<div class="titulo-grupo">${m.grupo}</div>`
    : `<a class="nav-link d-block ${m.id === pagina ? 'active' : ''}" href="${m.href}"><i class="bi ${m.icone}"></i> ${m.rotulo}</a>`).join('');

  const foot = document.createElement('footer');
  foot.className = 'footer-ia py-2 px-3 d-flex align-items-center gap-2 justify-content-center mt-auto';
  foot.innerHTML = `<img src="/img/iaprocess-badge.png" alt="IA Process Automation">
    <span>Desenvolvido por <span class="marca">IA PROCESS AUTOMATION</span> · Fernando Manesco · aOfficina v0.4.1</span>`;

  const main = document.getElementById('conteudo');
  const wrap = document.createElement('div');
  wrap.className = 'container-fluid';
  const row = document.createElement('div');
  row.className = 'row';
  main.parentNode.insertBefore(wrap, main);
  row.appendChild(side);
  main.className = 'col-md-9 col-lg-10 p-3 p-lg-4';
  row.appendChild(main);
  wrap.appendChild(row);
  document.body.prepend(nav);
  document.body.appendChild(foot);
  document.body.classList.add('d-flex', 'flex-column', 'min-vh-100');
  nav.querySelector('#btnMenu').onclick = () => side.classList.toggle('d-none');

  if (localStorage.getItem('primeiro_acesso') === '1' && pagina !== 'senha') {
    mostrarAlerta('Primeiro acesso: troque sua senha.', 'warning');
  }
}
