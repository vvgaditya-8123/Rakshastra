import React, { useState, useEffect } from "react";
import {
  Search,
  ShieldAlert,
  Users,
  Clock,
  Database,
  MessageSquare,
  Activity,
  HelpCircle
} from "lucide-react";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";
import { Input } from "@nous-research/ui/ui/components/input";
import { api } from "@/lib/api";

export default function DrugIntelligencePage() {
  const [query, setQuery] = useState("MDMA");
  const [searchVal, setSearchVal] = useState("MDMA");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [dictionary, setDictionary] = useState<any[]>([]);

  // Load dictionary and initial search at mount
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

  // Helper to highlight drug aliases in message text
  const highlightText = (text: string, aliases: string[] = []) => {
    if (!text) return "";
    let wordsToHighlight = [...aliases];
    if (query && !wordsToHighlight.includes(query.toLowerCase())) {
      wordsToHighlight.push(query);
    }
    
    // Sort by length descending to match longer phrases first
    wordsToHighlight = wordsToHighlight
      .filter(Boolean)
      .map(w => w.toLowerCase())
      .sort((a, b) => b.length - a.length);

    if (wordsToHighlight.length === 0) return <span>{text}</span>;

    // Build regex matching any of the aliases
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
            NARCOTICS INTELLIGENCE CORE
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
          {/* Left Column: Drug Overview & Statistics */}
          <div className="flex flex-col gap-6 lg:col-span-1">
            {/* Overview Card */}
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
                    <div className="flex justify-between">
                      <span className="text-text-tertiary">COMMON MISSPELLINGS:</span>
                      <span className="text-text-primary italic">{data.overview.misspellings.join(", ")}</span>
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

            {/* Metrics & Risk Card */}
            <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col gap-4">
              <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
                <ShieldAlert className="h-3.5 w-3.5 text-[#E56A21]" />
                INTEL METRICS
              </span>

              <div className="grid grid-cols-2 gap-4 border-b border-white/5 pb-4">
                <div className="bg-[#0B0B0B] border border-white/5 p-3 rounded-lg flex flex-col">
                  <span className="text-[9px] text-text-tertiary uppercase">RISK SCORE</span>
                  <span className="text-white text-xl font-bold mt-1">{data.risk_score}%</span>
                </div>
                <div className="bg-[#0B0B0B] border border-white/5 p-3 rounded-lg flex flex-col">
                  <span className="text-[9px] text-text-tertiary uppercase">MATCHED CONVS</span>
                  <span className="text-[#E56A21] text-xl font-bold mt-1">{data.conversations.length}</span>
                </div>
              </div>

              {/* Platform Distribution */}
              <div className="flex flex-col gap-2">
                <span className="text-[9px] text-text-tertiary uppercase">PLATFORM TELESCOPE</span>
                <div className="space-y-2">
                  {Object.entries(data.platforms || {}).map(([platform, count]: any) => {
                    const total = data.conversations.length;
                    const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                    return (
                      <div key={platform} className="flex flex-col gap-1 text-[10px]">
                        <div className="flex justify-between text-text-secondary">
                          <span className="uppercase">{platform}</span>
                          <span>{count} ({pct}%)</span>
                        </div>
                        <div className="h-1.5 bg-[#0B0B0B] border border-white/5 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              platform === "telegram"
                                ? "bg-sky-500"
                                : platform === "whatsapp"
                                ? "bg-emerald-500"
                                : "bg-rose-500"
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                  {Object.keys(data.platforms || {}).length === 0 && (
                    <span className="text-[9px] text-text-tertiary">No platforms matched.</span>
                  )}
                </div>
              </div>
            </div>

            {/* Detected Timeline */}
            <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col h-[280px]">
              <div className="flex justify-between items-center mb-3">
                <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-[#E56A21]" />
                  CONVERSATION TIMELINE
                </span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-3 pr-1 scrollbar-none text-[9px] text-text-secondary">
                {data.timeline.map((evt: any, idx: number) => (
                  <div key={idx} className="flex gap-2 relative">
                    <span className="text-[#E56A21] font-bold w-[35px] shrink-0 pt-0.5">{evt.time}</span>
                    <div className="flex flex-col items-center">
                      <div className="h-2 w-2 rounded-full bg-[#E56A21] shrink-0 mt-1" />
                      {idx < data.timeline.length - 1 && <div className="w-[1px] bg-white/10 flex-1 min-h-[15px]" />}
                    </div>
                    <div className="flex flex-col text-left">
                      <span className="text-white font-bold uppercase">{evt.action}</span>
                      <span className="text-text-tertiary truncate max-w-[200px]">{evt.details}</span>
                    </div>
                  </div>
                ))}
                {data.timeline.length === 0 && (
                  <div className="text-text-tertiary text-center py-8">No events.</div>
                )}
              </div>
            </div>
          </div>

          {/* Right Columns: Suspects & Filtered Conversations */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {/* Suspects Card */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Detected Sellers */}
              <div className="bg-[#151515] border border-white/5 rounded-xl p-4 flex flex-col h-[260px]">
                <div className="flex justify-between items-center border-b border-white/5 pb-2 mb-2">
                  <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
                    <Users className="h-3.5 w-3.5 text-red-500" /> DETECTED SELLERS
                  </span>
                  <Badge tone="destructive" className="text-[8px]">{data.sellers.length} ACCTS</Badge>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 scrollbar-none text-[9px] text-text-secondary">
                  {data.sellers.map((s: any) => (
                    <div key={s.id} className="bg-[#0B0B0B] border border-white/5 rounded-lg p-2 flex flex-col gap-1">
                      <div className="flex justify-between items-center">
                        <span className="text-white font-bold text-[10px]">{s.display_name}</span>
                        <span className="text-red-400 font-bold">RISK: {s.risk_score}</span>
                      </div>
                      <div className="grid grid-cols-2 text-[8px] text-text-tertiary">
                        <span>TG: {s.telegram_username}</span>
                        <span>IG: {s.instagram_handle}</span>
                        <span>WA: {s.whatsapp_number}</span>
                        <span>BOT PROB: {Math.round(s.bot_probability * 100)}%</span>
                      </div>
                    </div>
                  ))}
                  {data.sellers.length === 0 && (
                    <div className="text-text-tertiary text-center py-8">No sellers detected.</div>
                  )}
                </div>
              </div>

              {/* Detected Buyers */}
              <div className="bg-[#151515] border border-white/5 rounded-xl p-4 flex flex-col h-[260px]">
                <div className="flex justify-between items-center border-b border-white/5 pb-2 mb-2">
                  <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
                    <Users className="h-3.5 w-3.5 text-sky-400" /> DETECTED BUYERS
                  </span>
                  <Badge tone="warning" className="text-[8px]">{data.buyers.length} ACCTS</Badge>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 scrollbar-none text-[9px] text-text-secondary">
                  {data.buyers.map((b: any) => (
                    <div key={b.id} className="bg-[#0B0B0B] border border-white/5 rounded-lg p-2 flex flex-col gap-1">
                      <div className="flex justify-between items-center">
                        <span className="text-white font-bold text-[10px]">{b.display_name}</span>
                        <span className="text-sky-400 font-bold">RISK: {b.risk_score}</span>
                      </div>
                      <div className="grid grid-cols-2 text-[8px] text-text-tertiary">
                        <span>TG: {b.telegram_username}</span>
                        <span>IG: {b.instagram_handle}</span>
                        <span>WA: {b.whatsapp_number}</span>
                        <span>BOT PROB: {Math.round(b.bot_probability * 100)}%</span>
                      </div>
                    </div>
                  ))}
                  {data.buyers.length === 0 && (
                    <div className="text-text-tertiary text-center py-8">No buyers detected.</div>
                  )}
                </div>
              </div>
            </div>

            {/* Conversation Explorer Results */}
            <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col flex-1 min-h-[400px]">
              <div className="flex justify-between items-center border-b border-white/5 pb-3 mb-4">
                <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
                  <MessageSquare className="h-3.5 w-3.5 text-[#E56A21]" />
                  DETECTED CONVERSATIONS FOR "{query}"
                </span>
                <span className="text-[9px] text-text-tertiary">SHOWING {data.conversations.length} MATCHES</span>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3.5 pr-1 scrollbar-none">
                {data.conversations.map((c: any) => (
                  <div key={c.id} className="bg-[#0B0B0B] border border-white/5 rounded-xl p-4 flex flex-col gap-3 relative overflow-hidden">
                    {/* Platform highlight header */}
                    <div className="flex justify-between items-center border-b border-white/5 pb-2">
                      <div className="flex items-center gap-2">
                        <Badge
                          tone={
                            c.platform === "telegram"
                              ? "outline"
                              : c.platform === "whatsapp"
                              ? "success"
                              : "destructive"
                          }
                          className="text-[8px] uppercase tracking-wider"
                        >
                          {c.platform}
                        </Badge>
                        <span className="text-white text-[10px] font-bold">{c.display_name}</span>
                        <span className="text-text-tertiary text-[9px]">{c.username}</span>
                      </div>
                      <span className="text-text-tertiary text-[8px]">{c.timestamp}</span>
                    </div>

                    {/* Message body with highlighted slangs */}
                    <div className="text-text-primary text-[11px] leading-relaxed py-1">
                      {highlightText(c.message, data.overview?.aliases || [])}
                    </div>

                    {/* AI Reasoning summary */}
                    <div className="bg-[#121212] border border-white/5 p-2 rounded text-[9px] text-text-secondary leading-normal flex flex-col gap-1">
                      <div className="flex justify-between text-text-tertiary text-[8px] font-bold border-b border-white/5 pb-1">
                        <span>AI DETECTION EXPLAINABILITY (INTELLIGENCE REPORT)</span>
                        <span className="text-[#E56A21]">{Math.round(c.confidence * 100)}% CONFIDENCE</span>
                      </div>
                      <p className="mt-0.5">{c.reasoning}</p>
                      <div className="flex justify-between text-[8px] text-text-tertiary mt-1">
                        <span>BOT LIKELIHOOD: {Math.round(c.bot_probability * 100)}% ({c.bot_probability >= 0.7 ? "BOT" : "HUMAN"})</span>
                        <span>DETECTION HASH: {c.hash.substring(0, 16)}...</span>
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex justify-between items-center text-[8px] text-text-tertiary border-t border-white/5 pt-2">
                      <div className="flex gap-2">
                        {c.phone && <span>PHONE: {c.phone}</span>}
                        {c.wallet_address && <span>WALLET: {c.wallet_address.substring(0, 12)}...</span>}
                      </div>
                      <div className="flex gap-2">
                        <Badge tone={c.label === "seller" ? "destructive" : c.label === "buyer" ? "warning" : "outline"} className="text-[7.5px] uppercase">
                          {c.label}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
                {data.conversations.length === 0 && (
                  <div className="text-text-tertiary text-center py-20">
                    <Database className="h-8 w-8 opacity-20 mx-auto mb-2" />
                    <span>No conversations found matching search query.</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-text-tertiary text-center py-20 bg-[#151515] border border-white/5 rounded-xl">
          <Database className="h-8 w-8 opacity-20 mx-auto mb-2" />
          <span>Enter a drug name or slang in the explorer header to retrieve intelligence logs.</span>
        </div>
      )}
    </div>
  );
}
