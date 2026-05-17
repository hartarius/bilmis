/**
 * BİLMİŞ — Frontend Oyun Mantığı
 * API çağrıları, oyun akışı, animasyonlar
 */

// Local geliştirme: backend 8000'de, frontend 3000'de
// Vercel production: aynı domain, relative URL
const API_BASE = (window.location.hostname === 'localhost' && window.location.port !== '8000')
    ? 'http://localhost:8000'
    : '';

let currentSession = null;
let currentSecret = null;
let isProcessing = false;

// ═══════════════════════════════════════════════════════════════════════
//  HELPERS
// ═══════════════════════════════════════════════════════════════════════

function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}

function showToast(message) {
    const toast = document.getElementById('error-toast');
    toast.textContent = message;
    toast.classList.add('visible');
    setTimeout(() => toast.classList.remove('visible'), 3000);
}

async function apiCall(endpoint, body) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            signal: controller.signal,
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || `Sunucu hatası (${res.status})`);
        }

        return data;
    } catch (e) {
        if (e.name === 'AbortError') {
            throw new Error('İstek zaman aşımına uğradı. Lütfen tekrar dene.');
        }
        if (e.message.includes('Failed to fetch') || e.message.includes('NetworkError')) {
            throw new Error('Sunucuya bağlanılamadı. Backend çalışıyor mu?');
        }
        throw e;
    } finally {
        clearTimeout(timeout);
    }
}

// ═══════════════════════════════════════════════════════════════════════
//  TYPEWRITER EFFECT
// ═══════════════════════════════════════════════════════════════════════

async function typeQuestion(text) {
    const bubble = document.getElementById('question-text');
    const thinking = document.getElementById('thinking');

    thinking.classList.add('active');
    bubble.style.animation = 'none';
    bubble.offsetHeight; // reflow
    bubble.style.animation = 'bubbleIn 0.4s ease';
    bubble.textContent = '';

    // Hızlı yazma efekti
    const baseDelay = 20;
    for (let i = 0; i < text.length; i++) {
        bubble.textContent += text[i];
        // Noktalama işaretlerinde duraksa
        const delay = ',.!?:;'.includes(text[i]) ? baseDelay * 5 : baseDelay + Math.random() * 10;
        await new Promise(r => setTimeout(r, delay));
    }

    thinking.classList.remove('active');
}

// ═══════════════════════════════════════════════════════════════════════
//  HISTORY
// ═══════════════════════════════════════════════════════════════════════

function addToHistory(answer) {
    const qText = document.getElementById('question-text').textContent;
    const history = document.getElementById('history');
    const div = document.createElement('div');
    div.className = 'history-item';

    const answerEmoji = answer === 'evet' ? '✅' : answer === 'hayır' ? '❌' : '🤷';
    div.innerHTML = `<strong>S:</strong> ${qText}<br><strong>C:</strong> ${answerEmoji} ${answer}`;
    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
}

// ═══════════════════════════════════════════════════════════════════════
//  GAME START
// ═══════════════════════════════════════════════════════════════════════

document.getElementById('start-btn').addEventListener('click', async () => {
    if (isProcessing) return;

    const secret = document.getElementById('secret-input').value.trim();
    if (!secret) {
        showToast('Lütfen aklından bir şey tut! 🤔');
        document.getElementById('secret-input').focus();
        return;
    }

    if (secret.length > 100) {
        showToast('Biraz daha kısa bir şey tutar mısın? (max 100 karakter)');
        return;
    }

    isProcessing = true;
    const btn = document.getElementById('start-btn');
    btn.disabled = true;
    btn.querySelector('.btn-text').textContent = '⏳ Düşünüyorum...';

    try {
        const data = await apiCall('/api/new-game', { secret });
        currentSession = data.session_id;
        currentSecret = secret;

        showScreen('game-screen');
        document.getElementById('question-num').textContent = data.question_number;
        document.getElementById('history').innerHTML = '';

        await typeQuestion(data.question);
    } catch (e) {
        showToast(e.message);
    } finally {
        isProcessing = false;
        btn.disabled = false;
        btn.querySelector('.btn-text').textContent = '🔍 Başla';
    }
});

// Enter tuşu ile başlat
document.getElementById('secret-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('start-btn').click();
    }
});

// ═══════════════════════════════════════════════════════════════════════
//  ANSWER HANDLING
// ═══════════════════════════════════════════════════════════════════════

document.querySelectorAll('.btn-answer').forEach(btn => {
    btn.addEventListener('click', async () => {
        if (isProcessing || !currentSession) return;

        const answer = btn.dataset.answer;
        isProcessing = true;

        // Tüm butonları disable et
        document.querySelectorAll('.btn-answer').forEach(b => b.disabled = true);

        // Cevabı geçmişe ekle
        addToHistory(answer);

        try {
            const data = await apiCall('/api/answer', {
                session_id: currentSession,
                answer: answer,
            });

            document.getElementById('question-num').textContent = data.question_number;

            if (data.is_final) {
                showReveal(data.question);
            } else {
                await typeQuestion(data.question);
            }
        } catch (e) {
            showToast(e.message);
        } finally {
            isProcessing = false;
            if (currentSession) {
                document.querySelectorAll('.btn-answer').forEach(b => b.disabled = false);
            }
        }
    });
});

// ═══════════════════════════════════════════════════════════════════════
//  REVEAL
// ═══════════════════════════════════════════════════════════════════════

function showReveal(text) {
    const clean = text.replace(/^🎯\s*TAHMİN:\s*/i, '').trim();
    const finalText = clean.startsWith('🎯') ? clean : `🎯 ${clean}`;

    showScreen('reveal-screen');
    document.getElementById('revealed-answer').textContent = finalText;

    // Kullanıcının girdiği orijinal secret'ı göster
    if (currentSecret) {
        document.getElementById('secret-compare').textContent =
            `Senin tuttuğun: "${currentSecret}"`;
    }
}

// ═══════════════════════════════════════════════════════════════════════
//  REPLAY
// ═══════════════════════════════════════════════════════════════════════

document.getElementById('replay-btn').addEventListener('click', () => {
    currentSession = null;
    currentSecret = null;
    document.getElementById('secret-input').value = '';
    document.getElementById('history').innerHTML = '';
    document.getElementById('question-text').textContent = '';
    showScreen('start-screen');
    document.getElementById('secret-input').focus();
});
