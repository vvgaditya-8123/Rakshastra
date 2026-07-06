"use client";

import React, { useEffect, useRef, useState } from "react";
import { animate, createTimeline } from "animejs";
import { motion, AnimatePresence } from "framer-motion";
import Header from "@/components/Header";
import AnimatedDotGrid from "@/components/AnimatedDotGrid";
import TextScramble from "@/components/TextScramble";
import { CrowdVisualizer } from "@/components/CrowdCanvas";
import TerminalConsole from "@/components/TerminalConsole";
import CapabilityShowcase from "@/components/CapabilityShowcase";
import Roadmap from "@/components/Roadmap";
import DownloadSection from "@/components/DownloadSection";
import Footer from "@/components/Footer";


export default function Home() {
  const heroRef = useRef<HTMLDivElement>(null);
  const problemRef = useRef<HTMLDivElement>(null);
  const [expandedCard, setExpandedCard] = useState<"infrastructure" | "response" | null>(null);

  useEffect(() => {
    // 1. Initial Page Load Animation using Anime.js v4
    const tl = createTimeline({
      defaults: {
        ease: 'outExpo',
        duration: 1000
      }
    });

    // Animate badge
    tl.add('.hero-version', {
      opacity: [0, 1],
      translateY: [20, 0],
      duration: 800,
    });

    // Animate Hero title container
    tl.add('.hero-title-container', {
      opacity: [0, 1],
      translateY: [30, 0],
      duration: 1000,
    }, '-=600');

    // Animate Hero description
    tl.add('.hero-desc', {
      opacity: [0, 1],
      translateY: [20, 0],
      duration: 800,
    }, '-=1000');

    // Animate buttons with manual stagger delay
    tl.add('.hero-actions .btn-accent', {
      opacity: [0, 1],
      translateY: [15, 0],
      duration: 800,
    }, '-=700');

    tl.add('.hero-actions .btn-outline', {
      opacity: [0, 1],
      translateY: [15, 0],
      duration: 800,
    }, '-=700');

    // Animate Threat Visualizer Widget on the right
    tl.add('.visualizer-wrapper', {
      opacity: [0, 1],
      scale: [0.95, 1],
      duration: 1200,
      ease: 'outElastic(1, .8)'
    }, '-=1000');

    const observerProblem = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animate('#problem .problem-header-anim', {
            opacity: [0, 1],
            translateY: [30, 0],
            duration: 1000,
            ease: 'outExpo'
          });
          observerProblem.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    const observerConsole = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animate('#live-console .console-anim-target', {
            opacity: [0, 1],
            translateY: [40, 0],
            duration: 1200,
            ease: 'outExpo'
          });
          observerConsole.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    const probHeader = document.querySelector('#problem');
    if (probHeader) observerProblem.observe(probHeader);

    const consoleEl = document.querySelector('#live-console');
    if (consoleEl) observerConsole.observe(consoleEl);

    return () => {
      observerProblem.disconnect();
      observerConsole.disconnect();
    };
  }, []);

  return (
    <>
      <Header />

      <main>
        {/* ── Hero ── */}
        <section className="hero" style={{ padding: '4rem 1.5rem', minHeight: '85vh', display: 'flex', alignItems: 'center' }} ref={heroRef}>
          <AnimatedDotGrid />

          <div className="header-inner" style={{ position: 'relative', zIndex: 10, width: '100%', maxWidth: '1200px', display: 'grid', gridTemplateColumns: '1fr', gap: '3rem', alignItems: 'center' }}>
            <style dangerouslySetInnerHTML={{__html: `
              @media (min-width: 900px) {
                .hero-grid-split {
                  grid-template-columns: 1.1fr 0.9fr !important;
                }
              }
            `}} />
            <div className="hero-grid-split" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '3rem', alignItems: 'center', width: '100%' }}>
              
              {/* Left Column: Typography & Actions */}
              <div style={{ textAlign: 'left' }}>
                <span className="hero-version" style={{ opacity: 0 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--green)', display: 'inline-block', marginRight: '6px' }} />
                  v1.0.0 — Active Threat Intel
                </span>

                <div className="hero-title-container" style={{ opacity: 0 }}>
                  <h1 style={{ fontSize: 'clamp(3rem, 5.5vw, 5rem)', margin: 0, lineHeight: 1.1, minHeight: '120px', display: 'flex', alignItems: 'center' }}>
                    <TextScramble 
                      texts={[
                        "Rakshastra",
                        "रक्षास्त्र",
                        "రక్షాస్త్ర",
                        "ரக்ஷாஸ்த்ரா",
                        "রক্ষাস্ত্র",
                        "ರಕ್ಷಾಸ್ತ್ರ",
                        "રક્ષાસ્ત્ર",
                        "രക്ഷാസ്ത്ര"
                      ]} 
                      intervalDuration={3500}
                    />
                  </h1>
                </div>

                <p className="hero-desc" style={{ fontSize: '1.05rem', color: 'var(--fg-3)', margin: '0 0 2.5rem 0', maxWidth: '540px', lineHeight: 1.65, opacity: 0 }}>
                  An autonomous, AI-driven cyber defense agent designed to map, track, and disrupt digital narcotics operations and illicit bot networks across modern social platforms.
                </p>

                <div className="hero-actions" style={{ justifyContent: 'flex-start' }}>
                  <a href="#download" className="btn-accent" style={{ opacity: 0 }}>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Download Agent
                  </a>
                  <a href="#live-console" className="btn-outline" style={{ opacity: 0 }}>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
                    Live Console
                  </a>
                </div>
              </div>

              {/* Right Column: Interactive Visualizer Widget */}
              <div className="visualizer-wrapper" style={{ width: '100%', opacity: 0 }}>
                <CrowdVisualizer />
              </div>

            </div>
          </div>
        </section>

        <div className="divider" />

        {/* ── Problem ── */}
        <section className="section" id="problem" ref={problemRef}>
          <div className="problem-header-anim" style={{ marginBottom: '2.5rem', opacity: 0 }}>
            <span className="section-label">The Problem</span>
            <h2 className="section-heading">
              Drug networks hide in plain sight<br />across social platforms
            </h2>
            <p className="section-desc">
              Traffickers exploit Telegram channels, Instagram DMs, and WhatsApp
              groups to run automated, bot-driven supply chains with menus,
              pricing, and drop-location delivery.
            </p>
          </div>

          <div 
            className="features-grid"
            onMouseLeave={() => setExpandedCard(null)}
          >
            {/* Card 1: Invisible Infrastructure */}
            <motion.div
              layout
              initial={{ opacity: 0, y: 40, scale: 0.98 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{
                opacity: { duration: 0.8, delay: 0.1 },
                y: { type: "spring", stiffness: 100, damping: 15, delay: 0.1 },
                layout: { type: "spring", stiffness: 120, damping: 20 }
              }}
              onMouseEnter={() => setExpandedCard("infrastructure")}
              onClick={() => setExpandedCard("infrastructure")}
              className="feature-card"
              style={{
                flex: expandedCard === "infrastructure"
                  ? 2.2
                  : expandedCard === "response"
                    ? 0.8
                    : 1.5,
                cursor: "pointer",
                border: expandedCard === "infrastructure" ? "1px solid var(--sky)" : "1px solid rgba(255, 255, 255, 0.03)",
                boxShadow: expandedCard === "infrastructure" ? "0 0 20px rgba(5, 219, 233, 0.15)" : "none",
                transition: "border-color 0.3s ease, box-shadow 0.3s ease, background 0.3s ease",
              }}
            >
              <div className="feature-icon sky">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z"/><circle cx="12" cy="10" r="3"/></svg>
              </div>
              <h3>Invisible Infrastructure</h3>
              <p>Disposable accounts, coded slang, and emoji-based pricing that evades traditional keyword filters.</p>
              
              {expandedCard !== "infrastructure" && (
                <div style={{ 
                  marginTop: "1.25rem", 
                  fontFamily: "var(--font-mono)", 
                  fontSize: "0.68rem", 
                  color: "var(--sky)", 
                  opacity: 0.65,
                  display: "flex",
                  alignItems: "center",
                  gap: "6px"
                }}>
                  <span className="scanning-dot" style={{ width: "5px", height: "5px", borderRadius: "50%", background: "var(--sky)" }} />
                  <span>[ HOVER TO DECRYPT ]</span>
                </div>
              )}
              
              <AnimatePresence>
                {expandedCard === "infrastructure" && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.35, ease: "easeInOut" }}
                    style={{ overflow: "hidden" }}
                  >
                    <div style={{ marginTop: "1.5rem", borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "1.25rem" }}>
                      <h4 style={{ fontSize: "0.78rem", fontFamily: "var(--font-mono)", color: "var(--sky)", marginBottom: "0.75rem", letterSpacing: "0.05em" }}>
                        &gt; CORE_VULNERABILITIES_MAPPED
                      </h4>
                      <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: "0.82rem", color: "var(--fg-3)", display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                        <li style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
                          <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "var(--sky)", marginTop: "6px", flexShrink: 0 }} />
                          <span><strong>Disposable Bots:</strong> Automated storefronts rotated every 24-48 hours.</span>
                        </li>
                        <li style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
                          <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "var(--sky)", marginTop: "6px", flexShrink: 0 }} />
                          <span><strong>Emoji Codebooks:</strong> Dynamic menus avoiding standard keyword detection.</span>
                        </li>
                        <li style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
                          <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "var(--sky)", marginTop: "6px", flexShrink: 0 }} />
                          <span><strong>Drop Zones:</strong> Geotagged images in public chats with stripped metadata.</span>
                        </li>
                      </ul>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>

            {/* Card 2: Rakshastra's Response */}
            <motion.div
              layout
              initial={{ opacity: 0, y: 40, scale: 0.98 }}
              whileInView={{ opacity: 1, y: 0, scale: 1 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{
                opacity: { duration: 0.8, delay: 0.25 },
                y: { type: "spring", stiffness: 100, damping: 15, delay: 0.25 },
                layout: { type: "spring", stiffness: 120, damping: 20 }
              }}
              onMouseEnter={() => setExpandedCard("response")}
              onClick={() => setExpandedCard("response")}
              className="feature-card"
              style={{
                flex: expandedCard === "response"
                  ? 2.2
                  : expandedCard === "infrastructure"
                    ? 0.8
                    : 1.5,
                cursor: "pointer",
                border: expandedCard === "response" ? "1px solid var(--coral)" : "1px solid rgba(255, 255, 255, 0.03)",
                boxShadow: expandedCard === "response" ? "0 0 20px rgba(255, 125, 54, 0.15)" : "none",
                transition: "border-color 0.3s ease, box-shadow 0.3s ease, background 0.3s ease",
              }}
            >
              <div className="feature-icon coral">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </div>
              <h3>Rakshastra&apos;s Response</h3>
              <p>An autonomous AI agent combining Gemini NLP, graph-based identity resolution, and real-time metadata triangulation to build actionable intelligence for law enforcement agencies.</p>
              
              {expandedCard !== "response" && (
                <div style={{ 
                  marginTop: "1.25rem", 
                  fontFamily: "var(--font-mono)", 
                  fontSize: "0.68rem", 
                  color: "var(--coral)", 
                  opacity: 0.65,
                  display: "flex",
                  alignItems: "center",
                  gap: "6px"
                }}>
                  <span className="scanning-dot" style={{ width: "5px", height: "5px", borderRadius: "50%", background: "var(--coral)" }} />
                  <span>[ HOVER TO SCAN ]</span>
                </div>
              )}
              
              <AnimatePresence>
                {expandedCard === "response" && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.35, ease: "easeInOut" }}
                    style={{ overflow: "hidden" }}
                  >
                    <div style={{ marginTop: "1.5rem", borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "1.25rem" }}>
                      <h4 style={{ fontSize: "0.78rem", fontFamily: "var(--font-mono)", color: "var(--coral)", marginBottom: "0.75rem", letterSpacing: "0.05em" }}>
                        &gt; INTEGRATED_MITIGATION_SKILLS
                      </h4>
                      <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: "0.82rem", color: "var(--fg-3)", display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                        <li style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
                          <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "var(--coral)", marginTop: "6px", flexShrink: 0 }} />
                          <span><strong>Gemini Reasoning:</strong> Decodes street slang and maps accounts to legal identities.</span>
                        </li>
                        <li style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
                          <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "var(--coral)", marginTop: "6px", flexShrink: 0 }} />
                          <span><strong>Identity Graphing:</strong> Connects TG handles, Insta profiles, and WA numbers.</span>
                        </li>
                        <li style={{ display: "flex", alignItems: "flex-start", gap: "10px" }}>
                          <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "var(--coral)", marginTop: "6px", flexShrink: 0 }} />
                          <span><strong>Stealth Alerts:</strong> Triangulates high-fidelity digests directly to LEA officers.</span>
                        </li>
                      </ul>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>
        </section>

        <div className="divider" />

        {/* ── Console ── */}
        <section className="section" id="live-console">
          <div className="console-anim-target" style={{ opacity: 0 }}>
            <div style={{ marginBottom: '1rem' }}>
              <span className="section-label">Live Simulation</span>
              <h2 className="section-heading">Agent Console</h2>
              <p className="section-desc">
                Watch the crawlers ingest, analyze, and triangulate threats in real time.
              </p>
            </div>
            <TerminalConsole />
          </div>
        </section>

        <div className="divider" />

        {/* ── Capabilities ── */}
        <section className="section" id="capabilities">
          <div style={{ marginBottom: '1rem' }}>
            <span className="section-label">Architecture</span>
            <h2 className="section-heading">Core Capabilities</h2>
            <p className="section-desc">
              Built on Hermes Agent Core, powered by Gemini Pro, backed by Neo4j Knowledge Graphs.
            </p>
          </div>
          <CapabilityShowcase />
        </section>

        <div className="divider" />

        <Roadmap />

        <div className="divider" />

        <DownloadSection />
      </main>

      <Footer />

    </>
  );
}
