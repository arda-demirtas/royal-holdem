"use client";

import { useEffect } from "react";
import { initAudio, attachGlobalClickListener } from "../utils/audio";

export default function AudioProvider() {
  useEffect(() => {
    // Attach the global click listener
    const removeListener = attachGlobalClickListener();

    // Warm up/resume AudioContext on first user action
    const handleInteraction = () => {
      initAudio();
      
      // Remove warming event listeners once interaction is registered
      window.removeEventListener("click", handleInteraction);
      window.removeEventListener("keydown", handleInteraction);
      window.removeEventListener("touchstart", handleInteraction);
    };

    window.addEventListener("click", handleInteraction);
    window.addEventListener("keydown", handleInteraction);
    window.addEventListener("touchstart", handleInteraction);

    return () => {
      removeListener();
      window.removeEventListener("click", handleInteraction);
      window.removeEventListener("keydown", handleInteraction);
      window.removeEventListener("touchstart", handleInteraction);
    };
  }, []);

  return null;
}
