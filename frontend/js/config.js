// --- DEPLOYMENT CONFIGURATION ---
// IMPORTANT: Replace this with your actual Render URL!
// Example: "https://teacher-ai-backend.onrender.com"
const RENDER_BACKEND_URL = "https://ai-teacher-yv61.onrender.com";

const IS_PRODUCTION = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

window.API_BASE_URL = IS_PRODUCTION ? RENDER_BACKEND_URL : "";

if (IS_PRODUCTION) {
    window.WS_BASE_URL = RENDER_BACKEND_URL.replace(/^http/, 'ws');
} else {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    window.WS_BASE_URL = `${proto}//${window.location.host}`;
}
