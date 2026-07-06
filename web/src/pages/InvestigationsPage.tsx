import React, { useState, useEffect, useMemo } from "react";
import { useLocation } from "react-router-dom";
import {
  Search,
  ShieldAlert,
  Users,
  Download,
  Lock,
  Activity,
  HelpCircle,
  FileText
} from "lucide-react";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";
import { Input } from "@nous-research/ui/ui/components/input";
import { api } from "@/lib/api";

export default function InvestigationsPage() {
  const location = useLocation();
  const isEvidenceLocker = location.search.includes("evidence=true");

  if (isEvidenceLocker) {
    return <EvidenceLockerView />;
  }
  return <ExplorerView />;
}

// ──────────────────────────────────────────────────────────────────────────────
// EXPLORER VIEW (INVESTIGATIONS)
// ──────────────────────────────────────────────────────────────────────────────
function ExplorerView() {
  const [query, setQuery] = useState("MDMA");
  const [searchVal, setSearchVal] = useState("MDMA");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [dictionary, setDictionary] = useState<any[]>([]);

  useEffect(() => {
    async function init() {
      try {
        const dict = await api.getNarcoticsDictionary();
        setDictionary(dict || []);
      } catch (err) {
        console.error("Failed to load dictionary", err);
      }
    }
    init();
    handleSearch("MDMA");
  }, []);

  const handleSearch = async (qString: string) => {
    setLoading(true);
    try {
      const res = await api.searchNarcotics(qString);
      setData(res);
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setLoading(false);
    }
  };

  const onSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchVal.trim()) {
      setQuery(searchVal.trim());
      handleSearch(searchVal.trim());
    }
  };

  const handleQuickSelect = (name: string) => {
    setSearchVal(name);
    setQuery(name);
    handleSearch(name);
  };

  const highlightText = (text: string, aliases: string[] = []) => {
    if (!text) return "";
    let wordsToHighlight = [...aliases];
    if (query && !wordsToHighlight.includes(query.toLowerCase())) {
      wordsToHighlight.push(query);
    }
    
    wordsToHighlight = wordsToHighlight
      .filter(Boolean)
      .map(w => w.toLowerCase())
      .sort((a, b) => b.length - a.length);

    if (wordsToHighlight.length === 0) return <span>{text}</span>;

    const escaped = wordsToHighlight.map(w => w.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'));
    const regex = new RegExp(`\\b(${escaped.join("|")})\\b`, "gi");
    
    const parts = text.split(regex);
    return (
      <span>
        {parts.map((part, i) => {
          const isMatch = wordsToHighlight.includes(part.toLowerCase());
          return isMatch ? (
            <span key={i} className="bg-[#E56A21]/20 text-[#E56A21] border border-[#E56A21]/30 px-1 rounded font-bold animate-pulse">
              {part}
            </span>
          ) : (
            part
          );
        })}
      </span>
    );
  };

  return (
    <div className="flex flex-col gap-6 p-6 min-h-0 min-w-0 flex-1 overflow-y-auto text-text-primary bg-[#0E0E0E] font-mono">
      {/* Search Header */}
      <div className="bg-[#151515] border border-white/5 rounded-xl p-5 relative overflow-hidden flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="absolute top-0 right-0 w-[200px] h-[200px] bg-[#E56A21]/5 rounded-full blur-[80px] pointer-events-none" />
        <div className="flex-1 flex flex-col gap-1">
          <span className="text-[10px] tracking-widest text-[#E56A21] font-bold uppercase flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5" />
            NARCOTICS INVESTIGATIONS
          </span>
          <h1 className="text-white text-lg font-bold">DRUG CONVERSATION EXPLORER</h1>
        </div>
        
        <form onSubmit={onSearchSubmit} className="flex gap-2 w-full md:w-auto min-w-[300px]">
          <Input
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            placeholder="Search drug, alias, slang, emoji..."
            className="bg-[#0C0C0C] border-white/5 font-mono text-xs focus:border-[#E56A21]"
          />
          <Button type="submit" size="sm" className="bg-[#E56A21] hover:bg-[#E56A21]/80 text-white shrink-0">
            <Search className="h-4 w-4 mr-1.5" /> SEARCH
          </Button>
        </form>
      </div>

      {/* Quick Select Panel */}
      <div className="flex flex-wrap items-center gap-2 bg-[#151515]/50 border border-white/5 rounded-lg px-4 py-2 text-[10px] text-text-secondary">
        <span className="text-text-tertiary uppercase">Quick Targets:</span>
        {dictionary.map(d => (
          <button
            key={d.name}
            onClick={() => handleQuickSelect(d.name)}
            className={`px-2 py-0.5 border rounded cursor-pointer transition-colors duration-150 ${
              query.toLowerCase() === d.name.toLowerCase()
                ? "bg-[#E56A21]/20 border-[#E56A21] text-[#E56A21] font-bold"
                : "bg-[#1C1C1C] border-white/5 hover:border-white/20 text-white"
            }`}
          >
            {d.emojis?.[0] || "💊"} {d.name}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center min-h-[300px]">
          <div className="flex flex-col items-center gap-3 text-text-tertiary">
            <div className="h-8 w-8 border-2 border-[#E56A21]/30 border-t-[#E56A21] rounded-full animate-spin" />
            <span className="text-xs uppercase tracking-wider">Decoding slang and scanning telemetry...</span>
          </div>
        </div>
      ) : data ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column */}
          <div className="flex flex-col gap-6 lg:col-span-1">
            <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col gap-4">
              <div className="flex justify-between items-start border-b border-white/5 pb-3">
                <div>
                  <h2 className="text-white text-base font-bold flex items-center gap-2">
                    {data.overview?.emojis?.[0] || "💊"} {data.overview?.name || query.toUpperCase()}
                  </h2>
                  <span className="text-[10px] text-text-tertiary uppercase tracking-wider mt-0.5 block">Drug Classification</span>
                </div>
                {data.overview && (
                  <Badge
                    tone={data.overview.risk_level === "HIGH" || data.overview.risk_level === "CRITICAL" ? "destructive" : "warning"}
                    className="text-[9px] font-bold uppercase tracking-wider"
                  >
                    {data.overview.risk_level} RISK
                  </Badge>
                )}
              </div>

              {data.overview ? (
                <div className="space-y-4 text-xs text-text-secondary">
                  <p className="leading-relaxed text-text-primary text-[11px]">{data.overview.overview}</p>
                  <div className="grid gap-2 border-t border-white/5 pt-3">
                    <div className="flex justify-between">
                      <span className="text-text-tertiary">STREET NAMES:</span>
                      <span className="text-white font-semibold">{data.overview.aliases.join(", ")}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-tertiary">EMOJIS:</span>
                      <span className="text-white">{data.overview.emojis.join(" ")}</span>
                    </div>
                    <span className="text-text-tertiary uppercase text-[9px] mt-2 block">Multilingual Aliases</span>
                    <div className="flex justify-between">
                      <span className="text-text-tertiary">HINDI SPELLING:</span>
                      <span className="text-white font-semibold">{data.overview.hindi_spelling}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-tertiary">HINGLISH SPELLING:</span>
                      <span className="text-white font-semibold">{data.overview.hinglish_spelling}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-text-tertiary leading-relaxed">
                  <HelpCircle className="h-6 w-6 opacity-30 mb-2" />
                  <p>No formal database overview for "{query}". Showing telemetry matches matching search string.</p>
                </div>
              )}
            </div>

            <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col gap-4">
              <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
                <ShieldAlert className="h-3.5 w-3.5 text-[#E56A21]" />
                INTEL METRICS
              </span>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#0B0B0B] border border-white/5 p-3 rounded-lg flex flex-col">
                  <span className="text-[9px] text-text-tertiary uppercase">RISK SCORE</span>
                  <span className="text-white text-xl font-bold mt-1">{data.risk_score}%</span>
                </div>
                <div className="bg-[#0B0B0B] border border-white/5 p-3 rounded-lg flex flex-col">
                  <span className="text-[9px] text-text-tertiary uppercase">MATCHED CONVS</span>
                  <span className="text-[#E56A21] text-xl font-bold mt-1">{data.conversations.length}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Columns */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-[#151515] border border-white/5 rounded-xl p-4 flex flex-col h-[230px]">
                <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5 border-b border-white/5 pb-2 mb-2">
                  <Users className="h-3.5 w-3.5 text-red-500" /> DETECTED SELLERS
                </span>
                <div className="flex-1 overflow-y-auto space-y-2 pr-1 scrollbar-none text-[9px] text-text-secondary">
                  {data.sellers.map((s: any) => (
                    <div key={s.id} className="bg-[#0B0B0B] border border-white/5 rounded-lg p-2 flex justify-between items-center">
                      <div>
                        <span className="text-white font-bold block">{s.display_name}</span>
                        <span className="text-text-tertiary text-[8px]">{s.telegram_username || s.whatsapp_number}</span>
                      </div>
                      <span className="text-red-400 font-bold">RISK: {s.risk_score}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-[#151515] border border-white/5 rounded-xl p-4 flex flex-col h-[230px]">
                <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5 border-b border-white/5 pb-2 mb-2">
                  <Users className="h-3.5 w-3.5 text-sky-400" /> DETECTED BUYERS
                </span>
                <div className="flex-1 overflow-y-auto space-y-2 pr-1 scrollbar-none text-[9px] text-text-secondary">
                  {data.buyers.map((b: any) => (
                    <div key={b.id} className="bg-[#0B0B0B] border border-white/5 rounded-lg p-2 flex justify-between items-center">
                      <div>
                        <span className="text-white font-bold block">{b.display_name}</span>
                        <span className="text-text-tertiary text-[8px]">{b.telegram_username || b.whatsapp_number}</span>
                      </div>
                      <span className="text-sky-400 font-bold">RISK: {b.risk_score}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col flex-1 min-h-[300px]">
              <span className="text-[10px] tracking-wider text-text-tertiary uppercase border-b border-white/5 pb-3 mb-4 block">
                DETECTED CONVERSATIONS
              </span>
              <div className="space-y-4 max-h-[400px] overflow-y-auto pr-1 scrollbar-none">
                {data.conversations.map((c: any) => (
                  <div key={c.id} className="bg-[#0B0B0B] border border-white/5 rounded-xl p-4 flex flex-col gap-2">
                    <div className="flex justify-between items-center text-[8px] text-text-tertiary">
                      <div className="flex items-center gap-2">
                        <Badge tone="outline" className="text-[7.5px] uppercase">{c.platform}</Badge>
                        <span className="text-white font-bold text-[9px]">{c.display_name}</span>
                      </div>
                      <span>{c.timestamp}</span>
                    </div>
                    <p className="text-text-primary text-[10.5px] italic leading-normal">
                      {highlightText(c.message, data.overview?.aliases || [])}
                    </p>
                    <div className="flex justify-between items-center text-[8px] text-text-tertiary border-t border-white/5 pt-1.5 mt-1">
                      <span>BOT PROB: {Math.round(c.bot_probability * 100)}%</span>
                      <Badge tone={c.label === "seller" ? "destructive" : c.label === "buyer" ? "warning" : "outline"} className="text-[7.5px] uppercase">
                        {c.label}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// EVIDENCE LOCKER VIEW
// ──────────────────────────────────────────────────────────────────────────────
function EvidenceLockerView() {
  const [evidenceList, setEvidenceList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEv, setSelectedEv] = useState<any>(null);
  const [searchVal, setSearchVal] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getNarcoticsEvidence();
        setEvidenceList(res || []);
        if (res && res.length > 0) {
          setSelectedEv(res[0]);
        }
      } catch (err) {
        console.error("Evidence Locker failed", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filteredEvidence = useMemo(() => {
    return evidenceList.filter(ev => {
      const id = (ev.id || "").toLowerCase();
      const user = (ev.display_name || "").toLowerCase();
      const drug = (ev.drug || "").toLowerCase();
      const msg = (ev.message || "").toLowerCase();
      const sLower = searchVal.toLowerCase();
      return id.includes(sLower) || user.includes(sLower) || drug.includes(sLower) || msg.includes(sLower);
    });
  }, [evidenceList, searchVal]);

  const exportCertificate = (ev: any) => {
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
CLASSIFICATION STATUS: ${ev.risk_score >= 70 ? "HIGH RISK SELLER" : "BUYER INQUIRY"}
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

  if (loading) {
    return (
      <div className="flex items-center justify-center flex-1 bg-[#0E0E0E]">
        <div className="flex flex-col items-center gap-3 font-mono text-text-tertiary">
          <div className="h-8 w-8 border-2 border-[#E56A21]/30 border-t-[#E56A21] rounded-full animate-spin" />
          <span className="text-xs tracking-wider uppercase">Loading Prosecution Locker...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6 min-h-0 min-w-0 flex-1 overflow-y-auto text-text-primary bg-[#0E0E0E] font-mono">
      {/* Header */}
      <div className="bg-[#151515] border border-white/5 rounded-xl p-5 relative overflow-hidden flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="absolute top-0 right-0 w-[200px] h-[200px] bg-[#E56A21]/5 rounded-full blur-[80px] pointer-events-none" />
        <div className="flex-1 flex flex-col gap-1">
          <span className="text-[10px] tracking-widest text-[#E56A21] font-bold uppercase flex items-center gap-1.5">
            <Lock className="h-3.5 w-3.5" />
            EVIDENCE VAULT
          </span>
          <h1 className="text-white text-lg font-bold">SEC 65B CHAIN OF CUSTODY LOGS</h1>
        </div>
        <div className="flex gap-2 w-full md:w-auto min-w-[280px]">
          <Input
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            placeholder="Search evidence ID, drug, username..."
            className="bg-[#0C0C0C] border-white/5 font-mono text-xs focus:border-[#E56A21]"
          />
        </div>
      </div>

      {/* Vault Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        
        {/* Left Side: Evidence Cards */}
        <div className="lg:col-span-2 flex flex-col gap-4 overflow-y-auto pr-1 scrollbar-none max-h-[600px]">
          {filteredEvidence.map((ev: any) => (
            <div
              key={ev.id}
              onClick={() => setSelectedEv(ev)}
              className={`bg-[#151515] border rounded-xl p-4 flex flex-col gap-3 cursor-pointer transition-all duration-200 hover:border-[#E56A21]/30 ${
                selectedEv?.id === ev.id ? "border-[#E56A21] bg-[#1C1C1C]/60" : "border-white/5"
              }`}
            >
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <div className="flex items-center gap-2">
                  <span className="text-white font-bold text-[10px]">{ev.id}</span>
                  <span className="text-text-tertiary">|</span>
                  <Badge tone="outline" className="text-[7.5px] uppercase">{ev.platform}</Badge>
                  <span className="text-[#E56A21] font-bold text-[9px]">{ev.drug} mention</span>
                </div>
                <span className="text-text-tertiary text-[8px]">{ev.timestamp}</span>
              </div>
              
              <p className="text-text-primary text-[10px] leading-relaxed italic">
                "{ev.message}"
              </p>

              <div className="flex justify-between items-center border-t border-white/5 pt-2 mt-1 text-[8px] text-text-tertiary">
                <span className="truncate max-w-[260px]">SHA-256: {ev.hash}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); exportCertificate(ev); }}
                  className="flex items-center gap-1 bg-[#E56A21]/15 border border-[#E56A21]/30 hover:bg-[#E56A21]/35 text-[#E56A21] px-2 py-0.5 rounded text-[8px] cursor-pointer"
                >
                  <Download className="h-2.5 w-2.5" /> EXPORT CERTIFICATE
                </button>
              </div>
            </div>
          ))}
          {filteredEvidence.length === 0 && (
            <div className="text-text-tertiary text-center py-20 bg-[#151515] border border-white/5 rounded-xl">
              <FileText className="h-8 w-8 opacity-20 mx-auto mb-2" />
              <span>No evidence matches search query.</span>
            </div>
          )}
        </div>

        {/* Right Side: Evidence Detail Viewer */}
        <div className="lg:col-span-1 bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col max-h-[600px] overflow-y-auto scrollbar-none">
          <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5 mb-3 border-b border-white/5 pb-3">
            <FileText className="h-3.5 w-3.5 text-[#E56A21]" />
            PROSECUTION SPECIFICATION
          </span>

          {selectedEv ? (
            <div className="flex flex-col gap-3.5 text-[10px] text-text-secondary">
              <div className="flex justify-between border-b border-white/5 pb-2">
                <div>
                  <span className="text-white text-xs font-bold block">{selectedEv.id}</span>
                  <span className="text-text-tertiary text-[8.5px]">Case Reference Code</span>
                </div>
                <Badge tone="success" className="text-[7px]">INTEGRITY VERIFIED</Badge>
              </div>

              <div className="space-y-2 border-b border-white/5 pb-3">
                <div className="flex justify-between">
                  <span className="text-text-tertiary">CONV ID:</span>
                  <span className="text-white font-bold">{selectedEv.conv_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-tertiary">SOURCE PLATFORM:</span>
                  <span className="text-white uppercase font-bold">{selectedEv.platform}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-tertiary">USER IDENTITY:</span>
                  <span className="text-white">{selectedEv.display_name} ({selectedEv.username})</span>
                </div>
                {selectedEv.phone && (
                  <div className="flex justify-between">
                    <span className="text-text-tertiary">PHONE CONTACT:</span>
                    <span className="text-white">{selectedEv.phone}</span>
                  </div>
                )}
                {selectedEv.email && (
                  <div className="flex justify-between">
                    <span className="text-text-tertiary">EMAIL ADDRESS:</span>
                    <span className="text-white truncate max-w-[150px]">{selectedEv.email}</span>
                  </div>
                )}
                {selectedEv.wallet && (
                  <div className="flex flex-col gap-0.5 mt-1">
                    <span className="text-text-tertiary">PAYMENT WALLET:</span>
                    <span className="text-purple-400 font-courier break-all text-[8.5px]">{selectedEv.wallet}</span>
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-1 border-b border-white/5 pb-3">
                <span className="text-text-tertiary text-[9px] font-bold uppercase">MATCH DETAIL</span>
                <div className="flex justify-between mt-1">
                  <span>DETECTED DRUG:</span>
                  <span className="text-[#E56A21] font-bold">{selectedEv.drug}</span>
                </div>
                {selectedEv.slang && (
                  <div className="flex justify-between">
                    <span>MATCHED SLANG:</span>
                    <span className="text-white font-bold">{selectedEv.slang}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span>CLASSIFICATION:</span>
                  <span className="text-white uppercase font-bold">{selectedEv.risk_score >= 70 ? "Seller" : "Buyer"}</span>
                </div>
                <div className="flex justify-between">
                  <span>CONFIDENCE LEVEL:</span>
                  <span className="text-white font-bold">{Math.round(selectedEv.confidence * 100)}%</span>
                </div>
              </div>

              <div className="flex flex-col gap-1 border-b border-white/5 pb-3">
                <span className="text-text-tertiary text-[9px] font-bold uppercase">SHA-256 HASH PATH</span>
                <span className="text-purple-300 font-courier text-[8.5px] break-all bg-[#0C0C0C] border border-white/5 p-1.5 rounded mt-1">
                  {selectedEv.hash}
                </span>
              </div>

              <button
                onClick={() => exportCertificate(selectedEv)}
                className="w-full bg-[#E56A21] hover:bg-[#E56A21]/80 text-white font-bold py-2 rounded text-[10px] transition-colors cursor-pointer"
              >
                DOWNLOAD 65B CERTIFICATE
              </button>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-text-tertiary text-xs">
              <Lock className="h-6 w-6 opacity-30 mb-2" />
              <span>Select an evidence log to view details.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
