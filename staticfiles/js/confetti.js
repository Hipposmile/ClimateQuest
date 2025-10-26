const style_confetti = document.createElement('style');
style_confetti.textContent = `canvas {
        position: fixed;
        top: 0;
        left: 0;
        pointer-events: none;
        z-index: 9999;
    }`;
document.body.appendChild(style_confetti);

const canvas = document.createElement('canvas');
canvas.id = 'confetti-canvas';
document.body.appendChild(canvas);

const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let confettiParticles = [];
let isAnimating = false;

const colors = ['#FFC700', '#FF0000', '#2E3191', '#41BBC7', '#00ff5eff', '#ff00ddff', '#ff8c00ff'];

function createParticle() {
    return {
        x: Math.random() * canvas.width,
        y: canvas.height,
        size: Math.random() * 8 + 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        speedY: (Math.random() * 3 + 3) * -1,
        speedX: (Math.random() - 0.5) * 2,
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 10
    };
}

function startConfetti() {
    for (let i = 0; i < 150; i++) {
        confettiParticles.push(createParticle());
    }
    if (!isAnimating) {
        isAnimating = true;
        drawParticles();
    }
    setTimeout(() => {
        confettiParticles = [];
        isAnimating = false;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }, 5000);
}

function drawParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    confettiParticles.forEach(p => {
        p.y += p.speedY;
        p.x += p.speedX;
        p.rotation += p.rotationSpeed;

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rotation * Math.PI / 180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
        ctx.restore();
    });

    confettiParticles = confettiParticles.filter(p => p.y > -50);
    if (isAnimating) requestAnimationFrame(drawParticles);
}
