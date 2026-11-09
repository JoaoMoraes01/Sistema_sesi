/*
 * Acessibilidade: tamanho de fonte, alto contraste, fonte para dislexia e
 * espaçamento entre linhas. Tudo salvo no localStorage e reaplicado sozinho
 * quando a página carrega (veja applyAccessibilityPreferences em main.js).
 *
 * IMPORTANTE — performance:
 * Antes, o CSS tinha `transition` no seletor universal (*), então cada
 * toggle de acessibilidade disparava MILHARES de animações simultâneas
 * (uma por célula de tabela, botão, input). A tabela com 300 alunos × 8
 * células = 2.400 animações concorrentes → travamento visível de 1-2s.
 *
 * A correção tem duas partes:
 * 1) CSS: `transition` foi movido para elementos específicos (não `*`).
 * 2) Aqui: cada toggle envolve a mudança com `withInstantTransition`,
 *    que liga a classe `no-transitions` (transition: none !important em
 *    tudo) ANTES da mudança, força um reflow, e só remove a classe
 *    depois que o browser já pintou o novo estado. Resultado: a troca
 *    é instantânea, sem animação empilhada sobre o reflow.
 */

const FONT_SIZES = [14, 16, 18, 20, 22]; // px — índice 1 (16px) é o padrão do navegador

/**
 * Executa `fn` com TODAS as transições desligadas, e reativa depois que
 * o browser já pintou o novo estado.
 *
 * `void document.body.offsetHeight` força um reflow síncrono: garante
 * que o browser registre o `no-transitions` ANTES de aplicar as novas
 * cores/tamanhos. O duplo `requestAnimationFrame` garante que o paint
 * aconteça antes da reativação (senão o browser poderia batch e animar).
 */
function withInstantTransition(fn) {
    document.body.classList.add('no-transitions');
    // Força reflow síncrono — sem isto, o browser pode coalescer as mudanças
    // e acabar animando mesmo com a classe no-transitions aplicada.
    void document.body.offsetHeight;
    try {
        fn();
    } finally {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                document.body.classList.remove('no-transitions');
            });
        });
    }
}

function applyAccessibilityPreferences() {
    const savedIndex = parseInt(localStorage.getItem('a11y_fontSizeIndex'));
    const fontIndex = Number.isInteger(savedIndex) && savedIndex >= 0 && savedIndex < FONT_SIZES.length ? savedIndex : 1;

    // Aplica todas as preferências salvas de uma vez, sem transições.
    withInstantTransition(() => {
        document.documentElement.style.fontSize = `${FONT_SIZES[fontIndex]}px`;

        const highContrast = localStorage.getItem('a11y_highContrast') === 'true';
        document.body.classList.toggle('high-contrast', highContrast);
        document.getElementById('highContrastToggle')?.classList.toggle('active', highContrast);

        const dyslexiaFont = localStorage.getItem('a11y_dyslexiaFont') === 'true';
        document.body.classList.toggle('dyslexia-font', dyslexiaFont);
        document.getElementById('dyslexiaFontToggle')?.classList.toggle('active', dyslexiaFont);

        const lineSpacing = localStorage.getItem('a11y_lineSpacing') === 'true';
        document.body.classList.toggle('increased-spacing', lineSpacing);
        document.getElementById('lineSpacingToggle')?.classList.toggle('active', lineSpacing);
    });
}

function changeFontSize(direction) {
    withInstantTransition(() => {
        const current = FONT_SIZES.indexOf(parseInt(document.documentElement.style.fontSize) || 16);
        const currentIndex = current === -1 ? 1 : current;
        const newIndex = Math.min(FONT_SIZES.length - 1, Math.max(0, currentIndex + direction));
        document.documentElement.style.fontSize = `${FONT_SIZES[newIndex]}px`;
        localStorage.setItem('a11y_fontSizeIndex', newIndex);
    });
}

function toggleHighContrast() {
    withInstantTransition(() => {
        const isActive = document.body.classList.toggle('high-contrast');
        localStorage.setItem('a11y_highContrast', isActive);
        document.getElementById('highContrastToggle')?.classList.toggle('active', isActive);
    });
}

function toggleDyslexiaFont() {
    withInstantTransition(() => {
        const isActive = document.body.classList.toggle('dyslexia-font');
        localStorage.setItem('a11y_dyslexiaFont', isActive);
        document.getElementById('dyslexiaFontToggle')?.classList.toggle('active', isActive);
    });
}

function toggleLineSpacing() {
    withInstantTransition(() => {
        const isActive = document.body.classList.toggle('increased-spacing');
        localStorage.setItem('a11y_lineSpacing', isActive);
        document.getElementById('lineSpacingToggle')?.classList.toggle('active', isActive);
    });
}

function resetAccessibility() {
    withInstantTransition(() => {
        localStorage.removeItem('a11y_fontSizeIndex');
        localStorage.removeItem('a11y_highContrast');
        localStorage.removeItem('a11y_dyslexiaFont');
        localStorage.removeItem('a11y_lineSpacing');
        document.documentElement.style.fontSize = '';
        document.body.classList.remove('high-contrast', 'dyslexia-font', 'increased-spacing');
        document.getElementById('highContrastToggle')?.classList.remove('active');
        document.getElementById('dyslexiaFontToggle')?.classList.remove('active');
        document.getElementById('lineSpacingToggle')?.classList.remove('active');
    });
}

function toggleAccessibilityPanel() {
    document.getElementById('accessibilityPanel')?.classList.toggle('open');
}

export {
    applyAccessibilityPreferences,
    changeFontSize,
    toggleHighContrast,
    toggleDyslexiaFont,
    toggleLineSpacing,
    resetAccessibility,
    toggleAccessibilityPanel,
};
