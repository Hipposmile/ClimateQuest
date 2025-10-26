function initGoogleTranslate() {
    if (!localStorage.getItem('translateEnabled')) {
        const consent = confirm('This will enable Google Translate. By clicking "OK" you agree to their privacy policy and that we save your preferred language in your local storage. Moreover, design quality may go down. The translation may be incorrect.');
        if (!consent) return;
    }

    try {
        localStorage.setItem('translateEnabled', 'true');

        const google_translate_element = document.getElementById('google_translate_element');
        if (!google_translate_element) return;

        const style = document.createElement('style');
        style.textContent = `
            #google_translate_element {
                position: fixed;
                top: 20px;
                left: 10px;
                z-index: 9999;
            }
            .goog-te-banner-frame.skiptranslate {
                top: 80px !important;
                z-index: 9999 !important;
            }
        `;
        document.head.appendChild(style);

        if (window.translateLoaded) return;
        window.translateLoaded = true;

        window.googleTranslateElementInit = function () {
            new google.translate.TranslateElement({
                pageLanguage: 'de',
                layout: google.translate.TranslateElement.InlineLayout.SIMPLE
            }, 'google_translate_element');
        };

        const script = document.createElement('script');
        script.src = "//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
        script.id = "google_translate_script";
        document.body.appendChild(script);
        
    } catch (e) {
        alert("We're sorry, this function is not available at the moment. Please use your browser's translation tools or try again later.");
        console.error(e);
    }
}

function removeGoogleTranslate() {
    try {
        localStorage.removeItem('translateEnabled');
        window.translateLoaded = false;

        // Entferne das Google Translate Script
        const script = document.getElementById('google_translate_script');
        if (script) script.remove();

        // Entferne das eingebettete Widget
        const google_translate_element = document.getElementById('google_translate_element');
        if (google_translate_element) {
            google_translate_element.innerHTML = '';
            google_translate_element.style.display = 'none';
        }

        // Entferne alle Google Translate Styles
        const styles = document.querySelectorAll('style');
        styles.forEach(style => {
            if (style.textContent.includes('#google_translate_element') || style.textContent.includes('.goog-te-banner-frame')) {
                style.remove();
            }
        });

        // Entferne eventuelle Banner-Frames
        const frames = document.querySelectorAll('iframe');
        frames.forEach(frame => {
            if (frame.classList.contains('goog-te-banner-frame')) {
                frame.remove();
            }
        });

        // Entferne Google Translate DOM-Elemente
        const googElements = document.querySelectorAll('[class*="goog-te"]');
        googElements.forEach(el => el.remove());

        window.location.reload();

    } catch (e) {
        console.error("Error removing Google Translate:", e);
    }
}

function isGoogleTranslateActive() {
    return !!document.querySelector('.goog-te-menu-frame') || !!document.querySelector('.goog-te-banner-frame');
}