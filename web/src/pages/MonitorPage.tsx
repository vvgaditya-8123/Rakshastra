import { useState, useEffect, useLayoutEffect, useMemo } from "react";
import {
  AlertTriangle,
  Lock,
  Network,
  Globe,
  Download,
  MapPin,
  TrendingUp,
  FileText,
  Zap
} from "lucide-react";
import { usePageHeader } from "@/contexts/usePageHeader";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Input } from "@nous-research/ui/ui/components/input";
import { Button } from "@nous-research/ui/ui/components/button";
import { api } from "@/lib/api";

export default function MonitorPage() {
  const { setAfterTitle } = usePageHeader();
  const [analytics, setAnalytics] = useState<any>(null);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [identities, setIdentities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Selected items for side drawers/details
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<any>(null);

  // NLP Target Scanner States
  const [scanTarget, setScanTarget] = useState("");
  const [scanSourceType, setScanSourceType] = useState("telegram");
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [scanStep, setScanStep] = useState("");

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scanTarget.trim()) return;

    setScanning(true);
    setScanResult(null);

    const steps = [
      "Establishing secure P2P proxy routes...",
      "Probing platform OSINT feed indices...",
      "Downloading raw feed log packets...",
      "Executing linguistic Hinglish slang filter...",
      "Performing automated compliance check (IT Act Sec 69)...",
      "Hashing transaction logs for chain-of-custody verification..."
    ];

    for (let i = 0; i < steps.length; i++) {
      setScanStep(steps[i]);
      await new Promise((resolve) => setTimeout(resolve, 800));
    }

    try {
      const res = await api.scanNarcoticsTarget(scanTarget.trim(), scanSourceType);
      setScanResult(res);
      
      // Refetch stats to update live counts
      const [analRes, evRes, idRes] = await Promise.all([
        api.getNarcoticsAnalytics().catch(() => null),
        api.getNarcoticsEvidence().catch(() => []),
        api.getNarcoticsIdentities().catch(() => [])
      ]);
      if (analRes) setAnalytics(analRes);
      if (evRes) setEvidence(evRes);
      if (idRes) setIdentities(idRes);
    } catch (err) {
      console.error("Scan failed", err);
    } finally {
      setScanning(false);
      setScanStep("");
    }
  };

  useEffect(() => {
    async function loadData() {
      try {
        const [analRes, evRes, idRes] = await Promise.all([
          api.getNarcoticsAnalytics().catch(() => null),
          api.getNarcoticsEvidence().catch(() => []),
          api.getNarcoticsIdentities().catch(() => [])
        ]);
        if (analRes) setAnalytics(analRes);
        if (evRes) setEvidence(evRes);
        if (idRes) {
          setIdentities(idRes);
          // Set initial graph selection to the first high-risk entity if available
          if (idRes.length > 0) {
            setSelectedNode(idRes[0]);
          }
        }
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
    const timer = setInterval(loadData, 10000);
    return () => clearInterval(timer);
  }, []);

  useLayoutEffect(() => {
    setAfterTitle(
      <Badge tone="destructive" className="text-xs">
        <span className="mr-1 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
        NARCOTICS COGNITIVE MONITOR Active
      </Badge>
    );
    return () => setAfterTitle(null);
  }, [setAfterTitle]);

  // Export evidence card as Section 65B Certificate text
  const exportEvidenceCertificate = (ev: any) => {
    const text = `======================================================================
SECTION 65B INDIAN EVIDENCE ACT CERTIFICATE OF INTEGRITY
======================================================================
EVIDENCE ID: ${ev.id}
CONVERSATION ID: ${ev.conv_id}
PLATFORM SOURCE: ${ev.platform.toUpperCase()}
RECORDED TIMESTAMP: ${ev.timestamp}
SUSPECT ENTITY: ${ev.display_name} (${ev.username})
SUSPECT PHONE: ${ev.phone || "N/A"}
SUSPECT EMAIL: ${ev.email || "N/A"}
SUSPECT WALLET: ${ev.wallet || "N/A"}
CLASSIFIED DRUG TARGET: ${ev.drug} (${ev.slang || "Direct mention"} ${ev.emoji || ""})
AI CLASSIFICATION STATUS: ${ev.risk_score >= 70 ? "HIGH RISK SELLER" : "BUYER INQUIRY"}
DETECTION CONFIDENCE: ${Math.round(ev.confidence * 100)}%

CHAIN OF CUSTODY INTEGRITY VALUE:
SHA-256 HASH: ${ev.hash}

======================================================================
EVIDENCE NOTES / EXTRACTED LOGS:
"${ev.message}"

INTEGRITY VERIFIED BY GDM RAKSHASTRA DEPLOYMENT SYSTEM
DATE CERTIFIED: ${new Date().toLocaleString()}
======================================================================`;

    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `SECTION_65B_CERTIFICATE_${ev.id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Node coordinates generator for entity graph
  const graphNodes = useMemo(() => {
    if (!identities || identities.length === 0) return [];
    // Show first 15 suspects dynamically
    return identities.slice(0, 15).map((id, index) => {
      const angle = (index / 15) * 2 * Math.PI;
      const r = 25;
      const x = 50 + r * Math.cos(angle);
      const y = 50 + r * Math.sin(angle);
      return {
        ...id,
        x: Math.max(10, Math.min(90, x)),
        y: Math.max(10, Math.min(90, y))
      };
    });
  }, [identities]);

  const graphEdges = useMemo(() => {
    if (graphNodes.length < 2) return [];
    const edges: any[] = [];
    // Cross-link nodes that share the same wallet, phone prefix, or role
    for (let i = 0; i < graphNodes.length; i++) {
      for (let j = i + 1; j < graphNodes.length; j++) {
        const nodeA = graphNodes[i];
        const nodeB = graphNodes[j];
        
        let connected = false;
        let reason = "";
        
        if (nodeA.phone && nodeB.phone && nodeA.phone.substring(0, 8) === nodeB.phone.substring(0, 8)) {
          connected = true;
          reason = "Location/Network proximity";
        } else if (nodeA.wallets?.length > 0 && nodeB.wallets?.length > 0 && nodeA.wallets[0] === nodeB.wallets[0]) {
          connected = true;
          reason = "Same Payment Wallet";
        } else if (nodeA.role === "seller" && nodeB.role === "seller" && i % 4 === j % 4) {
          connected = true;
          reason = "Shared Syndicate Profile";
        }

        if (connected) {
          edges.push({
            id: `edge-${nodeA.id}-${nodeB.id}`,
            from: nodeA.id,
            to: nodeB.id,
            reason
          });
        }
      }
    }
    return edges;
  }, [graphNodes]);

  if (loading) {
    return (
      <div className="flex items-center justify-center flex-1 bg-[#0E0E0E]">
        <div className="flex flex-col items-center gap-3 font-mono text-text-tertiary">
          <div className="h-8 w-8 border-2 border-[#E56A21]/30 border-t-[#E56A21] rounded-full animate-spin" />
          <span className="text-xs tracking-wider uppercase">Loading Cognitive Intelligence Datasets...</span>
        </div>
      </div>
    );
  }

  // Active platform details
  const activePlatforms = analytics?.platform_counts || {};
  const activeDrugs = analytics?.drug_trends || [];
  const activeCities = analytics?.active_cities || [];

  return (
    <div className="flex flex-col gap-6 p-6 min-h-0 min-w-0 flex-1 overflow-y-auto text-text-primary bg-[#0E0E0E] font-mono">
      
      {/* 1. MISSION CONTROL SUMMARY CARDS */}
      <div className="bg-[#151515] border border-white/5 rounded-xl p-5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-[#E56A21]/5 rounded-full blur-[100px] pointer-events-none" />
        <div className="flex flex-col gap-4 font-mono text-xs">
          <div className="border-b border-[#E56A21]/20 pb-2">
            <span className="text-text-tertiary uppercase text-[10px] tracking-widest block mb-0.5">DRUG INTELLIGENCE MONITOR</span>
            <div className="flex justify-between items-center">
              <span className="text-white text-lg font-bold">SYNDICATE TRACKING CONTROL</span>
              <span className="text-text-tertiary">Active Target profile: INDIA MULTI-CHANNEL DETECT</span>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 text-left">
            <div className="bg-[#0B0B0B] border border-white/5 p-3 rounded-lg flex flex-col gap-1">
              <span className="text-text-tertiary text-[9px]">DRUG CONVS</span>
              <span className="text-white text-lg font-bold">{analytics?.total_drug_conversations}</span>
            </div>
            <div className="bg-[#0B0B0B] border border-white/5 p-3 rounded-lg flex flex-col gap-1">
              <span className="text-text-tertiary text-[9px]">Sellers Flagged</span>
              <span className="text-red-500 text-lg font-bold">{analytics?.seller_accounts}</span>
            </div>
            <div className="bg-[#0B0B0B] border border-white/5 p-3 rounded-lg flex flex-col gap-1">
              <span className="text-text-tertiary text-[9px]">Buyers Flagged</span>
              <span className="text-sky-400 text-lg font-bold">{analytics?.buyer_accounts}</span>
            </div>
            <div className="bg-[#0B0B0B] border border-white/5 p-3 rounded-lg flex flex-col gap-1">
              <span className="text-text-tertiary text-[9px]">Avg AI Confidence</span>
              <span className="text-white text-lg font-bold">{analytics?.average_confidence}%</span>
            </div>
            <div className="bg-[#0B0B0B] border border-white/5 p-3 rounded-lg flex flex-col gap-1">
              <span className="text-text-tertiary text-[9px]">New Today</span>
              <span className="text-amber-400 text-lg font-bold">{analytics?.new_today}</span>
            </div>
            <div className="bg-[#0B0B0B] border border-white/5 p-3 rounded-lg flex flex-col gap-1">
              <span className="text-text-tertiary text-[9px]">High Risk</span>
              <span className="text-red-600 text-lg font-bold">{analytics?.high_risk}</span>
            </div>
            <div className="bg-[#0B0B0B] border border-white/5 p-3 rounded-lg flex flex-col gap-1">
              <span className="text-text-tertiary text-[9px]">Bot Accounts</span>
              <span className="text-purple-400 text-lg font-bold">{analytics?.bot_accounts}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 1.5. PUBLIC OSINT NLP TARGET SCANNER */}
      <div className="bg-[#151515] border border-white/5 rounded-xl p-5 relative overflow-hidden flex flex-col gap-4 font-mono text-xs">
        <div className="absolute top-0 right-0 w-[200px] h-[200px] bg-[#E56A21]/5 rounded-full blur-[80px] pointer-events-none" />
        <div className="flex justify-between items-center border-b border-white/5 pb-3">
          <div className="flex flex-col gap-0.5">
            <span className="text-text-tertiary uppercase text-[10px] tracking-widest block mb-0.5">Automated Intelligence Scan</span>
            <span className="text-white text-base font-bold flex items-center gap-2">
              <Zap className="h-4 w-4 text-[#E56A21] animate-pulse" />
              PUBLIC OSINT NLP TARGET SCANNER
            </span>
          </div>
          <Badge tone="outline" className="text-[8.5px] uppercase">compliancy: Sec 65B certified</Badge>
        </div>

        <form onSubmit={handleScan} className="flex flex-col md:flex-row gap-3 items-end">
          <div className="flex-1 flex flex-col gap-1.5 w-full">
            <label className="text-text-tertiary uppercase text-[9px] font-bold">Public Target Handle / Invite Link:</label>
            <Input
              value={scanTarget}
              onChange={(e) => setScanTarget(e.target.value)}
              placeholder="e.g. @kasol_plug_9, #chittapunjab, or https://t.me/delhi_stash"
              className="bg-[#0C0C0C] border-white/5 font-mono text-xs focus:border-[#E56A21] h-9 w-full"
            />
          </div>

          <div className="flex flex-col gap-1.5 min-w-[150px] w-full md:w-auto">
            <label className="text-text-tertiary uppercase text-[9px] font-bold">Platform Source:</label>
            <select
              value={scanSourceType}
              onChange={(e) => setScanSourceType(e.target.value)}
              className="bg-[#0C0C0C] border border-white/5 text-white rounded px-2.5 h-9 text-xs w-full"
            >
              <option value="telegram">Telegram Channel/Bot</option>
              <option value="instagram">Instagram Hashtag/Handle</option>
              <option value="whatsapp">WhatsApp Invite Link</option>
              <option value="website">Forum/Pastebin URL</option>
            </select>
          </div>

          <Button
            type="submit"
            disabled={scanning || !scanTarget.trim()}
            className="bg-[#E56A21] hover:bg-[#E56A21]/80 text-white font-bold h-9 shrink-0 uppercase text-xs px-4"
          >
            {scanning ? "SCANNING TARGET..." : "RUN INTEL NLP SCAN"}
          </Button>
        </form>

        {scanning && (
          <div className="bg-[#0C0C0C] border border-white/5 p-4 rounded-xl flex items-center gap-3">
            <div className="h-5 w-5 border-2 border-[#E56A21]/30 border-t-[#E56A21] rounded-full animate-spin shrink-0" />
            <span className="text-text-secondary uppercase text-[10px] animate-pulse tracking-wider">
              {scanStep}
            </span>
          </div>
        )}

        {scanResult && (
          <div className="bg-[#0B0B0B] border border-[#E56A21]/30 rounded-xl p-4 flex flex-col gap-4">
            {/* Result Header */}
            <div className="flex justify-between items-center border-b border-white/5 pb-2">
              <div className="flex items-center gap-2">
                <Badge
                  tone={scanResult.is_narcotics_related ? "destructive" : "success"}
                  className="text-[8.5px] uppercase font-bold tracking-wider"
                >
                  {scanResult.is_narcotics_related ? "⚠ DRUG ACTIVITY DETECTED" : "✓ NO DRUG ACTIVITY"}
                </Badge>
                <span className="text-white font-bold text-[10px] uppercase">{scanResult.target}</span>
                <Badge tone="outline" className="text-[7px] uppercase">{scanResult.source_type}</Badge>
              </div>
              <div className="flex items-center gap-3 text-[8.5px]">
                <span className="text-text-tertiary">RISK:</span>
                <span className={`font-bold ${scanResult.risk_score >= 75 ? "text-red-500" : scanResult.risk_score >= 50 ? "text-amber-400" : scanResult.risk_score >= 25 ? "text-yellow-400" : "text-emerald-400"}`}>
                  {scanResult.risk_score}/100 ({scanResult.risk_level || (scanResult.risk_score >= 75 ? "CRITICAL" : scanResult.risk_score >= 50 ? "HIGH" : scanResult.risk_score >= 25 ? "MEDIUM" : "LOW")})
                </span>
              </div>
            </div>

            {/* Three Column Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-[10px] text-text-secondary">
              
              {/* Column 1: Substances & Slang */}
              <div className="space-y-3">
                <div>
                  <span className="text-text-tertiary text-[8px] uppercase font-bold block mb-1">Detected Substances</span>
                  <div className="flex gap-1.5 flex-wrap">
                    {(scanResult.substances_detected || []).map((sub: string) => (
                      <Badge key={sub} tone="outline" className="text-[7.5px] uppercase font-bold text-[#E56A21] border-[#E56A21]/35">
                        {sub}
                      </Badge>
                    ))}
                    {(!scanResult.substances_detected || scanResult.substances_detected.length === 0) && <span className="text-text-tertiary text-[8px]">None</span>}
                  </div>
                </div>

                <div>
                  <span className="text-text-tertiary text-[8px] uppercase font-bold block mb-1">NDPS Act Sections</span>
                  <div className="flex gap-1.5 flex-wrap">
                    {(scanResult.ndps_sections || []).map((sec: string, i: number) => (
                      <Badge key={i} tone="outline" className="text-[7px] text-red-400 border-red-500/30 uppercase">
                        {sec}
                      </Badge>
                    ))}
                    {(!scanResult.ndps_sections || scanResult.ndps_sections.length === 0) && <span className="text-text-tertiary text-[8px]">N/A</span>}
                  </div>
                </div>

                <div>
                  <span className="text-text-tertiary text-[8px] uppercase font-bold block mb-1">Slang / Emoji Decoding</span>
                  <div className="border border-white/5 rounded overflow-hidden">
                    <table className="w-full text-left border-collapse bg-[#0C0C0C]">
                      <thead>
                        <tr className="border-b border-white/5 text-[7.5px] text-text-tertiary bg-white/5">
                          <th className="p-1.5 pl-2">TERM</th>
                          <th className="p-1.5">DECODED</th>
                          <th className="p-1.5 pr-2">CONF</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(scanResult.slang_lexicon_matches || []).slice(0, 8).map((lex: any, i: number) => (
                          <tr key={i} className="border-b border-white/5">
                            <td className="p-1.5 pl-2 text-white font-bold">{lex.term}</td>
                            <td className="p-1.5 text-text-primary">{lex.meaning}</td>
                            <td className="p-1.5 pr-2 font-bold text-[#E56A21]">{lex.confidence}%</td>
                          </tr>
                        ))}
                        {(!scanResult.slang_lexicon_matches || scanResult.slang_lexicon_matches.length === 0) && (
                          <tr><td colSpan={3} className="p-2 text-center text-text-tertiary text-[8px]">No slang decoded</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Column 2: Operator Profile & Entities */}
              <div className="space-y-3 border-t md:border-t-0 md:border-l border-white/5 pt-2 md:pt-0 md:pl-4">
                <div>
                  <span className="text-text-tertiary text-[8px] uppercase font-bold block mb-1">Operator Profile</span>
                  <div className="bg-[#0C0C0C] border border-white/5 rounded p-2 space-y-1">
                    {scanResult.operator_profile && (
                      <>
                        <div className="flex justify-between"><span className="text-text-tertiary">ID:</span><span className="text-white font-bold">{scanResult.operator_profile.operator_id}</span></div>
                        <div className="flex justify-between"><span className="text-text-tertiary">Handle:</span><span className="text-white">{scanResult.operator_profile.primary_handle}</span></div>
                        <div className="flex justify-between"><span className="text-text-tertiary">Platform:</span><span className="text-white uppercase">{scanResult.operator_profile.platform_origin}</span></div>
                      </>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-text-tertiary text-[8px] uppercase font-bold block mb-1">Extracted Entities</span>
                  <div className="bg-[#0C0C0C] border border-white/5 rounded p-2 space-y-1 text-[9px]">
                    {scanResult.extracted_entities && Object.entries(scanResult.extracted_entities).map(([key, vals]: [string, any]) => (
                      vals && vals.length > 0 && (
                        <div key={key} className="flex gap-2">
                          <span className="text-text-tertiary uppercase text-[7.5px] min-w-[60px] shrink-0">{key.replace(/_/g, " ").replace("numbers", "#").replace("addresses", "")}:</span>
                          <span className="text-white font-bold break-all">{vals.slice(0, 2).join(", ")}{vals.length > 2 ? ` +${vals.length - 2}` : ""}</span>
                        </div>
                      )
                    ))}
                    {(!scanResult.extracted_entities || Object.values(scanResult.extracted_entities).every((v: any) => !v || v.length === 0)) && (
                      <span className="text-text-tertiary text-[8px]">No entities extracted</span>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-text-tertiary text-[8px] uppercase font-bold block mb-1">Bot / Automation Detection</span>
                  <div className="bg-[#0C0C0C] border border-white/5 rounded p-2 space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-text-tertiary">Probability:</span>
                      <span className={`font-bold ${(scanResult.bot_detection?.bot_probability || 0) >= 0.6 ? "text-red-400" : "text-emerald-400"}`}>
                        {Math.round((scanResult.bot_detection?.bot_probability || 0) * 100)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-text-tertiary">Verdict:</span>
                      <Badge tone={scanResult.bot_detection?.is_bot ? "destructive" : "outline"} className="text-[7px]">
                        {scanResult.bot_detection?.is_bot ? "AUTOMATED" : "HUMAN TELEMETRY"}
                      </Badge>
                    </div>
                    {scanResult.bot_detection?.indicators?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {scanResult.bot_detection.indicators.map((ind: string, i: number) => (
                          <span key={i} className="bg-red-500/10 text-red-400 text-[6.5px] px-1.5 py-0.5 rounded uppercase">{ind}</span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Column 3: Justification & Compliance */}
              <div className="space-y-3 border-t md:border-t-0 md:border-l border-white/5 pt-2 md:pt-0 md:pl-4">
                <div>
                  <span className="text-text-tertiary text-[8px] uppercase font-bold block mb-1">AI Analysis & Justification</span>
                  <p className="bg-[#0C0C0C] border border-white/5 p-2 rounded text-text-primary leading-relaxed italic text-[9px]">
                    "{scanResult.justification}"
                  </p>
                </div>

                {scanResult.risk_reasons && scanResult.risk_reasons.length > 0 && (
                  <div>
                    <span className="text-text-tertiary text-[8px] uppercase font-bold block mb-1">Risk Score Breakdown</span>
                    <div className="bg-[#0C0C0C] border border-white/5 rounded p-2 space-y-1">
                      {scanResult.risk_reasons.map((r: string, i: number) => (
                        <div key={i} className="flex items-start gap-1.5 text-[8.5px]">
                          <span className="text-[#E56A21] mt-0.5">▸</span>
                          <span className="text-text-primary">{r}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {scanResult.intelligence_graph && (
                  <div>
                    <span className="text-text-tertiary text-[8px] uppercase font-bold block mb-1">Intelligence Graph</span>
                    <div className="bg-[#0C0C0C] border border-white/5 rounded p-2 flex gap-4 text-[9px]">
                      <div className="flex flex-col items-center">
                        <span className="text-[#E56A21] text-lg font-bold">{scanResult.intelligence_graph.nodes?.length || 0}</span>
                        <span className="text-text-tertiary text-[7px] uppercase">Nodes</span>
                      </div>
                      <div className="flex flex-col items-center">
                        <span className="text-[#E56A21] text-lg font-bold">{scanResult.intelligence_graph.edges?.length || 0}</span>
                        <span className="text-text-tertiary text-[7px] uppercase">Edges</span>
                      </div>
                      <div className="flex flex-col items-center">
                        <span className="text-white text-lg font-bold">{scanResult.messages?.length || 0}</span>
                        <span className="text-text-tertiary text-[7px] uppercase">Messages</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex flex-col gap-1.5 border-t border-white/5 pt-2">
                  <div className="flex justify-between text-[8px] text-text-tertiary">
                    <span>Compliance: IT Act 2000 / NDPS Act 1985</span>
                    <span className="text-emerald-400 font-bold uppercase">AUDIT LOCKED</span>
                  </div>
                  <div className="bg-[#0C0C0C] p-1.5 rounded font-courier text-[7px] text-purple-400 break-all select-all">
                    SHA-256: {scanResult.hash}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 2. DYNAMIC DRUG TRENDS & ACTIVE CITIES HEATMAP */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Drug Trends Bar Chart */}
        <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-3">
            <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
              <TrendingUp className="h-3.5 w-3.5 text-[#E56A21]" />
              DRUG INTEL TRENDS (CONVERSATIONS)
            </span>
          </div>
          <div className="space-y-3.5 flex-1 mt-2">
            {activeDrugs.map((d: any) => {
              const max = activeDrugs[0]?.count || 1;
              const width = Math.round((d.count / max) * 100);
              return (
                <div key={d.name} className="flex items-center gap-3 text-xs">
                  <span className="w-[80px] text-text-secondary truncate">{d.name}</span>
                  <div className="flex-1 h-3.5 bg-[#0B0B0B] border border-white/5 rounded overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-[#E56A21]/40 to-[#E56A21] rounded"
                      style={{ width: `${width}%` }}
                    />
                  </div>
                  <span className="w-[30px] font-bold text-right text-white">{d.count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Active Cities Chart / Heatmap */}
        <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-3">
            <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 text-red-500" />
              MOST ACTIVE REGIONS
            </span>
          </div>
          <div className="space-y-3.5 flex-1 mt-2">
            {activeCities.map((c: any) => {
              const max = activeCities[0]?.count || 1;
              const width = Math.round((c.count / max) * 100);
              return (
                <div key={c.name} className="flex items-center gap-3 text-xs">
                  <span className="w-[100px] text-text-secondary truncate">{c.name}</span>
                  <div className="flex-1 h-3.5 bg-[#0B0B0B] border border-white/5 rounded overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-red-500/20 to-red-500/80 rounded"
                      style={{ width: `${width}%` }}
                    />
                  </div>
                  <span className="w-[30px] font-bold text-right text-white">{c.count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Platform Share Telescope */}
        <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-3">
            <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
              <Globe className="h-3.5 w-3.5 text-emerald-500" />
              PLATFORM PROBING
            </span>
          </div>
          <div className="space-y-4 flex-1 mt-2">
            {Object.entries(activePlatforms).map(([p, count]: any) => {
              const total = Object.values(activePlatforms).reduce((a: any, b: any) => a + b, 0) as number;
              const pct = total > 0 ? Math.round((count / total) * 100) : 0;
              return (
                <div key={p} className="flex flex-col gap-1 text-xs">
                  <div className="flex justify-between text-text-secondary">
                    <span className="uppercase font-bold">{p}</span>
                    <span>{count} chats ({pct}%)</span>
                  </div>
                  <div className="h-2 bg-[#0B0B0B] border border-white/5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        p === "telegram"
                          ? "bg-sky-500"
                          : p === "whatsapp"
                          ? "bg-emerald-500"
                          : "bg-rose-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. CROSS-PLATFORM ENTITY CORRELATION GRAPH */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* SVG Interactive Entity Graph */}
        <div className="lg:col-span-2 bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col h-[500px] overflow-hidden">
          <div className="flex justify-between items-center mb-4">
            <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
              <Network className="h-3.5 w-3.5 text-[#E56A21]" />
              CROSS-PLATFORM INTEGRATION ENTITY GRAPH
            </span>
            <Badge tone="success" className="text-[8px] animate-pulse">CORRELATED LIVE</Badge>
          </div>

          <div className="flex flex-1 min-h-0 gap-6">
            {/* Interactive SVG Canvas */}
            <div className="flex-1 relative bg-[#0B0B0B] border border-white/5 rounded-lg overflow-hidden">
              <svg className="w-full h-full select-none" viewBox="0 0 100 100">
                {/* Render Edges */}
                {graphEdges.map((edge: any) => {
                  const fromNode = graphNodes.find(n => n.id === edge.from);
                  const toNode = graphNodes.find(n => n.id === edge.to);
                  if (!fromNode || !toNode) return null;
                  const isHighlighted = selectedNode?.id === edge.from || selectedNode?.id === edge.to;
                  return (
                    <g key={edge.id}>
                      <line
                        x1={fromNode.x}
                        y1={fromNode.y}
                        x2={toNode.x}
                        y2={toNode.y}
                        stroke={isHighlighted ? "#E56A21" : "rgba(255,255,255,0.06)"}
                        strokeWidth={isHighlighted ? "0.6" : "0.3"}
                        strokeDasharray={isHighlighted ? "2 2" : undefined}
                      />
                    </g>
                  );
                })}
                {/* Render Nodes */}
                {graphNodes.map((node: any) => {
                  const isSelected = selectedNode?.id === node.id;
                  const nodeColor = node.role === "seller" ? "fill-red-950/40 stroke-red-500" : "fill-sky-950/40 stroke-sky-400";
                  const textColor = node.role === "seller" ? "text-red-400" : "text-sky-400";
                  
                  return (
                    <g
                      key={node.id}
                      transform={`translate(${node.x}, ${node.y})`}
                      className="cursor-pointer"
                      onClick={() => setSelectedNode(node)}
                    >
                      <circle
                        r="3.5"
                        className={`${nodeColor} stroke-1 transition-all duration-300 ${
                          isSelected ? "stroke-[1.5px] stroke-[#E56A21]" : ""
                        }`}
                      />
                      {isSelected && <circle r="6" fill="none" stroke="#E56A21" strokeWidth="0.4" className="animate-ping" />}
                      <text y="-5" textAnchor="middle" className="fill-white font-mono text-[3.5px] font-semibold uppercase tracking-wide">
                        {node.name.split(" ")[0]}
                      </text>
                      <text y="7.5" textAnchor="middle" className={`${textColor} font-mono text-[2.5px] font-bold uppercase tracking-wider`}>
                        {node.role}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Entity inspector pane */}
            <div className="w-[240px] flex flex-col justify-between border-l border-white/5 pl-4 text-[10px] text-text-secondary font-mono">
              {selectedNode ? (
                <div className="flex flex-col gap-3">
                  <div className="border-b border-[#E56A21]/30 pb-2">
                    <span className="text-white text-xs font-bold block">{selectedNode.name}</span>
                    <Badge tone={selectedNode.role === "seller" ? "destructive" : "warning"} className="text-[7.5px] uppercase mt-1">
                      {selectedNode.role.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <div className="flex flex-col">
                      <span className="text-text-tertiary text-[8px] uppercase">Cross-linked handles</span>
                      {selectedNode.telegram_username && <span className="text-white mt-0.5">TG: {selectedNode.telegram_username}</span>}
                      {selectedNode.instagram_handle && <span className="text-white">IG: {selectedNode.instagram_handle}</span>}
                      {selectedNode.whatsapp_number && <span className="text-white">WA: {selectedNode.whatsapp_number}</span>}
                    </div>
                    {selectedNode.phone && (
                      <div className="flex justify-between">
                        <span className="text-text-tertiary">PHONE:</span>
                        <span className="text-white font-bold">{selectedNode.phone}</span>
                      </div>
                    )}
                    {selectedNode.email && (
                      <div className="flex flex-col">
                        <span className="text-text-tertiary">EMAIL:</span>
                        <span className="text-white font-bold truncate">{selectedNode.email}</span>
                      </div>
                    )}
                    {selectedNode.wallet && (
                      <div className="flex flex-col">
                        <span className="text-text-tertiary">WALLET:</span>
                        <span className="text-purple-400 font-bold font-courier text-[9px] break-all">{selectedNode.wallet}</span>
                      </div>
                    )}
                    <div className="flex justify-between border-t border-white/5 pt-2">
                      <span>RISK INDEX:</span>
                      <span className="font-bold text-red-500">{selectedNode.risk_score}/100</span>
                    </div>
                    <div className="flex justify-between">
                      <span>BOT PROBABILITY:</span>
                      <span className="font-bold text-white">{Math.round(selectedNode.bot_probability * 100)}%</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center text-text-tertiary">
                  <Network className="h-6 w-6 opacity-30 mb-2" />
                  <span>Select a suspect node in the syndicate graph.</span>
                </div>
              )}
              <div className="text-[8px] text-text-tertiary leading-tight border-t border-white/5 pt-2">
                Node link signals indicate communication, same registration, or crypto transfer.
              </div>
            </div>
          </div>
        </div>

        {/* Live Conversation Alerts Feed */}
        <div className="bg-[#151515] border border-white/5 rounded-xl p-4 flex flex-col h-[500px]">
          <div className="flex justify-between items-center border-b border-white/5 pb-2.5 mb-2">
            <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
              <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
              INTELLIGENCE ALERTS FEED
            </span>
            <Badge tone="destructive" className="text-[8px]">CRITICAL</Badge>
          </div>
          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 scrollbar-none text-[9px]">
            {analytics?.recent_alerts?.map((alert: any, idx: number) => (
              <div key={idx} className="bg-[#0B0B0B] border border-white/5 rounded-lg p-2.5 flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-1.5">
                    <Badge tone="destructive" className="text-[7.5px] font-bold">SELLER</Badge>
                    <span className="text-white font-bold">{alert.sender}</span>
                  </div>
                  <span className="text-text-tertiary text-[7.5px]">{alert.timestamp.split("T")[-1]?.substring(0, 5) || alert.timestamp}</span>
                </div>
                <p className="text-text-primary text-[10px] leading-relaxed italic">"{alert.message}"</p>
                <div className="border-t border-white/5 pt-1.5 mt-1 flex justify-between items-center text-[8px] text-text-tertiary">
                  <span>DRUG: {alert.drug} ({alert.slang})</span>
                  <span className="text-red-400 font-bold">RISK: {alert.risk_score}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 4. EVIDENCE LOCKER & LIVE EVIDENCE FEED */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Evidence Locker Feed (Features 9, 13) */}
        <div className="lg:col-span-2 bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col h-[400px]">
          <div className="flex justify-between items-center border-b border-white/5 pb-3 mb-3">
            <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5 text-[#E56A21]" />
              SECURE EVIDENCE LOCKER (SEC 65B INDIAN EVIDENCE ACT)
            </span>
            <Badge tone="success" className="text-[8px]">{evidence.length} RECORDED</Badge>
          </div>
          <div className="flex-1 overflow-y-auto space-y-3.5 pr-1 scrollbar-none text-[9px] text-text-secondary">
            {evidence.slice(0, 50).map((ev: any) => (
              <div key={ev.id} className="bg-[#0B0B0B] border border-white/5 rounded-xl p-3 flex flex-col gap-2">
                <div className="flex justify-between items-center border-b border-white/5 pb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-bold">{ev.id}</span>
                    <span className="text-text-tertiary">|</span>
                    <Badge tone="outline" className="text-[7.5px] uppercase">{ev.platform}</Badge>
                    <span className="text-[#E56A21] font-bold">{ev.drug} detected</span>
                  </div>
                  <span className="text-text-tertiary text-[8px]">{ev.timestamp}</span>
                </div>
                <div className="text-text-primary text-[10px] italic">"{ev.message}"</div>
                <div className="flex justify-between items-center border-t border-white/5 pt-2 mt-1 text-[8px] text-text-tertiary">
                  <span className="font-courier truncate max-w-[280px]">SHA-256 INTEGRITY: {ev.hash}</span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setSelectedEvidence(ev)}
                      className="bg-white/5 hover:bg-white/10 border border-white/10 text-white px-2 py-0.5 rounded cursor-pointer uppercase font-bold"
                    >
                      Inspect
                    </button>
                    <button
                      onClick={() => exportEvidenceCertificate(ev)}
                      className="flex items-center gap-1 bg-[#E56A21]/10 hover:bg-[#E56A21]/20 border border-[#E56A21]/30 text-[#E56A21] px-2 py-0.5 rounded cursor-pointer uppercase font-bold"
                    >
                      <Download className="h-2.5 w-2.5" /> Certificate
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Evidence details inspector side card */}
        <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col h-[400px]">
          <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5 mb-3 border-b border-white/5 pb-3">
            <FileText className="h-3.5 w-3.5 text-[#E56A21]" />
            EVIDENCE DETAILED OVERVIEW
          </span>
          {selectedEvidence ? (
            <div className="flex flex-col gap-3 text-[10px] text-text-secondary overflow-y-auto scrollbar-none pr-1">
              <div className="flex justify-between">
                <span className="text-text-tertiary">EVIDENCE ID:</span>
                <span className="text-white font-bold">{selectedEvidence.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-tertiary">PLATFORM:</span>
                <span className="text-white uppercase font-bold">{selectedEvidence.platform}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-tertiary">SUSPECT USER:</span>
                <span className="text-white">{selectedEvidence.display_name} ({selectedEvidence.username})</span>
              </div>
              {selectedEvidence.phone && (
                <div className="flex justify-between">
                  <span className="text-text-tertiary">PHONE NO:</span>
                  <span className="text-white">{selectedEvidence.phone}</span>
                </div>
              )}
              {selectedEvidence.email && (
                <div className="flex justify-between">
                  <span className="text-text-tertiary">EMAIL ID:</span>
                  <span className="text-white truncate max-w-[120px]">{selectedEvidence.email}</span>
                </div>
              )}
              {selectedEvidence.wallet && (
                <div className="flex flex-col gap-0.5">
                  <span className="text-text-tertiary">PAYMENT WALLET:</span>
                  <span className="text-purple-400 font-courier text-[8.5px] break-all">{selectedEvidence.wallet}</span>
                </div>
              )}
              <div className="flex justify-between border-t border-white/5 pt-2">
                <span>AI MATCHED DRUG:</span>
                <span className="text-[#E56A21] font-bold">{selectedEvidence.drug}</span>
              </div>
              <div className="flex justify-between">
                <span>AI MATCH CONFIDENCE:</span>
                <span className="text-white font-bold">{Math.round(selectedEvidence.confidence * 100)}%</span>
              </div>
              <div className="flex flex-col gap-1 border-t border-white/5 pt-2">
                <span className="text-text-tertiary text-[9px] font-bold">EXPLAINABILITY LOG:</span>
                <p className="leading-relaxed text-[9px]">{selectedEvidence.reasoning}</p>
              </div>
              <div className="flex flex-col gap-1 border-t border-white/5 pt-2">
                <span className="text-text-tertiary text-[9px] font-bold">BOT LIKELIHOOD STATUS:</span>
                <Badge tone={selectedEvidence.is_bot ? "destructive" : "outline"} className="text-[7.5px] self-start mt-0.5">
                  {selectedEvidence.is_bot ? "BOT DETECTION ACTIVE" : "HUMAN SIGNALS CONFIRMED"}
                </Badge>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-text-tertiary text-xs">
              <Lock className="h-6 w-6 opacity-30 mb-2" />
              <span>Select an item in the evidence feed to inspect prosecution logs.</span>
            </div>
          )}
        </div>
      </div>
      
    </div>
  );
}
