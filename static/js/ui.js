/*
 * Notificações visuais: toast de canto, modal de confirmação e o banner
 * grande de sucesso. Não dependem de nenhum outro módulo (só do DOM).
 */

// === SISTEMA DE NOTIFICAÇÕES (substitui alert()) ===
// Usa o #toastBox e as classes .toast/.toast.error/.toast.warning que já existem no style.css
function showToast(message, type = 'success') {
    const box = document.getElementById('toastBox');
    if (!box) { console.warn(message); return; }

    const toast = document.createElement('div');
    toast.className = `toast ${type === 'success' ? '' : type}`.trim();
    toast.textContent = message;
    box.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(30px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Modal de confirmação simples (substitui confirm()), reaproveitando o padrão visual dos cards
function showConfirm(message) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:100001;';
        overlay.innerHTML = `
            <div class="card" style="max-width:420px;width:90%;text-align:center;">
                <p style="color:var(--text-color);margin-bottom:25px;font-weight:600;">${message}</p>
                <div style="display:flex;gap:15px;justify-content:center;">
                    <button id="confirmYes" class="btn-danger">Confirmar</button>
                    <button id="confirmNo" style="background-color:#64748b;">Cancelar</button>
                </div>
            </div>`;
        document.body.appendChild(overlay);
        overlay.querySelector('#confirmYes').onclick = () => { overlay.remove(); resolve(true); };
        overlay.querySelector('#confirmNo').onclick = () => { overlay.remove(); resolve(false); };
    });
}

// --- BANNER DE SUCESSO (grande e centralizado, exibido após ações importantes) ---

let successBannerTimer = null;

function showSuccessBanner(message, title = 'Sucesso!', durationMs = 6000) {
    const titleEl = document.getElementById('successBannerTitle');
    if (titleEl) titleEl.textContent = title;

    const textEl = document.getElementById('successBannerText');
    if (textEl) textEl.textContent = message;

    document.getElementById('successBanner')?.classList.add('open');

    clearTimeout(successBannerTimer);
    successBannerTimer = setTimeout(closeSuccessBanner, durationMs);
}

function closeSuccessBanner() {
    document.getElementById('successBanner')?.classList.remove('open');
    clearTimeout(successBannerTimer);
}

export { showToast, showConfirm, showSuccessBanner, closeSuccessBanner };