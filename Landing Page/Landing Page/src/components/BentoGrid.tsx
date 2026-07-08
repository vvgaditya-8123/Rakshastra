import React from "react";

export default function BentoGrid() {
  return (
    <div className="features-grid">
      <div className="feature-card wide">
        <div className="feature-icon coral">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><line x1="2" y1="12" x2="22" y2="12"/></svg>
        </div>
        <h3>Multi-Platform Autonomous Crawlers</h3>
        <p>Continuous, stealthy ingestion of messages, stories, and bot loops across Telegram, WhatsApp, and Instagram. Dynamically spins up crawlers with human-like interaction heuristics to evade anti-scraping defenses.</p>
      </div>

      <div className="feature-card">
        <div className="feature-icon sky">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
        </div>
        <h3>Gemini NLP Engine</h3>
        <p>Identifies coded messaging, localized drug slang, and emoji patterns using custom Gemini Pro semantic models.</p>
      </div>

      <div className="feature-card">
        <div className="feature-icon pink">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z"/><circle cx="12" cy="10" r="3"/></svg>
        </div>
        <h3>Metadata Triangulator</h3>
        <p>Extracts IP logs, device fingerprints, phone numbers, and email accounts to pinpoint offender locations.</p>
      </div>

      <div className="feature-card wide">
        <div className="feature-icon lime">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
        </div>
        <h3>Security Knowledge Graph</h3>
        <p>Unifies isolated threat footprints into a single Neo4j graph. Links Telegram bots to Instagram handles through shared metadata relationships — creating a digital twin of criminal networks.</p>
      </div>
    </div>
  );
}
