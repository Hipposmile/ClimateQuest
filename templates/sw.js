/* global workbox */

importScripts('/static/pwa/workbox/workbox-sw.js');

workbox.setConfig({
    modulePathPrefix: '/static/pwa/workbox/'
});

const CACHE = "pwabuilder-page";

const offlineFallbackPage = "/static/pwa/offline.html";

self.addEventListener("message", (event) => {
    if (event.data && event.data.type === "SKIP_WAITING") {
        self.skipWaiting();
    }
});

self.addEventListener('install', async (event) => {
    event.waitUntil(caches.open(CACHE)
        .then((cache) => cache.add(offlineFallbackPage)));
});

if (self.workbox && workbox.navigationPreload.isSupported()) {
    workbox.navigationPreload.enable();
}

self.addEventListener('fetch', (event) => {
    if (event.request.mode === 'navigate') {
        event.respondWith((async () => {
            try {
                const preloadResp = await event.preloadResponse;

                if (preloadResp) {
                    return preloadResp;
                }

                const networkResp = await fetch(event.request);
                return networkResp;
            } catch (error) {

                const cache = await caches.open(CACHE);
                const cachedResp = await cache.match(offlineFallbackPage);
                return cachedResp;
            }
        })());
    }
});

self.addEventListener('push', function (event) {
    const eventInfo = event.data.text();
    const data = JSON.parse(eventInfo);
    const head = data.head || 'New Notification 🕺🕺';
    const body = data.body || 'This is default content. Your notification didn\'t have one 🙄🙄';
    const url = data.url || '/benachrichtigungen/'

    // Keep the service worker alive until the notification is created.
    event.waitUntil(self.registration.showNotification(head, {
        body: body, data: {url: url}
    }));
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();

    const data = event.notification.data || {};
    const urlToOpen = data.url || '/'; // Fallback: Startseite

    event.waitUntil(clients.matchAll({type: 'window', includeUncontrolled: true}).then(windowClients => {
        // Prüfen, ob die Seite schon offen ist
        for (const client of windowClients) {
            if (client.url.includes(urlToOpen) && 'focus' in client) {
                return client.focus();
            }
        }

        // Sonst neue Seite öffnen
        if (clients.openWindow) {
            return clients.openWindow(urlToOpen);
        }
    }));
});