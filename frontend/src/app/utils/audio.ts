let audioCtx: AudioContext | null = null;
const lastPlayTimes: Record<string, number> = {};

let chipAudio: HTMLAudioElement | null = null;
let kartAudio: HTMLAudioElement | null = null;

export const initAudio = () => {
  if (typeof window === "undefined") return;

  // Initialize HTML5 Audio elements for MP3 files
  if (!chipAudio) {
    chipAudio = new Audio("/chip.mp3");
    chipAudio.preload = "auto";
  }
  if (!kartAudio) {
    kartAudio = new Audio("/kart.mp3");
    kartAudio.preload = "auto";
  }

  if (!audioCtx) {
    // @ts-ignore
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (audioCtx && audioCtx.state === "suspended") {
    audioCtx.resume();
  }
};

export const playSound = (type: "click" | "check" | "fold" | "raise" | "deal" | "win" | "pocket_deal") => {
  initAudio();
  
  // Throttle to prevent overlapping identical sounds
  const now = Date.now();
  const lastTime = lastPlayTimes[type] || 0;
  const throttleMs = type === "click" ? 50 : 150;
  
  if (now - lastTime < throttleMs) {
    return;
  }
  lastPlayTimes[type] = now;

  if (audioCtx && audioCtx.state === "suspended") {
    audioCtx.resume();
  }

  const playTime = audioCtx ? audioCtx.currentTime : 0;

  switch (type) {
    case "click": {
      if (!audioCtx) return;
      // Short pitch-dropping UI click
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      
      osc.type = "sine";
      osc.frequency.setValueAtTime(1000, playTime);
      osc.frequency.exponentialRampToValueAtTime(300, playTime + 0.04);
      
      gain.gain.setValueAtTime(0.08, playTime);
      gain.gain.exponentialRampToValueAtTime(0.001, playTime + 0.04);
      
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start(playTime);
      osc.stop(playTime + 0.04);
      break;
    }
    case "check": {
      if (!audioCtx) return;
      // Wood knock sound on table: two knocks in succession
      const knock = (time: number) => {
        if (!audioCtx) return;
        // Low sine for the tone
        const osc = audioCtx.createOscillator();
        const oscGain = audioCtx.createGain();
        osc.frequency.setValueAtTime(130, time);
        osc.frequency.exponentialRampToValueAtTime(60, time + 0.08);
        oscGain.gain.setValueAtTime(0.4, time);
        oscGain.gain.exponentialRampToValueAtTime(0.001, time + 0.08);
        
        osc.connect(oscGain);
        oscGain.connect(audioCtx.destination);
        osc.start(time);
        osc.stop(time + 0.08);

        // Low-passed white noise for the thump
        const bufferSize = audioCtx.sampleRate * 0.06;
        const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
          data[i] = Math.random() * 2 - 1;
        }
        
        const noise = audioCtx.createBufferSource();
        noise.buffer = buffer;
        
        const filter = audioCtx.createBiquadFilter();
        filter.type = "lowpass";
        filter.frequency.setValueAtTime(180, time);
        filter.Q.setValueAtTime(1, time);
        
        const noiseGain = audioCtx.createGain();
        noiseGain.gain.setValueAtTime(0.2, time);
        noiseGain.gain.exponentialRampToValueAtTime(0.001, time + 0.06);
        
        noise.connect(filter);
        filter.connect(noiseGain);
        noiseGain.connect(audioCtx.destination);
        
        noise.start(time);
        noise.stop(time + 0.06);
      };

      knock(playTime);
      knock(playTime + 0.14); // second knock
      break;
    }
    case "fold": {
      if (!audioCtx) return;
      // Fold: Swoosh/slide of cards
      const duration = 0.15;
      const bufferSize = audioCtx.sampleRate * duration;
      const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        data[i] = Math.random() * 2 - 1;
      }

      const noise = audioCtx.createBufferSource();
      noise.buffer = buffer;

      const filter = audioCtx.createBiquadFilter();
      filter.type = "bandpass";
      filter.Q.setValueAtTime(5, playTime);
      filter.frequency.setValueAtTime(1400, playTime);
      filter.frequency.exponentialRampToValueAtTime(400, playTime + duration);

      const gain = audioCtx.createGain();
      gain.gain.setValueAtTime(0.001, playTime);
      gain.gain.linearRampToValueAtTime(0.12, playTime + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.001, playTime + duration);

      noise.connect(filter);
      filter.connect(gain);
      gain.connect(audioCtx.destination);

      noise.start(playTime);
      noise.stop(playTime + duration);
      break;
    }
    case "pocket_deal": {
      if (!audioCtx) return;
      // Card Deal: soft felt friction drag (for player pocket card deals)
      const duration = 0.2;
      const bufferSize = audioCtx.sampleRate * duration;
      const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        data[i] = Math.random() * 2 - 1;
      }

      const noise = audioCtx.createBufferSource();
      noise.buffer = buffer;

      const filter = audioCtx.createBiquadFilter();
      filter.type = "bandpass";
      filter.Q.setValueAtTime(3, playTime);
      filter.frequency.setValueAtTime(800, playTime);
      filter.frequency.exponentialRampToValueAtTime(600, playTime + duration);

      const gain = audioCtx.createGain();
      gain.gain.setValueAtTime(0.001, playTime);
      gain.gain.linearRampToValueAtTime(0.08, playTime + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.001, playTime + duration);

      noise.connect(filter);
      filter.connect(gain);
      gain.connect(audioCtx.destination);

      noise.start(playTime);
      noise.stop(playTime + duration);
      break;
    }
    case "raise":
    case "win": {
      // Play chip.mp3
      if (chipAudio) {
        try {
          const clone = chipAudio.cloneNode(true) as HTMLAudioElement;
          clone.volume = 0.55;
          clone.play().catch(e => console.log("Play chip.mp3 error:", e));
        } catch (e) {
          console.log("Clone chip.mp3 error:", e);
        }
      }
      break;
    }
    case "deal": {
      // Play kart.mp3 (community cards deal)
      if (kartAudio) {
        try {
          const clone = kartAudio.cloneNode(true) as HTMLAudioElement;
          clone.volume = 0.55;
          clone.play().catch(e => console.log("Play kart.mp3 error:", e));
        } catch (e) {
          console.log("Clone kart.mp3 error:", e);
        }
      }
      break;
    }
  }
};

export const attachGlobalClickListener = () => {
  if (typeof window === "undefined") return () => {};

  const handler = (e: MouseEvent) => {
    const target = e.target as HTMLElement;
    const button = target.closest("button") || target.closest("select") || target.closest("[role=\"button\"]");
    if (!button) return;

    // Ignore game actions that play their own specific sound effects
    const action = button.getAttribute("data-action");
    if (
      action === "fold" ||
      action === "check" ||
      action === "call" ||
      action === "raise"
    ) {
      return;
    }

    playSound("click");
  };

  document.addEventListener("click", handler);
  return () => {
    document.removeEventListener("click", handler);
  };
};
