// 🧠 Konfiguration: Cookie-Kategorien und ihre Erklärungen
const cookieCategories = {
    essential: {
        label: "Essenzielle Cookies",
        explanation: "Unverzichtbar für den Betrieb der Website. Dazu gehört die Verwendung des localStorage.",
        required: true
    },
    recaptcha: {
        label: "reCAPTCHA",
        explanation: "Wird zur Registrierung benötigt.",
        required: false
    },
    quill: {
        label: "Quill",
        explanation: "Hiermit kannst du manche Text-Inputs schöner stylen, z.B. fett, kursiv, unterstrichen oder mit Links.",
        required: false
    }
};

function addCookieBanner() {
    const banner = document.createElement('div');
    banner.innerHTML = `<div id="cookie-overlay"></div>
      <div role="dialog" aria-label="Cookie-Einstellungen" aria-modal="true" id="cookie-banner">
        <p><strong>Wir verwenden Cookies</strong> für Funktion, Analyse und Marketing. <a href="../rechtliches/Datenschutz.pdf">Mehr erfahren</a>.</p>
        <p>Durch das Akzeptieren der Cookies bestätigst du, dass du volljährig bist oder dass eine erziehungsberechtigte Person diese Einwilligung erteilt hat.</p>
        <div class="buttons">
          <button id="btn-accept">Alle akzeptieren</button>
          <button id="btn-reject">Alle ablehnen</button>
          <button id="btn-settings">Genauere Einstellungen</button>
        </div>
        <div id="settings-panel">
          <p><strong>Cookie-Auswahl:</strong></p>
          ${Object.entries(cookieCategories).map(([key, {label, explanation, required}]) => `
            <div class="cookie-category">
              <label>
                <input type="checkbox" id="${key}" ${required ? 'disabled checked' : ''}>
                ${label}
              </label>
                <button class="toggle-expl" data-target="${key}-expl">Erklärung anzeigen</button>
                <span class="explanation" id="${key}-expl">${explanation}</span>
            </div>
          `).join('')}
          <button id="btn-save">Einstellungen speichern</button>
        </div>
      </div>`;
    document.body.appendChild(banner);

// 🧩 Eventhandler definieren
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

// 💾 Consent speichern und Banner entfernen
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
                    script.async = true; // optional, je nach Bedarf
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

                // Fallback: falls kein Match
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
                    console.error("Error matching link")
                }
            } else {
                el.innerHTML = content;
            }
        } else {
            el.innerHTML = `<div class="cookie-forbidden-div">
          Dieses Element ist blockiert. Bitte '${type}'-Cookies erlauben, um es zu sehen. Evtl. musst du die Seite anschließend neu laden.
        </div>`;
        }
    });
}


// 🔄 Consent beim Laden prüfen
window.addEventListener('load', () => {
    const consent = localStorage.getItem('cookieConsent');
    if (consent) {
        setConsent(JSON.parse(consent))
    } else {
        addCookieBanner();
    }
});

function addResetBtn() {
    // 🔁 Reset-Button zum Zurücksetzen
    const resetBtnDiv = document.createElement('div');
    resetBtnDiv.id = 'cookie-reset-div';
    resetBtnDiv.role = "complementary";
    resetBtnDiv.ariaLabel = 'Cookie-Einstellungen anzeigen';
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