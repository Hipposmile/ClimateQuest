// 🧠 Konfiguration: Cookie-Kategorien und ihre Erklärungen
const cookieCategories = {
    essential: {
        label: "Essenzielle Cookies",
        explanation: "Unverzichtbar für den Betrieb der Website.",
        required: true
    },
    analytics: {
        label: "Analytics",
        explanation: "Hilft uns, die Website zu verbessern.",
        required: false
    },
    marketing: {
        label: "Marketing",
        explanation: "Erlaubt z.B. die Anzeige von YouTube-Videos.",
        required: false
    },
    recaptcha: {
        label: "reCAPTCHA",
        explanation: "Wird zur Registrierung benötigt.",
        required: false
    },
    translate: {
        label: "translate",
        explanation: "Wird zur Übersetzung benötigt.",
        required: false
    },
    quill: {
        label: "Quill",
        explanation: "Hiermit kannst du manche Text-Inputs schöner stylen, z.B. fett, kursiv, unterstrichen oder mit Links.",
        required: false
    }
};

// 🎨 Styles dynamisch einfügen
const styleCookie = document.createElement('style');
styleCookie.textContent = `:root {
        --color-bg: #f4f6f8;
        --color-text: #333;
        --color-primary: #3498db;
        --color-primary-hover: #2980b9;
        --color-accent: #ff00a2;
        --color-white: #ffffff;
        --color-shadow-light: rgba(0, 0, 0, 0.06);
        --color-shadow-hover: rgba(0, 0, 0, 0.1);
        --color-success: #2ecc71;
        --color-muted: #888;
    }
    #cookie-overlay {
        position: fixed; inset: 0;
        background: var(--color-shadow-light);
        z-index: 9998;
        animation: fadeIn 0.3s ease-in-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; } to { opacity: 1; }
    }

    #cookie-banner {
        position: fixed; bottom: 2%; left: 50%;
        transform: translateX(-50%);
        width: 90%; 
        max-width: 520px;
        background: var(--color-white);
        color: var(--color-text);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 8px 24px var(--color-shadow-light);
        font-family: 'Segoe UI', sans-serif;
        z-index: 9999;
        max-height: 500px; /* Höhe des Divs, um Scrollen zu ermöglichen */
        overflow-y: auto;
    }

    #cookie-banner a {
        color: var(--color-primary);
        text-decoration: none;
    }
    #cookie-banner a:hover {
        color: var(--color-primary-hover);
        text-decoration: underline;
    }

    #cookie-banner button {
        margin: 6px;
        padding: 10px 18px;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
        background: var(--color-primary);
        color: var(--color-white);
        cursor: pointer;
        transition: background 0.2s ease;
    }

    #cookie-banner button:hover {
        background-color: var(--color-primary-hover);
    }

    #settings-panel {
        display: none;
        background: var(--color-bg);
        padding: 16px;
        border-radius: 8px;
        margin-top: 16px;
    }

    .cookie-category {
        margin-bottom: 14px;
    }

    .cookie-category label {
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--color-text);
    }

    .cookie-category input[type="checkbox"] {
        accent-color: var(--color-primary);
        width: 18px; height: 18px;
        cursor: pointer;
    }

    .toggle-expl {
        background: transparent;
        border: 1px solid var(--color-primary);
        color: var(--color-primary);
        border-radius: 6px;
        font-size: 0.85em;
        padding: 4px 8px;
        margin-top: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .toggle-expl:hover {
        background: var(--color-primary);
        color: var(--color-white);
    }

    .explanation {
        display: none;
        font-size: 0.85em;
        color: var(--color-muted);
        margin-top: 4px;
    }

    #btn-save {
        background-color: var(--color-success);
    }

    #cookie-reset {
        position: fixed; bottom: 20px; left: 20px;
        padding: 10px 16px;
        background-color: var(--color-accent);
        color: var(--color-white);
        border: none;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        z-index: 99;
        box-shadow: 0 4px 12px var(--color-shadow-light);
    }
    
    #cookie-reset:hover {
        background-color: var(--color-accent);
    }

    body.blocked {
  overflow: hidden;
  background-color: #868484ff; /* Optional: dunkler Hintergrund */
}

/* Overlay als Schleier */
#cookie-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4); /* ← Rauchiger Schleier */
  z-index: 9998;
  animation: fadeIn 0.3s ease-in-out;
  pointer-events: auto; /* ← wichtig: erlaubt Interaktion mit dem Banner */
}
  

/* Banner bleibt interaktiv */
#cookie-banner {
  z-index: 9999; /* ← über dem Overlay */
}

#cookie-reset:hover {
  background-color: var(--color-accent); /* Fix: fehlender Wert */
}`;
document.head.appendChild(styleCookie);

// 🧱 HTML-Struktur erzeugen
const banner = document.createElement('div');
banner.innerHTML = `<div id="cookie-overlay"></div>
  <div id="cookie-banner">
    <p><strong>Wir verwenden Cookies</strong> für Funktion, Analyse und Marketing. <a href="https://climate-quest.de/static/rechtliches/Datenschutz.pdf">Mehr erfahren</a>.</p>
    <p><strong>Nach Änderung der Cookie-Einstellungen Seite bitte neu laden!</strong></p>
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
          ${!required ? `
            <button class="toggle-expl" data-target="${key}-expl">Erklärung anzeigen</button>
            <span class="explanation" id="${key}-expl">${explanation}</span>
          ` : `<span class="explanation">${explanation}</span>`}
        </div>
      `).join('')}
      <button id="btn-save">Einstellungen speichern</button>
    </div>
  </div>`;
document.body.appendChild(banner);

// document.body.classList.add('blocked');

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

// 💾 Consent speichern und Banner entfernen
function setConsent(consent) {
    localStorage.setItem('cookieConsent', JSON.stringify(consent));
    ['cookie-banner', 'cookie-overlay'].forEach(id => document.getElementById(id)?.remove());
    document.body.classList.remove('blocked');
    handleCookieBlocks(consent);
}

function handleCookieBlocks(consentState) {
    document.querySelectorAll('.cookie-blocked').forEach(el => {
        const type = el.dataset.requires;
        const content = el.dataset.content?.trim();

        if (consentState[type]) {
            console.log(content);

            // 🔍 <script> extern
            const scriptSrcMatch = content.match(/<script\s+src=["']([^"']+)["']><\/script>/i);
            if (scriptSrcMatch) {
                const script = document.createElement("script");
                script.src = scriptSrcMatch[1];
                script.async = true;
                document.body.appendChild(script);
                return;
            }

            // 🔍 <script> inline
            const inlineScriptMatch = content.match(/<script>([\s\S]*?)<\/script>/i);
            if (inlineScriptMatch) {
                const script = document.createElement("script");
                script.textContent = inlineScriptMatch[1];
                document.body.appendChild(script);
                return;
            }

            // 🔍 <link> Stylesheet
            const linkMatch = content.match(/<link\s+[^>]*href=["']([^"']+)["'][^>]*rel=["']stylesheet["'][^>]*>/i);
            if (linkMatch) {
                const link = document.createElement("link");
                link.href = linkMatch[1];
                link.rel = "stylesheet";
                document.head.appendChild(link);
                return;
            }

            // 🧼 Fallback: HTML direkt einfügen
            el.innerHTML = content;
        } else {
            el.innerHTML = `<div style="background:#ccc; padding:15px; border-radius:8px; margin: 15px;">
        Dieses Element ist blockiert. Bitte '${type}'-Cookies erlauben, um es zu sehen. Evtl. musst du die Seite anschließend neu laden.
      </div>`;
        }
    });
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
                    console.log(content);
                    const script = document.createElement("script");
                    script.src = srcMatch[1];
                    script.async = true; // optional, je nach Bedarf
                    document.body.appendChild(script);
                    return;
                }

                // Prüfen, ob es ein Inline-Skript ist
                const inlineMatch = content.match(/<script>([\s\S]*?)<\/script>/i);
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
            el.innerHTML = `<div style="background:#ccc; padding:15px; border-radius:8px; margin: 15px;">
          Dieses Element ist blockiert. Bitte '${type}'-Cookies erlauben, um es zu sehen. Evtl. musst du die Seite anschließend neu laden.
        </div>`;
        }
    });
}


// 🔄 Consent beim Laden prüfen
window.addEventListener('load', () => {
    const consent = localStorage.getItem('cookieConsent');
    if (consent) setConsent(JSON.parse(consent));
});

// 🔁 Reset-Button zum Zurücksetzen
const resetBtn = document.createElement('button');
resetBtn.id = 'cookie-reset';
resetBtn.innerHTML = '&#x1F36A;';
resetBtn.addEventListener('click', () => {
    localStorage.removeItem('cookieConsent');
    location.reload();
});
document.body.appendChild(resetBtn);

function getCookiePreferences() {
    const consentString = localStorage.getItem('cookieConsent');
    return consentString ? JSON.parse(consentString) : {};
}