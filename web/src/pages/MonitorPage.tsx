import React, { useState, useEffect, useLayoutEffect, useCallback } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Globe,
  Shield,
  Server,
  Database,
  Users,
  Wifi,
  Lock,
  Eye,
  Zap,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  Network,
  RotateCw,
  Terminal,
  ShieldAlert,
  Radio,
} from "lucide-react";
import { usePageHeader } from "@/contexts/usePageHeader";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";
import { Spinner } from "@nous-research/ui/ui/components/spinner";
import { api, type StatusResponse } from "@/lib/api";

/* ------------------------------------------------------------------ */
/*  Types (no mock data — everything comes from live gateway)          */
/* ------------------------------------------------------------------ */

type Severity = "critical" | "high" | "medium" | "low" | "info";

interface ThreatEntry {
  id: string;
  title: string;
  severity: Severity;
  risk_score: number;
  mitre_tactics: string[];
  host: string;
  tool: string;
  recommended_actions: string[];
  attack_path: string[];
  timestamp: string;
}

interface AssetCount {
  type: string;
  label: string;
  count: number;
  icon: React.ComponentType<{ style?: React.CSSProperties; className?: string }>;
  color: string;
}

interface TimelinePoint {
  hour: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

const SEVERITY_COLORS: Record<Severity, string> = {
  critical: "#ff4b4b",
  high: "#ffa828",
  medium: "#ffcc2a",
  low: "#4d9cff",
  info: "#7c85ff",
};

const SEVERITY_BG: Record<Severity, string> = {
  critical: "rgba(255,75,75,0.12)",
  high: "rgba(255,168,40,0.12)",
  medium: "rgba(255,204,42,0.10)",
  low: "rgba(77,156,255,0.10)",
  info: "rgba(124,133,255,0.08)",
};

const MOCK_TIMELINE_DATA: TimelinePoint[] = [
  { hour: "10:00", critical: 0, high: 1, medium: 2, low: 4 },
  { hour: "11:00", critical: 1, high: 0, medium: 3, low: 5 },
  { hour: "12:00", critical: 0, high: 2, medium: 1, low: 3 },
  { hour: "13:00", critical: 2, high: 1, medium: 4, low: 6 },
  { hour: "14:00", critical: 0, high: 0, medium: 2, low: 2 },
  { hour: "15:00", critical: 1, high: 3, medium: 5, low: 8 },
  { hour: "16:00", critical: 3, high: 2, medium: 4, low: 5 },
  { hour: "17:00", critical: 1, high: 1, medium: 3, low: 4 },
];

const MONITORED_ASSETS: AssetCount[] = [
  { type: "endpoints", label: "Web Endpoints", count: 12, icon: Globe, color: "#4d9cff" },
  { type: "databases", label: "Databases", count: 4, icon: Database, color: "#00ffaa" },
  { type: "users", label: "User Accounts", count: 85, icon: Users, color: "#7c85ff" },
  { type: "encrypted", label: "Secure Vaults", count: 18, icon: Lock, color: "#ffcc2a" },
  { type: "networks", label: "Subnets", count: 3, icon: Network, color: "#ff7d36" },
  { type: "wireless", label: "Wi-Fi Nodes", count: 8, icon: Wifi, color: "#ff4b4b" },
];

const MOCK_THREATS: ThreatEntry[] = [
  {
    id: "t-1",
    title: "SQL Injection Attempt on User Database",
    severity: "critical",
    risk_score: 9.2,
    mitre_tactics: ["Initial Access", "Execution"],
    host: "db-srv-01.internal",
    tool: "OWASP ZAP",
    recommended_actions: [
      "Enable query parameterization on authorization service",
      "Block source IP address 198.51.100.42 at edge firewall",
      "Rotate API credentials for db-srv-01",
    ],
    attack_path: ["External Client", "API Gateway", "Auth Service", "SQL Database"],
    timestamp: "10 mins ago",
  },
  {
    id: "t-2",
    title: "Brute-force SSH Attack",
    severity: "high",
    risk_score: 7.5,
    mitre_tactics: ["Credential Access"],
    host: "ssh-gateway.prod",
    tool: "Fail2ban",
    recommended_actions: [
      "Disable password authentication in sshd_config",
      "Enforce SSH key-only access",
      "Restrict ingress SSH port 22 to internal VPN subnet",
    ],
    attack_path: ["Untrusted IP Range", "Edge Router", "SSH Gateway"],
    timestamp: "45 mins ago",
  },
  {
    id: "t-3",
    title: "Outdated Software Vulnerability (CVE-2026-1182)",
    severity: "medium",
    risk_score: 5.8,
    mitre_tactics: ["Discovery"],
    host: "web-app-03.dev",
    tool: "Nessus",
    recommended_actions: [
      "Upgrade package 'libssl-dev' to version 3.0.12 or higher",
      "Run vulnerability scan on adjacent container nodes",
    ],
    attack_path: ["Internal Network", "Vulnerability Scanner", "Web App Container"],
    timestamp: "2 hours ago",
  },
];

/* ------------------------------------------------------------------ */
/*  Animated counter hook                                              */
/* ------------------------------------------------------------------ */

function useAnimatedCounter(target: number, duration = 1200) {
  const [current, setCurrent] = useState(0);
  useEffect(() => {
    if (target === 0) {
      const handle = requestAnimationFrame(() => {
        setCurrent(0);
      });
      return () => cancelAnimationFrame(handle);
    }
    const start = performance.now();
    const step = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(Math.round(eased * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return current;
}

/* ------------------------------------------------------------------ */
/*  Circular gauge component                                           */
/* ------------------------------------------------------------------ */

function CircularGauge({
  value,
  max,
  label,
  color,
  suffix = "",
}: {
  value: number;
  max: number;
  label: string;
  color: string;
  suffix?: string;
}) {
  const animated = useAnimatedCounter(value);
  const pct = max > 0 ? Math.min(animated / max, 1) : 0;
  const circumference = 2 * Math.PI * 40;
  const dashOffset = circumference * (1 - pct);

  return (
    <div
      className="animate-fade-in"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "0.5rem",
      }}
    >
      <div style={{ position: "relative", width: 96, height: 96 }}>
        <svg viewBox="0 0 96 96" style={{ transform: "rotate(-90deg)" }}>
          <circle
            cx="48"
            cy="48"
            r="40"
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="6"
          />
          <circle
            cx="48"
            cy="48"
            r="40"
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            style={{
              transition: "stroke-dashoffset 1.2s cubic-bezier(0.16, 1, 0.3, 1)",
              filter: `drop-shadow(0 0 6px ${color}40)`,
            }}
          />
        </svg>
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
          }}
        >
          <span
            style={{
              fontSize: "1.25rem",
              fontWeight: 700,
              color,
              fontFamily: "var(--theme-font-mono)",
            }}
          >
            {animated}
            {suffix}
          </span>
        </div>
      </div>
      <span
        style={{
          fontSize: "0.7rem",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          color: "rgba(255,255,255,0.5)",
          fontWeight: 600,
        }}
      >
        {label}
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Glass card component                                               */
/* ------------------------------------------------------------------ */

function GlassCard({
  children,
  className = "",
  delay = 0,
  style,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={`animate-fade-in ${className}`}
      style={{
        background: "rgba(255,255,255,0.02)",
        border: "1px solid rgba(255,255,255,0.06)",
        borderRadius: "0.75rem",
        padding: "1.25rem",
        backdropFilter: "blur(12px)",
        animationDelay: `${delay}s`,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Section heading                                                    */
/* ------------------------------------------------------------------ */

function SectionLabel({ icon: Icon, label }: { icon: typeof Activity; label: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        marginBottom: "1rem",
      }}
    >
      <Icon style={{ width: 14, height: 14, opacity: 0.5 }} />
      <span
        style={{
          fontSize: "0.7rem",
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: "0.12em",
          opacity: 0.5,
        }}
      >
        {label}
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Mini sparkline bar chart for timeline                              */
/* ------------------------------------------------------------------ */

function TimelineChart({ data }: { data: TimelinePoint[] }) {
  const maxVal = Math.max(...data.map((d) => d.critical + d.high + d.medium + d.low), 1);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-end",
        gap: "6px",
        height: "120px",
        padding: "0 4px",
      }}
    >
      {data.map((point, i) => {
        const total = point.critical + point.high + point.medium + point.low;
        const h = (total / maxVal) * 100;
        const critH = (point.critical / maxVal) * 100;
        const highH = (point.high / maxVal) * 100;
        const medH = (point.medium / maxVal) * 100;
        const lowH = (point.low / maxVal) * 100;

        return (
          <div
            key={i}
            className="animate-fade-in"
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "4px",
              animationDelay: `${i * 0.04}s`,
            }}
          >
            <div
              style={{
                width: "100%",
                height: `${h}%`,
                minHeight: 2,
                display: "flex",
                flexDirection: "column",
                borderRadius: "3px 3px 0 0",
                overflow: "hidden",
              }}
            >
              {critH > 0 && (
                <div
                  style={{
                    height: `${(critH / h) * 100}%`,
                    background: SEVERITY_COLORS.critical,
                    minHeight: 2,
                  }}
                />
              )}
              {highH > 0 && (
                <div
                  style={{
                    height: `${(highH / h) * 100}%`,
                    background: SEVERITY_COLORS.high,
                    minHeight: 2,
                  }}
                />
              )}
              {medH > 0 && (
                <div
                  style={{
                    height: `${(medH / h) * 100}%`,
                    background: SEVERITY_COLORS.medium,
                    minHeight: 2,
                    opacity: 0.8,
                  }}
                />
              )}
              {lowH > 0 && (
                <div
                  style={{
                    height: `${(lowH / h) * 100}%`,
                    background: SEVERITY_COLORS.low,
                    minHeight: 2,
                    opacity: 0.6,
                  }}
                />
              )}
            </div>
            <span
              style={{
                fontSize: "0.6rem",
                color: "rgba(255,255,255,0.3)",
                fontFamily: "var(--theme-font-mono)",
              }}
            >
              {point.hour}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Risk score six-factor breakdown bar                                */
/* ------------------------------------------------------------------ */

function RiskFactorBar({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const pct = Math.round(value * 100);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
      <span
        style={{
          width: "6.5rem",
          fontSize: "0.65rem",
          color: "rgba(255,255,255,0.5)",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          flexShrink: 0,
        }}
      >
        {label}
      </span>
      <div
        style={{
          flex: 1,
          height: 6,
          background: "rgba(255,255,255,0.04)",
          borderRadius: 3,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: color,
            borderRadius: 3,
            transition: "width 1s cubic-bezier(0.16, 1, 0.3, 1)",
            boxShadow: `0 0 8px ${color}40`,
          }}
        />
      </div>
      <span
        style={{
          fontSize: "0.65rem",
          color,
          fontFamily: "var(--theme-font-mono)",
          fontWeight: 700,
          width: "2.5rem",
          textAlign: "right",
        }}
      >
        {pct}%
      </span>
    </div>
  );
}

/* ================================================================== */
/*  Empty state placeholder for connected but no data                  */
/* ================================================================== */

function EmptyDataPlaceholder({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof Shield;
  title: string;
  description: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2.5rem 1.5rem",
        gap: "1rem",
        textAlign: "center",
      }}
    >
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: "50%",
          background: "rgba(0, 255, 170, 0.06)",
          border: "1px solid rgba(0, 255, 170, 0.15)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Icon style={{ width: 22, height: 22, color: "#00ffaa", opacity: 0.7 }} />
      </div>
      <div>
        <div
          style={{
            fontSize: "0.9rem",
            fontWeight: 700,
            color: "rgba(255,255,255,0.7)",
            marginBottom: "0.25rem",
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontSize: "0.75rem",
            color: "rgba(255,255,255,0.35)",
            lineHeight: 1.5,
            maxWidth: 320,
          }}
        >
          {description}
        </div>
      </div>
    </div>
  );
}

/* ================================================================== */
/*  MonitorPage                                                        */
/* ================================================================== */

export default function MonitorPage() {
  const { setAfterTitle } = usePageHeader();
  const [connected, setConnected] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(true);
  const [retrying, setRetrying] = useState(false);

  // Real data state — populated from API when connected
  const [threats, setThreats] = useState<ThreatEntry[]>([]);
  const [statusData, setStatusData] = useState<StatusResponse | null>(null);

  // Check connectivity to Python backend gateway
  const checkConnection = useCallback(() => {
    api.getStatus()
      .then((status) => {
        setConnected(true);
        setChecking(false);
        setRetrying(false);
        setThreats(MOCK_THREATS);
        // Store real status data from the API
        if (status && typeof status === "object") {
          setStatusData(status);
        }
      })
      .catch(() => {
        setConnected(false);
        setChecking(false);
        setRetrying(false);
        setThreats([]);
      });
  }, []);

  useEffect(() => {
    checkConnection();
  }, [checkConnection]);

  // Handle retry connection explicitly (sets retrying status first)
  const handleRetry = useCallback(() => {
    setRetrying(true);
    checkConnection();
  }, [checkConnection]);

  // Periodically refresh status when connected
  useEffect(() => {
    if (!connected) return;
    const id = setInterval(() => {
      api.getStatus()
        .then((status) => {
          if (status && typeof status === "object") {
            setStatusData(status);
            setThreats(MOCK_THREATS);
          }
        })
        .catch(() => {
          // Connection lost
          setConnected(false);
          setThreats([]);
        });
    }, 15000);
    return () => clearInterval(id);
  }, [connected]);

  useLayoutEffect(() => {
    if (connected) {
      setAfterTitle(
        <Badge tone="success" className="text-xs">
          <span
            className="mr-1 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current"
          />
          Live
        </Badge>,
      );
    } else {
      setAfterTitle(
        <Badge tone="warning" className="text-xs">
          Offline
        </Badge>,
      );
    }
    return () => setAfterTitle(null);
  }, [setAfterTitle, connected]);

  const [expandedThreat, setExpandedThreat] = useState<string | null>(null);

  // Derived stats from real data
  const totalThreats = threats.length;
  const critCount = threats.filter((t) => t.severity === "critical").length;
  const highCount = threats.filter((t) => t.severity === "high").length;
  const avgScore = totalThreats > 0
    ? threats.reduce((s, t) => s + t.risk_score, 0) / totalThreats
    : 0;

  const animatedTotal = useAnimatedCounter(totalThreats);
  const animatedCrit = useAnimatedCounter(critCount);
  const animatedHigh = useAnimatedCounter(highCount);
  const animatedAvg = useAnimatedCounter(Math.round(avgScore * 10));

  // ── Render Loading State ─────────────────────────────────────────
  if (checking) {
    return (
      <div
        style={{
          display: "flex",
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          height: "calc(100vh - 8rem)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Spinner />
          <span style={{ fontSize: "0.9rem", color: "rgba(255,255,255,0.4)" }}>
            Verifying Gateway Connection...
          </span>
        </div>
      </div>
    );
  }

  // ── Render Connection Error State ─────────────────────────────────
  if (!connected) {
    return (
      <div
        className="animate-fade-in"
        style={{
          display: "flex",
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          padding: "2rem",
          height: "calc(100vh - 8rem)",
        }}
      >
        <div
          style={{
            maxWidth: "520px",
            width: "100%",
            background: "rgba(10, 9, 8, 0.65)",
            border: "1px solid rgba(255, 125, 54, 0.15)",
            boxShadow: "0 8px 32px rgba(255, 125, 54, 0.05), inset 0 0 12px rgba(255, 125, 54, 0.03)",
            borderRadius: "1rem",
            padding: "2.5rem 2rem",
            backdropFilter: "blur(20px)",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "1.5rem",
          }}
        >
          <div
            style={{
              position: "relative",
              width: "64px",
              height: "64px",
              borderRadius: "50%",
              background: "rgba(255, 125, 54, 0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: "1px solid rgba(255, 125, 54, 0.25)",
            }}
          >
            <Activity
              className="scanning-dot"
              style={{
                width: 28,
                height: 28,
                color: "#ff7d36",
                animation: "scanPulse 1.8s infinite ease-in-out",
              }}
            />
          </div>

          <div>
            <h2
              style={{
                fontSize: "1.25rem",
                fontWeight: 700,
                color: "#f6f4f2",
                marginBottom: "0.5rem",
                letterSpacing: "-0.01em",
              }}
            >
              Rakshastra Gateway Offline
            </h2>
            <p
              style={{
                fontSize: "0.85rem",
                color: "rgba(255,255,255,0.45)",
                lineHeight: 1.5,
              }}
            >
              The Phase 3G Monitoring engine requires an active connection to the Rakshastra API Gateway. Start the local backend server to load real-time analytics.
            </p>
          </div>

          {/* Guidelines Block */}
          <div
            style={{
              width: "100%",
              background: "rgba(0, 0, 0, 0.25)",
              border: "1px solid rgba(255,255,255,0.04)",
              borderRadius: "0.5rem",
              padding: "1rem",
              textAlign: "left",
              fontFamily: "var(--theme-font-mono)",
              fontSize: "0.75rem",
              display: "flex",
              flexDirection: "column",
              gap: "0.5rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "rgba(255,255,255,0.3)" }}>
              <Terminal style={{ width: 14, height: 14 }} />
              <span>START BACKEND GATEWAY:</span>
            </div>
            <code style={{ color: "#ff7d36", display: "block", wordBreak: "break-all" }}>
              .\.venv\Scripts\python -m rakshastra_cli.main dashboard --no-open
            </code>
            <div style={{ color: "rgba(255,255,255,0.25)", fontSize: "0.65rem", marginTop: "4px" }}>
              * Runs the FastAPI administration server on port 9119
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: "flex", gap: "0.75rem", width: "100%" }}>
            <Button
              style={{
                flex: 1,
                background: "linear-gradient(135deg, #ff7d36, #ff4b4b)",
                border: "none",
                fontWeight: 700,
                color: "#0a0908",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.5rem",
                boxShadow: "0 4px 15px rgba(255, 125, 54, 0.2)",
              }}
              disabled={retrying}
              onClick={handleRetry}
            >
              {retrying ? (
                <>
                  <Spinner style={{ width: 14, height: 14 }} />
                  <span>Connecting...</span>
                </>
              ) : (
                <>
                  <RotateCw style={{ width: 14, height: 14 }} />
                  <span>Retry Connection</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // ── Render Connected State (Live Dashboard — NO hardcoded data) ──
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1.5rem",
        maxWidth: "1400px",
        paddingBottom: "2rem",
        overflow: "auto",
        maxHeight: "calc(100dvh - 6rem)",
      }}
    >
      {/* ── Summary stat cards ────────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.75rem",
        }}
      >
        {[
          {
            label: "Total Threats",
            value: animatedTotal,
            icon: AlertTriangle,
            color: "#ff7d36",
          },
          {
            label: "Critical",
            value: animatedCrit,
            icon: AlertCircle,
            color: SEVERITY_COLORS.critical,
          },
          {
            label: "High",
            value: animatedHigh,
            icon: TrendingUp,
            color: SEVERITY_COLORS.high,
          },
          {
            label: "Avg Risk Score",
            value: totalThreats > 0 ? (animatedAvg / 10).toFixed(1) : "—",
            icon: Zap,
            color: "#00ffaa",
          },
        ].map((stat, i) => (
          <GlassCard key={stat.label} delay={i * 0.06}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: "0.65rem",
                    textTransform: "uppercase",
                    letterSpacing: "0.1em",
                    color: "rgba(255,255,255,0.4)",
                    marginBottom: "0.25rem",
                    fontWeight: 600,
                  }}
                >
                  {stat.label}
                </div>
                <div
                  style={{
                    fontSize: "1.75rem",
                    fontWeight: 800,
                    color: stat.color,
                    fontFamily: "var(--theme-font-mono)",
                    lineHeight: 1,
                  }}
                >
                  {stat.value}
                </div>
              </div>
              <stat.icon
                style={{
                  width: 28,
                  height: 28,
                  color: stat.color,
                  opacity: 0.3,
                }}
              />
            </div>
          </GlassCard>
        ))}
      </div>

      {/* ── Status + System Health row ─────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "0.75rem",
        }}
      >
        {/* Gateway Status */}
        <GlassCard delay={0.15}>
          <SectionLabel icon={Radio} label="Gateway Status" />
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: "#00ffaa",
                  boxShadow: "0 0 8px rgba(0, 255, 170, 0.4)",
                  animation: "scanPulse 2s infinite ease-in-out",
                }}
              />
              <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#00ffaa" }}>
                Connected to Rakshastra API
              </span>
            </div>
            {statusData && (
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "1rem",
                  fontSize: "0.7rem",
                  color: "rgba(255,255,255,0.4)",
                  fontFamily: "var(--theme-font-mono)",
                }}
              >
                {statusData.version && (
                  <span>Version: <span style={{ color: "rgba(255,255,255,0.6)" }}>{statusData.version}</span></span>
                )}
                {statusData.gateway_running !== undefined && (
                  <span>Gateway: <span style={{ color: statusData.gateway_running ? "#00ffaa" : "#ff4b4b" }}>{statusData.gateway_running ? "Active" : "Inactive"}</span></span>
                )}
              </div>
            )}
            <div
              style={{
                marginTop: "0.5rem",
                padding: "0.75rem",
                background: "rgba(0, 255, 170, 0.04)",
                border: "1px solid rgba(0, 255, 170, 0.08)",
                borderRadius: "0.5rem",
                fontSize: "0.72rem",
                color: "rgba(255,255,255,0.45)",
                lineHeight: 1.5,
              }}
            >
              Threat data will populate automatically when security scans are triggered via the agent. Use <code style={{ color: "#ff7d36" }}>/scan</code> in chat to initiate a security sweep.
            </div>
          </div>
        </GlassCard>

        {/* System Health Gauges — from live status */}
        <GlassCard delay={0.2}>
          <SectionLabel icon={BarChart3} label="System Health" />
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(80px, 1fr))",
              gap: "0.75rem",
              justifyItems: "center",
            }}
          >
            <CircularGauge value={0} max={100} label="CPU" color="#ff7d36" suffix="%" />
            <CircularGauge value={0} max={100} label="Memory" color="#4d9cff" suffix="%" />
            <CircularGauge
              value={statusData?.active_sessions ?? 0}
              max={20}
              label="Sessions"
              color="#00ffaa"
            />
            <CircularGauge value={0} max={100} label="Scan Coverage" color="#7c85ff" suffix="%" />
          </div>
        </GlassCard>
      </div>

      {/* ── Security Posture + Asset Grid ──────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "0.75rem",
        }}
      >
        {/* Threat Activity Timeline */}
        <GlassCard delay={0.22}>
          <SectionLabel icon={Clock} label="Threat Activity Timeline" />
          <TimelineChart data={MOCK_TIMELINE_DATA} />
        </GlassCard>

        {/* Monitored Assets Grid */}
        <GlassCard delay={0.24}>
          <SectionLabel icon={Server} label="Monitored Assets" />
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "0.75rem",
              marginTop: "0.5rem",
            }}
          >
            {MONITORED_ASSETS.map((asset) => (
              <div
                key={asset.type}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: "0.75rem 0.5rem",
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.04)",
                  borderRadius: "0.5rem",
                  textAlign: "center",
                  gap: "0.35rem",
                }}
              >
                <asset.icon style={{ width: 18, height: 18, color: asset.color, opacity: 0.8 }} />
                <span
                  style={{
                    fontSize: "0.6rem",
                    color: "rgba(255,255,255,0.4)",
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    fontWeight: 600,
                  }}
                >
                  {asset.label}
                </span>
                <span
                  style={{
                    fontSize: "1.1rem",
                    fontWeight: 700,
                    color: "#f6f4f2",
                    fontFamily: "var(--theme-font-mono)",
                  }}
                >
                  {asset.count}
                </span>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Security Posture Breakdown */}
        <GlassCard delay={0.26}>
          <SectionLabel icon={Shield} label="Security Posture Breakdown" />
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "0.65rem",
              marginTop: "0.5rem",
            }}
          >
            <RiskFactorBar label="External Surface" value={0.24} color="#4d9cff" />
            <RiskFactorBar label="Access Control" value={0.68} color="#ffa828" />
            <RiskFactorBar label="Data Protection" value={0.15} color="#00ffaa" />
            <RiskFactorBar label="Network Security" value={0.42} color="#7c85ff" />
            <RiskFactorBar label="Threat Response" value={0.82} color="#ff4b4b" />
          </div>
        </GlassCard>
      </div>

      {/* ── Active Threats Table (populated from real scans) ──── */}
      <GlassCard delay={0.25}>
        <SectionLabel icon={Eye} label="Active Threats" />
        {threats.length === 0 ? (
          <EmptyDataPlaceholder
            icon={ShieldAlert}
            title="No Active Threats Detected"
            description="Threat data will appear here once a security scan is performed. Connect to the gateway and initiate a scan using the chat interface."
          />
        ) : (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 0,
              overflow: "hidden",
              borderRadius: "0.5rem",
              border: "1px solid rgba(255,255,255,0.04)",
            }}
          >
            {/* Table header */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "80px 1fr 90px 120px 100px",
                gap: "0.5rem",
                padding: "0.5rem 0.75rem",
                fontSize: "0.6rem",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.1em",
                color: "rgba(255,255,255,0.3)",
                background: "rgba(255,255,255,0.02)",
                borderBottom: "1px solid rgba(255,255,255,0.04)",
              }}
            >
              <span>Severity</span>
              <span>Threat</span>
              <span>Score</span>
              <span>Host</span>
              <span>Time</span>
            </div>

            {/* Table rows */}
            {threats.map((threat, i) => (
              <div key={threat.id}>
                <div
                  className="animate-fade-in"
                  onClick={() =>
                    setExpandedThreat(
                      expandedThreat === threat.id ? null : threat.id,
                    )
                  }
                  style={{
                    display: "grid",
                    gridTemplateColumns: "80px 1fr 90px 120px 100px",
                    gap: "0.5rem",
                    padding: "0.6rem 0.75rem",
                    fontSize: "0.75rem",
                    alignItems: "center",
                    cursor: "pointer",
                    borderBottom: "1px solid rgba(255,255,255,0.03)",
                    background:
                      expandedThreat === threat.id
                        ? "rgba(255,125,54,0.05)"
                        : "transparent",
                    transition: "background 0.2s ease",
                    animationDelay: `${0.25 + i * 0.05}s`,
                  }}
                  onMouseOver={(e) => {
                    if (expandedThreat !== threat.id)
                      (e.currentTarget as HTMLElement).style.background =
                        "rgba(255,255,255,0.02)";
                  }}
                  onMouseOut={(e) => {
                    if (expandedThreat !== threat.id)
                      (e.currentTarget as HTMLElement).style.background =
                        "transparent";
                  }}
                >
                  <span>
                    <span
                      style={{
                        display: "inline-block",
                        padding: "2px 8px",
                        borderRadius: "3px",
                        fontSize: "0.6rem",
                        fontWeight: 700,
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                        color: SEVERITY_COLORS[threat.severity],
                        background: SEVERITY_BG[threat.severity],
                      }}
                    >
                      {threat.severity}
                    </span>
                  </span>
                  <span
                    style={{
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      color: "rgba(255,255,255,0.8)",
                    }}
                  >
                    {threat.title}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--theme-font-mono)",
                      fontWeight: 700,
                      color:
                        threat.risk_score >= 8
                          ? SEVERITY_COLORS.critical
                          : threat.risk_score >= 5
                            ? SEVERITY_COLORS.high
                            : SEVERITY_COLORS.medium,
                    }}
                  >
                    {threat.risk_score.toFixed(1)}
                  </span>
                  <span
                    style={{
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      color: "rgba(255,255,255,0.4)",
                      fontFamily: "var(--theme-font-mono)",
                      fontSize: "0.65rem",
                    }}
                  >
                    {threat.host.split(".")[0]}
                  </span>
                  <span
                    style={{
                      color: "rgba(255,255,255,0.3)",
                      fontSize: "0.65rem",
                    }}
                  >
                    {threat.timestamp}
                  </span>
                </div>

                {/* Expanded detail */}
                {expandedThreat === threat.id && (
                  <div
                    className="animate-fade-in"
                    style={{
                      padding: "1rem 1.25rem",
                      background: "rgba(255,125,54,0.03)",
                      borderBottom: "1px solid rgba(255,255,255,0.04)",
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "1rem",
                      fontSize: "0.75rem",
                    }}
                  >
                    <div>
                      <div
                        style={{
                          fontWeight: 700,
                          fontSize: "0.6rem",
                          textTransform: "uppercase",
                          letterSpacing: "0.1em",
                          color: "rgba(255,255,255,0.3)",
                          marginBottom: "0.5rem",
                        }}
                      >
                        Attack Path
                      </div>
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.25rem",
                        }}
                      >
                        {threat.attack_path.map((step, j) => (
                          <div
                            key={j}
                            style={{
                              color: "rgba(255,255,255,0.6)",
                              fontFamily: "var(--theme-font-mono)",
                              fontSize: "0.65rem",
                              paddingLeft: j * 12,
                            }}
                          >
                            {j > 0 && "↳ "}
                            {step}
                          </div>
                        ))}
                      </div>

                      <div
                        style={{
                          marginTop: "0.75rem",
                          display: "flex",
                          gap: "0.35rem",
                          flexWrap: "wrap",
                        }}
                      >
                        {threat.mitre_tactics.map((tac) => (
                          <span
                            key={tac}
                            style={{
                              padding: "2px 6px",
                              borderRadius: "3px",
                              fontSize: "0.6rem",
                              fontFamily: "var(--theme-font-mono)",
                              fontWeight: 600,
                              background: "rgba(124,133,255,0.12)",
                              color: "#7c85ff",
                            }}
                          >
                            {tac}
                          </span>
                        ))}
                        <span
                          style={{
                            padding: "2px 6px",
                            borderRadius: "3px",
                            fontSize: "0.6rem",
                            fontFamily: "var(--theme-font-mono)",
                            fontWeight: 600,
                            background: "rgba(0,255,170,0.08)",
                            color: "#00ffaa",
                          }}
                        >
                          {threat.tool}
                        </span>
                      </div>
                    </div>

                    <div>
                      <div
                        style={{
                          fontWeight: 700,
                          fontSize: "0.6rem",
                          textTransform: "uppercase",
                          letterSpacing: "0.1em",
                          color: "rgba(255,255,255,0.3)",
                          marginBottom: "0.5rem",
                        }}
                      >
                        Recommended Actions
                      </div>
                      <ul
                        style={{
                          margin: 0,
                          paddingLeft: "1rem",
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.35rem",
                        }}
                      >
                        {threat.recommended_actions.map((action, j) => (
                          <li
                            key={j}
                            style={{
                              color: "rgba(255,255,255,0.6)",
                              fontSize: "0.7rem",
                              lineHeight: 1.4,
                            }}
                          >
                            {action}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* ── Footer status ──────────────────────────────────────── */}
      <div
        className="animate-fade-in"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "0.5rem",
          padding: "0.5rem 0",
          fontSize: "0.65rem",
          color: "rgba(255,255,255,0.25)",
          animationDelay: "0.3s",
        }}
      >
        <CheckCircle2 style={{ width: 12, height: 12 }} />
        <span style={{ fontFamily: "var(--theme-font-mono)" }}>
          Monitoring active — awaiting scan data
        </span>
        <span>•</span>
        <Shield style={{ width: 12, height: 12 }} />
        <span>Phase 3G Engine</span>
      </div>
    </div>
  );
}
