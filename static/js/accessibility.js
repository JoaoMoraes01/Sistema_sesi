/*
 * Acessibilidade: tamanho de fonte, alto contraste, fonte para dislexia e
 * espaçamento entre linhas. Tudo salvo no localStorage e reaplicado sozinho
 * quando a página carrega (veja applyAccessibilityPreferences em main.js).
 */

const FONT_SIZES = [14, 16, 18, 20, 22]; // px — índice 1 (16px) é o padrão do navegador

function applyAccessibilityPreferences() {
    const savedIndex = parseInt(localStorage.getItem('a11y_fontSizeIndex'));
    const fontIndex = Number.isInteger(savedIndex) && savedIndex >= 0 && savedIndex < FONT_SIZES.length ? savedIndex : 1;
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
}

function changeFontSize(direction) {
    const current = FONT_SIZES.indexOf(parseInt(document.documentElement.style.fontSize) || 16);
    const currentIndex = current === -1 ? 1 : current;
    const newIndex = Math.min(FONT_SIZES.length - 1, Math.max(0, currentIndex + direction));
    document.documentElement.style.fontSize = `${FONT_SIZES[newIndex]}px`;
    localStorage.setItem('a11y_fontSizeIndex', newIndex);
}

function toggleHighContrast() {
    const isActive = document.body.classList.toggle('high-contrast');
    localStorage.setItem('a11y_highContrast', isActive);
    document.getElementById('highContrastToggle')?.classList.toggle('active', isActive);
}

function toggleDyslexiaFont() {
    const isActive = document.body.classList.toggle('dyslexia-font');
    localStorage.setItem('a11y_dyslexiaFont', isActive);
    document.getElementById('dyslexiaFontToggle')?.classList.toggle('active', isActive);
}

function toggleLineSpacing() {
    const isActive = document.body.classList.toggle('increased-spacing');
    localStorage.setItem('a11y_lineSpacing', isActive);
    document.getElementById('lineSpacingToggle')?.classList.toggle('active', isActive);
}

function resetAccessibility() {
    localStorage.removeItem('a11y_fontSizeIndex');
    localStorage.removeItem('a11y_highContrast');
    localStorage.removeItem('a11y_dyslexiaFont');
    localStorage.removeItem('a11y_lineSpacing');
    document.documentElement.style.fontSize = '';
    document.body.classList.remove('high-contrast', 'dyslexia-font', 'increased-spacing');
    document.getElementById('highContrastToggle')?.classList.remove('active');
    document.getElementById('dyslexiaFontToggle')?.classList.remove('active');
    document.getElementById('lineSpacingToggle')?.classList.remove('active');
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