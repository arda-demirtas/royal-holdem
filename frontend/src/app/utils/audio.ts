let audioCtx: AudioContext | null = null;
const lastPlayTimes: Record<string, number> = {};

export const initAudio = () => {
  if (typeof window === "undefined") return;
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

export const playSound = (type: "click" | "check" | "fold" | "raise" | "deal") => {
  initAudio();
  if (!audioCtx) return;

  // Throttle to prevent overlapping identical sounds
  const now = audioCtx.currentTime;
  const lastTime = lastPlayTimes[type] || 0;
  const throttleMs = type === "click" ? 50 : 150;
  
  if (now * 1000 - lastTime < throttleMs) {
    return;
  }
  lastPlayTimes[type] = now * 1000;

  if (audioCtx.state === "suspended") {
    audioCtx.resume();
  }

  const playTime = audioCtx.currentTime;

  switch (type) {
    case "click": {
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
    case "deal": {
      // Card Deal: short friction sound (felt drag)
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
    case "raise": {
      // Chips Clink: 3 quick clinks
      const clink = (time: number, vol: number) => {
        if (!audioCtx) return;
        const freqs = [1800, 2700, 3900];
        freqs.forEach((freq) => {
          if (!audioCtx) return;
          const osc = audioCtx.createOscillator();
          const gain = audioCtx.createGain();

          osc.type = "sine";
          osc.frequency.setValueAtTime(freq, time);
          osc.frequency.exponentialRampToValueAtTime(freq * 0.9, time + 0.05);

          gain.gain.setValueAtTime(vol * 0.1, time);
          gain.gain.exponentialRampToValueAtTime(0.001, time + 0.05);

          osc.connect(gain);
          gain.connect(audioCtx.destination);

          osc.start(time);
          osc.stop(time + 0.05);
        });
      };

      clink(playTime, 0.4);
      clink(playTime + 0.04, 0.3);
      clink(playTime + 0.08, 0.2);
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
