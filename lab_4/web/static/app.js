// ═══ State ═══
let currentPath = '/';
let cpMvMode = 'cp';   // 'cp' или 'mv'
let cpMvSource = '';

// ═══ Helpers ═══
function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' Б';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' КБ';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' МБ';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' ГБ';
}

function timeNow() {
    return new Date().toLocaleTimeString('ru-RU', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
}

function log(message, ok = true) {
    const body = document.getElementById('logBody');
    const entry = document.createElement('div');
    entry.className = 'log-entry ' + (ok ? 'log-entry--ok' : 'log-entry--err');
    entry.innerHTML = `<span class="log-time">${timeNow()}</span><span>${ok ? '✓' : '✗'} ${message}</span>`;
    body.prepend(entry);
}

async function api(endpoint, data = null) {//функция для отправки запросов на flask сервер
    const opts = data !== null
        ? { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) }
        : { method: 'GET' };
    const res = await fetch('/api/' + endpoint, opts);
    const json = await res.json();
    return json;
}

// ═══ Modals ═══
function showModal(id) {
    document.getElementById(id).classList.add('active');
    const input = document.querySelector('#' + id + ' input, #' + id + ' textarea');
    if (input) setTimeout(() => input.focus(), 100);
}

function hideModal(id) {
    document.getElementById(id).classList.remove('active');
}

// Close modals on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
    }
});

// Close modals on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
    }
});

// ═══ Render ═══
//Рисует кликабельное дерево папок и файлов
//в боковой панели. Клик по треугольнику — раскрыть/свернуть
//папку. Клик по имени папки — перейти в неё.
//Клик по файлу — открыть просмотр.
//Вложенные папки отрисовываются рекурсивно с увеличивающимся отступом.
function renderTree(items, container, level = 0) {
    container.innerHTML = '';
    items.forEach(item => {
        if (item.is_folder) {
            const div = document.createElement('div');

            const row = document.createElement('div');
            row.className = 'tree-item';
            row.style.paddingLeft = (12 + level * 16) + 'px';

            const toggle = document.createElement('span');
            toggle.className = 'tree-toggle';
            toggle.textContent = '▶';

            const icon = document.createElement('span');
            icon.className = 'tree-icon';
            icon.textContent = '📁';

            const name = document.createElement('span');
            name.className = 'tree-name';
            name.textContent = item.name;

            row.appendChild(toggle);
            row.appendChild(icon);
            row.appendChild(name);

            const children = document.createElement('div');//контейнер для детей папки изначально скрыт
            children.className = 'tree-children';
            children.style.display = 'none';

            row.addEventListener('click', (e) => {
                e.stopPropagation();
                if (e.target === toggle) {
                    const open = children.style.display !== 'none';
                    children.style.display = open ? 'none' : 'block';
                    toggle.textContent = open ? '▶' : '▼';
                } else {
                    cdTo(item.path);
                }
            });

            if (item.children && item.children.length > 0) {
                renderTree(item.children, children, level + 1);
            }

            div.appendChild(row);
            div.appendChild(children);
            container.appendChild(div);
        } else {
            const row = document.createElement('div');
            row.className = 'tree-item';
            row.style.paddingLeft = (12 + level * 16 + 22) + 'px';
            row.innerHTML = `<span class="tree-icon">📄</span><span class="tree-name">${item.name}</span>`;
            row.addEventListener('click', () => openCat(item.name));
            container.appendChild(row);
        }
    });
}

function renderTable(entries) {
    const tbody = document.getElementById('fileTableBody');
    const empty = document.getElementById('emptyState');

    if (entries.length === 0) {
        tbody.innerHTML = '';
        empty.style.display = 'block';
        return;
    }
    empty.style.display = 'none';

    tbody.innerHTML = entries.map(e => `
        <tr>
            <td>${e.is_folder ? '📁' : '📄'}</td>
            <td>
                <span class="file-name" onclick="${e.is_folder ? `cdTo('${e.name}')` : `openCat('${e.name}')`}">
                    ${e.name}
                </span>
            </td>
            <td class="file-size">${formatSize(e.size)}</td>
            <td>${e.format || '—'}</td>
            <td class="file-perm" title="${e.perm_numeric}">${e.permissions}</td>
            <td>${e.owner}</td>
            <td>${e.modified}</td>
            <td class="file-actions">
                ${!e.is_folder ? `
                    <button class="btn btn--small" onclick="openWrite('${e.name}')" title="Записать">✏️</button>
                    <button class="btn btn--small" onclick="openCat('${e.name}')" title="Просмотр">👁</button>
                ` : ''}
                <button class="btn btn--small" onclick="openCpMv('cp','${e.name}')" title="Копировать">📋</button>
                <button class="btn btn--small" onclick="openCpMv('mv','${e.name}')" title="Переместить">✂️</button>
                <button class="btn btn--small" onclick="openChmod('${e.name}')" title="Права">🔐</button>
                <button class="btn btn--small" onclick="openChown('${e.name}')" title="Владелец">👤</button>
                ${e.format === 'ZIP' ? `<button class="btn btn--small" onclick="openExtract('${e.name}')" title="Распаковать">📦</button>` : ''}
                <button class="btn btn--small btn--danger" onclick="doRm('${e.name}', ${e.is_folder})" title="Удалить">🗑</button>
            </td>
        </tr>
    `).join('');
}

// ═══ Load State ═══ вызывается при загрузке и после каждой операции(обновление всей страницы)
async function loadState() {
    const data = await api('state');
    currentPath = data.current_path;
    document.getElementById('currentPath').textContent = data.current_path;
    document.getElementById('currentUser').textContent = data.current_user;

    if (data.disk) {
        document.getElementById('diskInfo').textContent = data.disk.name + ' (' + data.disk.filesystem + ')';
        document.getElementById('diskUsed').textContent = formatSize(data.disk.used);
        document.getElementById('diskTotal').textContent = formatSize(data.disk.total);
        const pct = (data.disk.used / data.disk.total * 100).toFixed(1);
        document.getElementById('diskFill').style.width = pct + '%';
    }

    renderTable(data.entries);
    renderTree(data.tree, document.getElementById('treeView'));
}

// ═══ Navigation ═══
async function cdTo(path) {
    const res = await api('cd', { path });
    if (res.status === 'ok') {
        log(`cd ${path}`);
        loadState();
    } else {
        log(res.message, false);
    }
}

// ═══ File Operations ═══
async function doTouch() {
    const name = document.getElementById('touchName').value.trim();
    if (!name) return;
    const res = await api('touch', { name });
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') {
        hideModal('touchModal');
        document.getElementById('touchName').value = '';
        loadState();
    }
}

async function doMkdir() {
    const name = document.getElementById('mkdirName').value.trim();
    if (!name) return;
    const res = await api('mkdir', { name });
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') {
        hideModal('mkdirModal');
        document.getElementById('mkdirName').value = '';
        loadState();
    }
}

function openWrite(name) {
    document.getElementById('writeFileName').textContent = name;
    document.getElementById('writeContent').value = '';
    document.getElementById('writeContent').dataset.path = name;
    showModal('writeModal');
}

async function doWrite() {
    const path = document.getElementById('writeContent').dataset.path;
    const content = document.getElementById('writeContent').value;
    const res = await api('write', { path, content });
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') {
        hideModal('writeModal');
        loadState();
    }
}

async function openCat(name) {
    const res = await api('cat', { path: name });
    if (res.status === 'ok') {
        document.getElementById('catFileName').textContent = name;
        document.getElementById('catContent').textContent = res.content;
        showModal('catModal');
    } else {
        log(res.message, false);
    }
}

function openCpMv(mode, name) {
    cpMvMode = mode;
    cpMvSource = name;
    document.getElementById('cpMvTitle').textContent = mode === 'cp' ? 'Копировать' : 'Переместить';
    document.getElementById('cpMvSrc').textContent = name;
    document.getElementById('cpMvDst').value = '';
    document.getElementById('cpMvBtn').textContent = mode === 'cp' ? 'Копировать' : 'Переместить';
    showModal('cpMvModal');
}

async function doCpMv() {
    const dst = document.getElementById('cpMvDst').value.trim();
    if (!dst) return;
    const res = await api(cpMvMode, { src: cpMvSource, dst });
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') {
        hideModal('cpMvModal');
        loadState();
    }
}

async function doRm(name, isFolder) {
    const msg = isFolder
        ? `Удалить папку "${name}" рекурсивно?`
        : `Удалить "${name}"?`;
    if (!confirm(msg)) return;
    const res = await api('rm', { path: name, recursive: isFolder });
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') loadState();
}

// ═══ Permissions ═══
function openChmod(name) {
    document.getElementById('chmodPath').textContent = name;
    document.getElementById('chmodMode').value = '';
    document.getElementById('chmodMode').dataset.path = name;
    showModal('chmodModal');
}

async function doChmod() {
    const path = document.getElementById('chmodMode').dataset.path;
    const mode = document.getElementById('chmodMode').value.trim();
    if (!mode) return;
    const res = await api('chmod', { path, mode });
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') {
        hideModal('chmodModal');
        loadState();
    }
}

function openChown(name) {
    document.getElementById('chownPath').textContent = name;
    document.getElementById('chownOwner').value = '';
    document.getElementById('chownOwner').dataset.path = name;
    showModal('chownModal');
}

async function doChown() {
    const path = document.getElementById('chownOwner').dataset.path;
    const owner = document.getElementById('chownOwner').value.trim();
    if (!owner) return;
    const res = await api('chown', { path, owner });
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') {
        hideModal('chownModal');
        loadState();
    }
}

// ═══ Archive ═══
async function doArchive() {
    const name = document.getElementById('archiveName').value.trim();
    const srcStr = document.getElementById('archiveSources').value.trim();
    if (!name || !srcStr) return;
    const sources = srcStr.split(/\s+/);
    const res = await api('archive', { name, sources });
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') {
        hideModal('archiveModal');
        document.getElementById('archiveName').value = '';
        document.getElementById('archiveSources').value = '';
        loadState();
    }
}

function openExtract(name) {
    document.getElementById('extractName').textContent = name;
    document.getElementById('extractDest').value = '';
    document.getElementById('extractDest').dataset.path = name;
    showModal('extractModal');
}

async function doExtract() {
    const path = document.getElementById('extractDest').dataset.path;
    const dest = document.getElementById('extractDest').value.trim() || '.';
    const res = await api('extract', { path, destination: dest });
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') {
        hideModal('extractModal');
        loadState();
    }
}

// ═══ Backup / Restore ═══
async function doBackup() {
    const res = await api('backup', {});
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') loadState();
}

function doRestore() {
    showModal('restoreModal');
}

async function doRestoreConfirm() {
    const name = document.getElementById('restoreName').value.trim();
    if (!name) return;
    const res = await api('restore', { name });
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') {
        hideModal('restoreModal');
        loadState();
    }
}

// Fix: wire the restore button properly
document.addEventListener('DOMContentLoaded', () => {
    // Override the restore modal button
    const restoreBtn = document.querySelector('#restoreModal .btn--primary');
    if (restoreBtn) {
        restoreBtn.onclick = doRestoreConfirm;
    }
});

// ═══ Organize ═══
async function doOrganize() {
    const res = await api('organize', { path: '.' });
    log(res.message, res.status === 'ok');
    if (res.status === 'ok') loadState();
}

// ═══ Enter key in modals ═══
document.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    const active = document.querySelector('.modal-overlay.active');
    if (!active) return;
    const btn = active.querySelector('.btn--primary');
    if (btn) btn.click();
});

// ═══ Init ═══
loadState();
