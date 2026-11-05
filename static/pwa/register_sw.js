const getCsrfMiddlewareToken = () => {
    return document.querySelector('input[name="csrfmiddlewaretoken"]').value;
}

const registerSw = async () => {
    if ('serviceWorker' in navigator) {
        await navigator.serviceWorker.register('/sw.js');

        // WICHTIG: Auf aktiven SW warten
        const reg = await navigator.serviceWorker.ready;

        initialiseState(reg);
    } else {
        showNotAllowed("You can't send push notifications ☹️😢");
    }
};

const initialiseState = (reg) => {
    if (!reg.showNotification) {
        showNotAllowed('Showing notifications isn\'t supported ☹️😢');
        return
    }
    if (Notification.permission === 'denied') {
        showNotAllowed('You prevented us from showing notifications ☹️🤔');
        return
    }
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
    if (!('PushManager' in window)) {
        showNotAllowed("Push isn't allowed in your browser 🤔");
        return
    }
    subscribe(reg);
}

const showNotAllowed = (message) => {
    //const button = document.querySelector('form>button');
    //button.innerHTML = `${message}`;
    //button.setAttribute('disabled', 'true');
};

function urlB64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    const outputData = outputArray.map((output, index) => rawData.charCodeAt(index));

    return outputData;
}

const subscribe = async (reg) => {
    const subscription = await reg.pushManager.getSubscription();
    if (subscription) {
        sendSubData(subscription);
        return;
    }

    const vapidMeta = document.querySelector('meta[name="vapid-key"]');
    const key = vapidMeta.content;
    const options = {
        userVisibleOnly: true,
        // if key exists, create applicationServerKey property
        ...(key && {applicationServerKey: urlB64ToUint8Array(key)})
    };

    const sub = await reg.pushManager.subscribe(options);
    sendSubData(sub)
};

// The server only needs to hear about a push subscription when it is new or the user changed.
// Without this check every single page view sent a POST (and a database write) to /webpush/save_information.
const syncKey = (subscription) => {
    const userMeta = document.querySelector('meta[name="cq-user-id"]');
    return `${userMeta ? userMeta.content : ''}|${subscription.endpoint}`;
};

const alreadySynced = (key) => {
    try {
        return localStorage.getItem('push-subscription-synced') === key;
    } catch (error) {
        return false;
    }
};

const rememberSynced = (key) => {
    try {
        localStorage.setItem('push-subscription-synced', key);
    } catch (error) {
        // storage not available: we simply sync again next time
    }
};

const sendSubData = async (subscription) => {
    const key = syncKey(subscription);
    if (alreadySynced(key)) {
        return;
    }
    const browser = navigator.userAgent.match(/(firefox|msie|chrome|safari|trident)/ig)[0].toLowerCase();
    const token = getCsrfMiddlewareToken();
    const data = {
        status_type: 'subscribe',
        subscription: subscription.toJSON(),
        browser: browser,
    };

    const res = await fetch('/webpush/save_information', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
            'content-type': 'application/json',
            'X-CSRF-Token': token,
        },
        credentials: "include"
    });

    if (res.ok) {
        rememberSynced(key);
    }
    handleResponse(res);
};

const handleResponse = (res) => {

};

registerSw();
