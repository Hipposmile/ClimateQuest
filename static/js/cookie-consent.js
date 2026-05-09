// ─────────────────────────────────────────────
// i18n
// ─────────────────────────────────────────────

const translations = {
    de: {
        cookieTitle: "Wir verwenden Cookies,",
        cookieBody: "um die Funktionalität unserer Webseite zu gewährleisten und sie vor Spam und Missbrauch zu schützen.",
        learnMore: "Mehr erfahren",
        ageConfirm: "Durch das Akzeptieren der Cookies bestätigst du, dass du volljährig bist oder dass eine erziehungsberechtigte Person diese Einwilligung erteilt hat.",
        acceptAll: "Alle akzeptieren",
        rejectAll: "Alle ablehnen",
        settings: "Genauere Einstellungen",
        cookieSelection: "Cookie-Auswahl:",
        saveSettings: "Einstellungen speichern",
        showExplanation: "Erklärung anzeigen",
        blockedText: (type) => `Dieses Element ist blockiert. Bitte '${type}'-Cookies erlauben, um es zu sehen. Evtl. musst du die Seite anschließend neu laden.`,
        dialogLabel: "Cookie-Einstellungen",
        resetLabel: "Cookie-Einstellungen anzeigen",
        categories: {
            essential: {
                label: "Essenzielle Cookies",
                explanation: "Unverzichtbar für den Betrieb der Website. Dazu gehört die Verwendung des localStorage."
            },
            recaptcha: {
                label: "reCAPTCHA",
                explanation: "Wird zur Registrierung benötigt."
            }
        }
    },
    en: {
        cookieTitle: "We use cookies",
        cookieBody: "to ensure the websites functionality and to protect it from spam and abuse.",
        learnMore: "Learn more",
        ageConfirm: "By accepting cookies you confirm that you are of legal age, or that a parent or guardian has given their consent.",
        acceptAll: "Accept all",
        rejectAll: "Reject all",
        settings: "More settings",
        cookieSelection: "Cookie selection:",
        saveSettings: "Save settings",
        showExplanation: "Show explanation",
        blockedText: (type) => `This element is blocked. Please allow '${type}' cookies to view it. You may need to reload the page afterwards.`,
        dialogLabel: "Cookie settings",
        resetLabel: "Show cookie settings",
        categories: {
            essential: {
                label: "Essential cookies",
                explanation: "Required for the website to function, including the use of localStorage."
            },
            recaptcha: {
                label: "reCAPTCHA",
                explanation: "Required for registration."
            }
        }
    }
};

function getLang() {
    return document.documentElement.lang?.slice(0, 2) || 'en';
}

function t(key) {
    const lang = getLang();
    return translations[lang]?.[key] ?? translations['en'][key] ?? key;
}

function tCategory(categoryKey, field) {
    const lang = getLang();
    return translations[lang]?.categories?.[categoryKey]?.[field]
        ?? translations['en']?.categories?.[categoryKey]?.[field]
        ?? categoryKey;
}

// ─────────────────────────────────────────────
// Cookie categories
// ─────────────────────────────────────────────

const cookieCategories = {
    essential: {
        get label() {
            return tCategory('essential', 'label');
        },
        get explanation() {
            return tCategory('essential', 'explanation');
        },
        required: true
    },
    recaptcha: {
        get label() {
            return tCategory('recaptcha', 'label');
        },
        get explanation() {
            return tCategory('recaptcha', 'explanation');
        },
        required: false
    }
};

// ─────────────────────────────────────────────
// Banner
// ─────────────────────────────────────────────

function addCookieBanner() {
    const banner = document.createElement('div');
    banner.innerHTML = `
      <div id="cookie-overlay"></div>
      <div role="dialog" aria-label="${t('dialogLabel')}" aria-modal="true" id="cookie-banner">
        <p><strong>${t('cookieTitle')}</strong> ${t('cookieBody')} <a href="https://climate-quest.de/datenschutz/">${t('learnMore')}</a>.</p>
        <p>${t('ageConfirm')}</p>
        <div class="buttons">
          <button id="btn-accept">${t('acceptAll')}</button>
          <button id="btn-reject">${t('rejectAll')}</button>
          <button id="btn-settings">${t('settings')}</button>
        </div>
        <div id="settings-panel">
          <p><strong>${t('cookieSelection')}</strong></p>
          ${Object.entries(cookieCategories).map(([key, {label, explanation, required}]) => `
            <div class="cookie-category">
              <label>
                <input type="checkbox" id="${key}" ${required ? 'disabled checked' : ''}>
                ${label}
              </label>
              <button class="toggle-expl" data-target="${key}-expl">${t('showExplanation')}</button>
              <span class="explanation" id="${key}-expl">${explanation}</span>
            </div>
          `).join('')}
          <button id="btn-save">${t('saveSettings')}</button>
        </div>
      </div>`;
    document.body.appendChild(banner);

    document.getElementById('btn-accept').addEventListener('click', () => {
        const consent = {};
        for (const key in cookieCategories) {
            consent[key] = true;
        }
        setConsent(consent);
        window.location.reload();
    });

    document.getElementById('btn-reject').addEventListener('click', () => {
        const consent = {};
        for (const key in cookieCategories) {
            consent[key] = cookieCategories[key].required;
        }
        setConsent(consent);
        window.location.reload();
    });

    document.getElementById('btn-settings').addEventListener('click', () => {
        const panel = document.getElementById('settings-panel');
        panel.style.display = panel.style.display === 'block' ? 'none' : 'block';
    });

    document.querySelectorAll('.toggle-expl').forEach(btn => {
        btn.addEventListener('click', () => {
            const expl = document.getElementById(btn.dataset.target);
            expl.style.display = expl.style.display === 'block' ? 'none' : 'block';
        });
    });

    document.getElementById('btn-save').addEventListener('click', () => {
        const consent = {};
        for (const key in cookieCategories) {
            consent[key] = cookieCategories[key].required || document.getElementById(key).checked;
        }
        setConsent(consent);
        window.location.reload();
    });
}

// ─────────────────────────────────────────────
// Consent handling
// ─────────────────────────────────────────────

function setConsent(consent) {
    localStorage.setItem('cookieConsent', JSON.stringify(consent));
    ['cookie-banner', 'cookie-overlay'].forEach(id => document.getElementById(id)?.remove());
    document.body.classList.remove('blocked');
    handleCookieBlocks(consent);
}

// 🚫 Blockierte Inhalte je nach Consent anzeigen
function handleCookieBlocks(consentState) {
    document.querySelectorAll('.cookie-blocked').forEach(el => {
        const type = el.dataset.requires;
        const content = el.dataset.content?.trim();

        if (consentState[type]) {
            if (content.startsWith("<script")) {
                // Prüfen, ob es ein externes Skript ist
                const srcMatch = content.match(/<script\s+src=["']([^"']+)["']><\/script>/i);
                if (srcMatch) {
                    const script = document.createElement("script");
                    script.src = srcMatch[1];
                    script.async = true;
                    document.body.appendChild(script);
                    return;
                }

                // Prüfen, ob es ein Inline-Skript ist
                const inlineMatch = content.match(/<script nonce="{{ request.csp_script_nonce }}">([\s\S]*?)<\/script>/i);
                if (inlineMatch) {
                    const script = document.createElement("script");
                    script.textContent = inlineMatch[1];
                    document.body.appendChild(script);
                    return;
                }

                console.warn("Unbekanntes Skriptformat:", content);
            } else if (content.startsWith("<link")) {
                const linkMatch = content.match(/<link\s+[^>]*href=["']([^"']+)["'][^>]*rel=["']stylesheet["'][^>]*>/i);
                if (linkMatch) {
                    const link = document.createElement("link");
                    link.href = linkMatch[1];
                    link.rel = "stylesheet";
                    document.head.appendChild(link);
                    return;
                } else {
                    console.error("Error matching link");
                }
            } else {
                el.innerHTML = content;
            }
        } else {
            const text = el.dataset.text || t('blockedText')(type);
            el.innerHTML = `<div class="cookie-forbidden-div${el.dataset.important === 'true' ? ' important' : ''}">${text}</div>`;
        }
    });
}

// ─────────────────────────────────────────────
// Init
// ─────────────────────────────────────────────

window.addEventListener('load', () => {
    const consent = localStorage.getItem('cookieConsent');
    if (consent) {
        setConsent(JSON.parse(consent));
    } else {
        addCookieBanner();
    }
});

function addResetBtn() {
    const resetBtnDiv = document.createElement('div');
    resetBtnDiv.id = 'cookie-reset-div';
    resetBtnDiv.role = "complementary";
    resetBtnDiv.ariaLabel = t('resetLabel');
    resetBtnDiv.innerHTML = '<button id="cookie-reset" class="emoji">&#x1F36A;</button>';
    const resetBtn = resetBtnDiv.querySelector('#cookie-reset');
    resetBtn.addEventListener('click', () => {
        localStorage.removeItem('cookieConsent');
        addCookieBanner();
    });
    document.body.appendChild(resetBtnDiv);
}

function getCookiePreferences() {
    const consentString = localStorage.getItem('cookieConsent');
    return consentString ? JSON.parse(consentString) : {};
}

document.addEventListener('DOMContentLoaded', () => {
    addResetBtn();
});