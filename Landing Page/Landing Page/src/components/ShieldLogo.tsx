import React from "react";

export default function ShieldLogo() {
  return (
    <div className="hero-graphic-container">
      <div className="shield-logo-wrapper">
        <svg className="shield-svg" viewBox="0 0 800 800" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="metal-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#434343" />
              <stop offset="50%" stopColor="#2c3e50" />
              <stop offset="100%" stopColor="#000000" />
            </linearGradient>
            <linearGradient id="gold-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#d4af37" />
              <stop offset="50%" stopColor="#aa771c" />
              <stop offset="100%" stopColor="#f3e5ab" />
            </linearGradient>
            <filter id="neon-glow-red" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="15" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="neon-glow-orange" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="12" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          
          <circle cx="400" cy="380" r="280" fill="url(#metal-grad)" opacity="0.1" filter="url(#neon-glow-red)"/>
          
          <path d="M 400 120 L 530 180 C 530 180, 560 380, 400 600 C 240 380, 270 180, 270 180 Z" fill="url(#metal-grad)" stroke="#d4af37" strokeWidth="6" strokeLinejoin="round" />
          
          <path d="M 400 140 L 510 195 C 510 195, 535 370, 400 570 C 265 370, 290 195, 290 195 Z" fill="#0f1115" stroke="#1d222b" strokeWidth="4" />
          
          <path d="M 400 240 L 400 500 C 400 500, 315 380, 315 280 L 370 250 L 330 330 L 375 350 L 340 420 C 340 420, 385 460, 400 500 L 400 240 Z" fill="#b31212" opacity="0.95" filter="url(#neon-glow-red)"/>
          
          <g stroke="#ff6a00" strokeWidth="3" fill="none" opacity="0.8" filter="url(#neon-glow-orange)">
            <path d="M 430 220 L 490 250 L 490 320 L 460 350 L 460 410 L 430 440" />
            <path d="M 450 200 L 475 212 L 475 280 L 445 310" />
            <path d="M 410 460 L 450 500 L 435 525" />
            <circle cx="490" cy="320" r="5" fill="#ff6a00" />
            <circle cx="460" cy="410" r="5" fill="#ff9000" />
            <circle cx="445" cy="311" r="5" fill="#ff9000" />
            <circle cx="435" cy="525" r="5" fill="#ff6a00" />
          </g>

          <g className="eye-core">
            <path d="M 330 180 Q 400 130, 470 180 Q 400 210, 330 180 Z" fill="none" stroke="#d4af37" strokeWidth="4" />
            <circle cx="400" cy="175" r="28" fill="#e65c00" opacity="0.3" filter="url(#neon-glow-orange)"/>
            <circle cx="400" cy="175" r="16" fill="#ff9000" filter="url(#neon-glow-orange)"/>
            <circle cx="400" cy="175" r="7" fill="#ffffff" />
          </g>

          <line x1="400" y1="180" x2="400" y2="560" stroke="#d4af37" strokeWidth="4" opacity="0.7"/>
          <circle cx="400" cy="510" r="6" fill="#ff3300" filter="url(#neon-glow-red)" />
          <circle cx="400" cy="510" r="3" fill="#ffffff" />

          <circle cx="400" cy="380" r="340" fill="none" stroke="#ff3300" strokeDasharray="10 30" strokeWidth="1.5" opacity="0.3" className="hud-rotate" />
          <circle cx="400" cy="380" r="360" fill="none" stroke="#ff8c00" strokeDasharray="80 180" strokeWidth="2" opacity="0.2" className="hud-rotate-reverse" />
        </svg>
      </div>
      
      <div className="hud-overlay-card top-left">
        <span className="hud-lbl">SEC-STATUS</span>
        <span className="hud-val text-green">ARMED & SCANNING</span>
      </div>
      <div className="hud-overlay-card bottom-right">
        <span className="hud-lbl">GEMINI-CORE</span>
        <span className="hud-val text-amber">ANALYZING CHANNELS</span>
      </div>
    </div>
  );
}
