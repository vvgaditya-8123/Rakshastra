"use client";

import React, { useState, useEffect } from "react";

interface TextScrambleProps {
  texts: string[];
  speed?: number;
  intervalDuration?: number;
  className?: string;
}

const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&* रक्षास्त्र ラクシャストラ Ракшастра";

export default function TextScramble({
  texts,
  speed = 35,
  intervalDuration = 4000,
  className = "",
}: TextScrambleProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [displayText, setDisplayText] = useState(texts[0]);
  const [isAnimating, setIsAnimating] = useState(false);

  const startScramble = (targetText: string) => {
    setIsAnimating(true);
    let frame = 0;
    const totalFrames = targetText.length * 3;
    
    const interval = setInterval(() => {
      let result = "";
      for (let i = 0; i < targetText.length; i++) {
        if (i < frame / 3) {
          result += targetText[i];
        } else if (targetText[i] === " ") {
          result += " ";
        } else {
          result += chars[Math.floor(Math.random() * chars.length)];
        }
      }
      setDisplayText(result);

      if (frame >= totalFrames) {
        setDisplayText(targetText);
        clearInterval(interval);
        setIsAnimating(false);
      }
      frame++;
    }, speed);
  };

  useEffect(() => {
    const mainInterval = setInterval(() => {
      if (isAnimating) return;
      const nextIndex = (currentIndex + 1) % texts.length;
      setCurrentIndex(nextIndex);
      startScramble(texts[nextIndex]);
    }, intervalDuration);

    return () => clearInterval(mainInterval);
  }, [currentIndex, texts, isAnimating, intervalDuration]);

  // Initial scramble on mount
  useEffect(() => {
    startScramble(texts[0]);
  }, []);

  return (
    <span className={className}>
      {displayText}
    </span>
  );
}

