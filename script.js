const audio = document.getElementById('audio');
const visualizer = document.getElementById('visualizer');
const imageGrid = document.getElementById('image-grid');

// Fetch and populate images
fetch('static/images.json')
    .then(response => response.json())
    .then(images => {
        // Calculate how many images we need to fill the grid
        // Each row is (200vw / 8) / (16 / 9) height
        // We need at least 200vh of height
        const rowHeight = (window.innerWidth * 2 / 8) / (16 / 9);
        const rowsNeeded = Math.ceil((window.innerHeight * 2) / rowHeight);
        const totalImages = Math.max(64, rowsNeeded * 8);

        // Populate grid with images (random order)
        for (let i = 0; i < totalImages; i++) {
            const img = document.createElement('img');
            const randomIndex = Math.floor(Math.random() * images.length);
            img.src = images[randomIndex];
            img.alt = `Image ${i + 1}`;
            imageGrid.appendChild(img);
        }
    });

// Split text into words, then split each word into characters with rainbow colors
const text = visualizer.textContent;
visualizer.textContent = '';
const words = text.split(' ');
const chars = [];
let charIndex = 0;
words.forEach((word, wordIdx) => {
    const wordSpan = document.createElement('span');
    wordSpan.style.display = 'inline-block';
    wordSpan.style.whiteSpace = 'nowrap';

    word.split('').forEach((char) => {
        const span = document.createElement('span');
        span.textContent = char;
        const hue = (charIndex / text.length) * 360;
        span.style.color = `hsl(${hue}, 100%, 85%)`;
        wordSpan.appendChild(span);
        chars.push(span);
        charIndex++;
    });

    visualizer.appendChild(wordSpan);

    // Add space after word (except for the last word)
    if (wordIdx < words.length - 1) {
        const space = document.createTextNode(' ');
        visualizer.appendChild(space);
        charIndex++; // Count the space
    }
});

// Create audio context and analyzer
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const analyser = audioContext.createAnalyser();
const source = audioContext.createMediaElementSource(audio);

source.connect(analyser);
analyser.connect(audioContext.destination);

analyser.fftSize = 256;
const bufferLength = analyser.frequencyBinCount;
const dataArray = new Uint8Array(bufferLength);

// Function to get bass (low frequencies)
function getBass() {
    // Average of lower frequency bins (bass range)
    let sum = 0;
    const bassRange = Math.floor(bufferLength * 0.5); // First 15% of frequencies
    for (let i = 0; i < bassRange; i++) {
        sum += dataArray[i];
    }
    return sum / bassRange / 255; // Normalize to 0-1
}

// Function to get treble (high frequencies)
function getTreble() {
    // Average of higher frequency bins (treble range)
    let sum = 0;
    const trebleStart = Math.floor(bufferLength * 0.5); // Last 30% of frequencies
    for (let i = trebleStart; i < bufferLength; i++) {
        sum += dataArray[i];
    }
    return sum / (bufferLength - trebleStart) / 255; // Normalize to 0-1
}

// Animation loop
let hueOffset = 0;
function animate() {
    requestAnimationFrame(animate);

    analyser.getByteFrequencyData(dataArray);

    const bass = getBass();
    const treble = getTreble();

    // Apply exponential function: loud = big
    const scaleX = Math.pow(bass * 3, 2) * 0.2; // Exponential scaling
    const scaleY = Math.pow(treble * 3, 2); // Exponential scaling

    visualizer.style.transform = `scale(${scaleX}, ${scaleY})`;

    // Animate rainbow hue shift and wave
    hueOffset += 2;
    const time = Date.now() * 0.003;
    chars.forEach((span, i) => {
        const hue = ((i / text.length) * 360 + hueOffset) % 360;
        span.style.color = `hsl(${hue}, 100%, 85%)`;

        // Wave animation
        const wave = Math.sin(time + i * 0.5) * 30;
        span.style.transform = `translateY(${wave}px)`;
    });
}

// Button to start visualizer
const startBtn = document.getElementById('startBtn');
const title = document.getElementById('title');
const originalTitle = title.textContent;

startBtn.addEventListener('click', () => {
    startBtn.style.display = 'none';
    visualizer.style.display = 'block';

    // Flash arrows around title
    let showArrows = true;
    setInterval(() => {
        title.textContent = showArrows ? `>>> ${originalTitle} <<<` : originalTitle;
        showArrows = !showArrows;
    }, 100);

    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }

    audio.play().then(() => {
        animate();
    }).catch(err => console.error('Playback failed:', err));
});

// Handle audio errors
audio.addEventListener('error', (e) => {
    console.error('Audio error:', e);
});
