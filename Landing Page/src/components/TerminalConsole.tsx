"use client";

import React, { useState, useEffect, useRef } from "react";

interface LogLine {
  id: string;
  type: "system" | "success" | "info" | "warning" | "danger" | "prompt";
  text: string;
}

const logTemplates = [
  { type: "info", text: "[CRAWLER] Spider #ID scanning PLATFORM/CHANNEL..." },
  { type: "info", text: "[CRAWLER] Thread #ID: Analyzing post #POST for token matches..." },
  { type: "warning", text: '[NLP] Semantic analysis: "TEXT_CONTENT"' },
  { type: "danger", text: "[ALERT] HIGH CONFIDENCE — Keyword: KEYWORD (CONFIDENCE%)" },
  { type: "system", text: "[TRIANGULATE] Resolving IP and device fingerprints..." },
  { type: "success", text: "[TRIANGULATE] Location: LOCATION | IP: IP_ADDR | ISP: ISP_NAME" },
  { type: "system", text: "[GRAPH] Querying Neo4j — cross-referencing handles..." },
  { type: "success", text: "[NEO4J] Link: BOT_NAME → IG_NAME via PHONE_NUM (MATCH_CONF%)" },
  { type: "system", text: "[DISPATCH] Compiling incident packet for LEA..." },
  { type: "success", text: "[GATEWAY] Alert digest dispatched to Central Command." },
];

const platforms = ["Telegram", "WhatsApp", "Instagram", "Instagram Stories"];
const channels = ["@SpeedyNarcoticsIN", "@DirectMedsExpress", "@MedsExpress_IN", "@EcstasySupplies99", "@LSD_PartyStamps"];
const keywords = ["MDMA", "LSD", "Mephedrone", "Ecstasy", "party pills", "synthetic drugs"];
const locations = ["Delhi NCR", "Mumbai", "Bengaluru", "Chennai", "Hyderabad", "Pune"];
const rawIps = ["103.45.210.4", "182.72.19.143", "202.164.44.82", "122.160.220.10"];
const isps = ["Bharti Airtel", "Reliance Jio", "Vodafone Idea", "BSNL"];
const botNames = ["@NarcoFastBot", "@DirectMedsBot", "@ExpressPillBot"];
const igNames = ["@GlowVibesParty", "@NightOutDeals", "@NeonTripsIndia"];
const phones = ["+91 98932 XXXXX", "+91 70008 XXXXX", "+91 88710 XXXXX"];
const texts = [
  "party stamps for weekend dm for rates",
  "LSD blotters best quality imported",
  "ecstasy pills stocks refilled cod available",
  "Mephedrone rate card: 1g, 2g, 5g",
];

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

export default function TerminalConsole() {
  const [logs, setLogs] = useState<LogLine[]>([
    { id: "init-1", type: "system", text: "$ rakshastra-agent start --mode=production" },
    { id: "init-2", type: "system", text: "[CORE] Initializing Hermes Agent Core v1.0.0..." },
    { id: "init-3", type: "success", text: "[CORE] GCP Cloud Run container online." },
    { id: "init-4", type: "success", text: "[CORE] Gemini API handshake complete." },
    { id: "init-5", type: "info", text: "[CORE] Loading keyword database [MDMA, LSD, Mephedrone, ...]" },
    { id: "init-6", type: "prompt", text: "[CORE] All systems nominal. Starting crawlers..." },
  ]);

  const [stats, setStats] = useState({ crawlers: 148, flagged: 1402, identities: 418, alerts: 92 });
  const [flashStat, setFlashStat] = useState<string | null>(null);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [logs]);

  useEffect(() => {
    let timer: NodeJS.Timeout;

    function next() {
      timer = setTimeout(() => {
        const t = pick(logTemplates);
        const text = t.text
          .replace("#ID", String(Math.floor(Math.random() * 9000) + 1000))
          .replace("PLATFORM", pick(platforms))
          .replace("CHANNEL", pick(channels))
          .replace("#POST", String(Math.floor(Math.random() * 500) + 1))
          .replace("TEXT_CONTENT", pick(texts))
          .replace("KEYWORD", pick(keywords))
          .replace("CONFIDENCE", (Math.random() * 15 + 85).toFixed(1))
          .replace("LOCATION", pick(locations))
          .replace("IP_ADDR", pick(rawIps))
          .replace("ISP_NAME", pick(isps))
          .replace("BOT_NAME", pick(botNames))
          .replace("IG_NAME", pick(igNames))
          .replace("PHONE_NUM", pick(phones))
          .replace("MATCH_CONF", (Math.random() * 10 + 90).toFixed(1));

        setLogs((prev) => {
          const n = [...prev, { id: Math.random().toString(36).slice(2, 9), type: t.type as LogLine["type"], text }];
          return n.length > 40 ? n.slice(n.length - 40) : n;
        });

        const r = Math.random();
        setStats((s) => {
          const ns = { ...s };
          if (r < 0.05) { ns.crawlers += Math.random() > 0.5 ? 1 : -1; ns.crawlers = Math.max(140, Math.min(160, ns.crawlers)); }
          if (r > 0.05 && r < 0.2) { ns.flagged += Math.ceil(Math.random() * 2); setFlashStat("flagged"); setTimeout(() => setFlashStat(null), 400); }
          if (r > 0.2 && r < 0.28) { ns.identities += 1; setFlashStat("identities"); setTimeout(() => setFlashStat(null), 400); }
          if (r > 0.9) { ns.alerts += 1; setFlashStat("alerts"); setTimeout(() => setFlashStat(null), 400); }
          return ns;
        });

        next();
      }, Math.random() * 1500 + 800);
    }

    next();
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="console-container">
      <div className="console-layout">
        <div className="console-sidebar">
          <span className="sidebar-title">Agent Metrics</span>
          {[
            { key: "crawlers", label: "Active Crawlers", value: stats.crawlers },
            { key: "flagged", label: "Flagged Channels", value: stats.flagged.toLocaleString() },
            { key: "identities", label: "Identities Mapped", value: stats.identities },
            { key: "alerts", label: "Alerts Dispatched", value: stats.alerts },
          ].map((s) => (
            <div className="stat-item" key={s.key}>
              <span className="stat-label">{s.label}</span>
              <span className={`stat-value${flashStat === s.key ? " flash" : ""}`}>{s.value}</span>
            </div>
          ))}
        </div>

        <div className="console-main">
          <div className="console-toolbar">
            <div className="toolbar-dots">
              <span className="toolbar-dot red" />
              <span className="toolbar-dot yellow" />
              <span className="toolbar-dot green" />
            </div>
            <span className="toolbar-label">rakshastra-agent@core:~</span>
          </div>

          <div className="console-body" ref={bodyRef}>
            {logs.map((log) => (
              <div key={log.id} className={`log-line ${log.type}`}>{log.text}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
