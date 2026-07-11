import { useState, useEffect, useMemo } from "react";
import {
  ShieldAlert,
  Check,
  SlidersHorizontal
} from "lucide-react";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";
import { Input } from "@nous-research/ui/ui/components/input";
import { api } from "@/lib/api";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<any>(null);
  
  // Filters
  const [searchVal, setSearchVal] = useState("");
  const [drugFilter, setDrugFilter] = useState("ALL");
  const [resolvedIds, setResolvedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getNarcoticsAnalytics().catch(() => null);
        if (res && res.critical_alerts) {
          // Add some medium/high alerts as well to pad the list
          const formatted = res.critical_alerts.map((al: any) => ({
            ...al,
            severity: al.risk_score >= 85 ? "CRITICAL" : "HIGH"
          }));
          setAlerts(formatted);
          if (formatted.length > 0) {
            setSelectedAlert(formatted[0]);
          }
        }
      } catch (err) {
        console.error("Alerts load failed", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filteredAlerts = useMemo(() => {
    return alerts.filter(al => {
      const isResolved = resolvedIds.has(al.id);
      if (isResolved) return false;

      const user = (al.username || "").toLowerCase();
      const text = (al.message || "").toLowerCase();
      const sLower = searchVal.toLowerCase();
      
      const matchesSearch = user.includes(sLower) || text.includes(sLower);
      const matchesDrug = drugFilter === "ALL" || (al.drug_mention && al.drug_mention.toUpperCase() === drugFilter);
      return matchesSearch && matchesDrug;
    });
  }, [alerts, searchVal, drugFilter, resolvedIds]);

  const handleResolve = (id: string) => {
    setResolvedIds(prev => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
    if (selectedAlert?.id === id) {
      setSelectedAlert(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center flex-1 bg-[#0E0E0E]">
        <div className="flex flex-col items-center gap-3 font-mono text-text-tertiary">
          <div className="h-8 w-8 border-2 border-[#E56A21]/30 border-t-[#E56A21] rounded-full animate-spin" />
          <span className="text-xs tracking-wider uppercase">Loading security dispatch queue...</span>
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
            <ShieldAlert className="h-3.5 w-3.5 animate-pulse text-red-500" />
            CRITICAL DISPATCH
          </span>
          <h1 className="text-white text-lg font-bold">THREAT ALERTS INBOX</h1>
        </div>
        <div className="flex gap-2 w-full md:w-auto min-w-[280px]">
          <Input
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            placeholder="Search alerts, user, text..."
            className="bg-[#0C0C0C] border-white/5 font-mono text-xs focus:border-[#E56A21]"
          />
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-[#151515] border border-white/5 rounded-xl p-4 flex flex-wrap gap-4 items-center text-xs text-text-secondary">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="h-3.5 w-3.5 text-[#E56A21]" />
          <span className="text-text-tertiary uppercase text-[10px] font-bold">Filters:</span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-text-tertiary">Drug Target:</span>
          <select
            value={drugFilter}
            onChange={(e) => setDrugFilter(e.target.value)}
            className="bg-[#0C0C0C] border border-white/5 text-white rounded px-2.5 py-1"
          >
            <option value="ALL">ALL DRUGS</option>
            <option value="MDMA">MDMA</option>
            <option value="LSD">LSD</option>
            <option value="COCAINE">COCAINE</option>
            <option value="CANNABIS">CANNABIS</option>
            <option value="MEPHEDRONE">MEPHEDRONE</option>
          </select>
        </div>

        <span className="ml-auto text-text-tertiary text-[10px]">
          ACTIVE ALERTS: {filteredAlerts.length}
        </span>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        
        {/* Left Side: Alerts List */}
        <div className="lg:col-span-2 flex flex-col gap-4 overflow-y-auto pr-1 scrollbar-none max-h-[600px]">
          {filteredAlerts.map((al) => {
            const isCritical = al.severity === "CRITICAL";
            return (
              <div
                key={al.id}
                onClick={() => setSelectedAlert(al)}
                className={`bg-[#151515] border rounded-xl p-4 flex flex-col gap-2.5 cursor-pointer transition-all duration-200 hover:border-[#E56A21]/30 ${
                  selectedAlert?.id === al.id ? "border-[#E56A21] bg-[#1C1C1C]/60" : "border-white/5"
                }`}
              >
                <div className="flex justify-between items-center border-b border-white/5 pb-2">
                  <div className="flex items-center gap-2">
                    <Badge tone={isCritical ? "destructive" : "warning"} className="text-[7.5px] uppercase font-bold tracking-widest">
                      {al.severity}
                    </Badge>
                    <span className="text-white font-bold text-[10px]">{al.display_name}</span>
                    <span className="text-text-tertiary text-[8.5px]">{al.username}</span>
                  </div>
                  <span className="text-text-tertiary text-[8px]">{al.timestamp}</span>
                </div>

                <p className="text-text-primary text-[10.5px] leading-relaxed italic">
                  "{al.message}"
                </p>

                <div className="flex justify-between items-center border-t border-white/5 pt-2 mt-1 text-[8px] text-text-tertiary">
                  <div className="flex gap-3">
                    <span>PLATFORM: <span className="text-white uppercase font-bold">{al.platform}</span></span>
                    <span>DRUG: <span className="text-[#E56A21] font-bold">{al.drug_mention}</span></span>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleResolve(al.id); }}
                      className="flex items-center gap-1 bg-emerald-500/15 border border-emerald-500/30 hover:bg-emerald-500/35 text-emerald-400 px-2 py-0.5 rounded text-[8px] cursor-pointer"
                    >
                      <Check className="h-2.5 w-2.5" /> RESOLVE
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
          {filteredAlerts.length === 0 && (
            <div className="text-text-tertiary text-center py-20 bg-[#151515] border border-white/5 rounded-xl">
              <ShieldAlert className="h-8 w-8 opacity-20 mx-auto mb-2" />
              <span>No active threats inside the queue.</span>
            </div>
          )}
        </div>

        {/* Right Side: Deep Alert Inspector */}
        <div className="lg:col-span-1 bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col max-h-[600px] overflow-y-auto scrollbar-none justify-between">
          {selectedAlert ? (
            <div className="flex flex-col gap-4 text-[10px] text-text-secondary">
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <div>
                  <span className="text-white text-xs font-bold block">{selectedAlert.id}</span>
                  <span className="text-text-tertiary text-[9px] uppercase mt-0.5 block">Alert Reference</span>
                </div>
                <Badge tone={selectedAlert.severity === "CRITICAL" ? "destructive" : "warning"} className="text-[7.5px]">
                  RISK: {selectedAlert.risk_score}%
                </Badge>
              </div>

              <div className="space-y-2 border-b border-white/5 pb-3">
                <div className="flex justify-between">
                  <span className="text-text-tertiary">USER IDENTITY:</span>
                  <span className="text-white font-bold">{selectedAlert.display_name} ({selectedAlert.username})</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-tertiary">SOURCE CHANNEL:</span>
                  <span className="text-white font-bold">{selectedAlert.channel_or_group || "Direct Message"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-tertiary">TIMESTAMP:</span>
                  <span className="text-white">{selectedAlert.timestamp}</span>
                </div>
                {selectedAlert.phone && (
                  <div className="flex justify-between">
                    <span className="text-text-tertiary">CONTACT NUMBER:</span>
                    <span className="text-white font-bold">{selectedAlert.phone}</span>
                  </div>
                )}
                {selectedAlert.email && (
                  <div className="flex justify-between">
                    <span className="text-text-tertiary">EMAIL ADDRESS:</span>
                    <span className="text-white">{selectedAlert.email}</span>
                  </div>
                )}
              </div>

              {/* Explainability */}
              <div className="flex flex-col gap-1.5 border-b border-white/5 pb-3">
                <span className="text-text-tertiary text-[8.5px] uppercase font-bold tracking-wider">AI explainability (reasoning)</span>
                <p className="leading-relaxed text-text-primary text-[9.5px] bg-[#0C0C0C] border border-white/5 p-2 rounded">
                  {selectedAlert.reasoning}
                </p>
                <div className="flex justify-between text-[8px] text-text-tertiary mt-1">
                  <span>Target Slang: {selectedAlert.slang || "N/A"}</span>
                  <span>Confidence: {Math.round(selectedAlert.confidence * 100)}%</span>
                </div>
              </div>

              {/* Bot probability */}
              <div className="flex justify-between items-center">
                <span className="text-text-tertiary">BOT PROBABILITY:</span>
                <span className="text-white font-bold">{Math.round(selectedAlert.bot_probability * 100)}%</span>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-text-tertiary text-xs">
              <ShieldAlert className="h-6 w-6 opacity-30 mb-2" />
              <span>Select a dispatch alert to retrieve forensic breakdowns.</span>
            </div>
          )}

          {selectedAlert && (
            <div className="flex gap-2 border-t border-white/5 pt-3 mt-4">
              <Button
                onClick={() => handleResolve(selectedAlert.id)}
                className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[9px] py-1.5"
              >
                RESOLVE THREAT
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
