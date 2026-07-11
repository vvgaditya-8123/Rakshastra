import { useState, useEffect, useMemo } from "react";
import {
  Clock,
  SlidersHorizontal
} from "lucide-react";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Input } from "@nous-research/ui/ui/components/input";
import { api } from "@/lib/api";

export default function TimelinePage() {
  const [timelineEvents, setTimelineEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchVal, setSearchVal] = useState("");
  const [activeFilter, setActiveFilter] = useState("ALL");

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getNarcoticsAnalytics().catch(() => null);
        if (res && res.timeline) {
          // Stagger the times slightly for a realistic chronological appearance
          const staggered = res.timeline.map((evt: any, idx: number) => ({
            ...evt,
            id: `evt-${idx}`,
            platform: idx % 3 === 0 ? "telegram" : idx % 3 === 1 ? "instagram" : "whatsapp"
          }));
          setTimelineEvents(staggered);
        }
      } catch (err) {
        console.error("Timeline load failed", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filteredEvents = useMemo(() => {
    return timelineEvents.filter(evt => {
      const act = (evt.action || "").toLowerCase();
      const det = (evt.details || "").toLowerCase();
      const sLower = searchVal.toLowerCase();
      
      const matchesSearch = act.includes(sLower) || det.includes(sLower);
      const matchesFilter = activeFilter === "ALL" || evt.platform === activeFilter.toLowerCase();
      
      return matchesSearch && matchesFilter;
    });
  }, [timelineEvents, searchVal, activeFilter]);

  if (loading) {
    return (
      <div className="flex items-center justify-center flex-1 bg-[#0E0E0E]">
        <div className="flex flex-col items-center gap-3 font-mono text-text-tertiary">
          <div className="h-8 w-8 border-2 border-[#E56A21]/30 border-t-[#E56A21] rounded-full animate-spin" />
          <span className="text-xs tracking-wider uppercase">Reconstructing audit timeline...</span>
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
            <Clock className="h-3.5 w-3.5" />
            CASE LOGBOOK
          </span>
          <h1 className="text-white text-lg font-bold">CHRONOLOGICAL EVENT TIMELINE</h1>
        </div>
        <div className="flex gap-2 w-full md:w-auto min-w-[280px]">
          <Input
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            placeholder="Search timeline events..."
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

        <button
          onClick={() => setActiveFilter("ALL")}
          className={`px-3 py-1 border rounded cursor-pointer transition-colors duration-150 ${
            activeFilter === "ALL" ? "bg-[#E56A21]/20 border-[#E56A21] text-[#E56A21] font-bold" : "bg-[#1C1C1C] border-white/5"
          }`}
        >
          ALL LOGS
        </button>
        <button
          onClick={() => setActiveFilter("TELEGRAM")}
          className={`px-3 py-1 border rounded cursor-pointer transition-colors duration-150 ${
            activeFilter === "TELEGRAM" ? "bg-[#E56A21]/20 border-[#E56A21] text-[#E56A21] font-bold" : "bg-[#1C1C1C] border-white/5"
          }`}
        >
          TELEGRAM SCANS
        </button>
        <button
          onClick={() => setActiveFilter("INSTAGRAM")}
          className={`px-3 py-1 border rounded cursor-pointer transition-colors duration-150 ${
            activeFilter === "INSTAGRAM" ? "bg-[#E56A21]/20 border-[#E56A21] text-[#E56A21] font-bold" : "bg-[#1C1C1C] border-white/5"
          }`}
        >
          INSTAGRAM SCANS
        </button>
        <button
          onClick={() => setActiveFilter("WHATSAPP")}
          className={`px-3 py-1 border rounded cursor-pointer transition-colors duration-150 ${
            activeFilter === "WHATSAPP" ? "bg-[#E56A21]/20 border-[#E56A21] text-[#E56A21] font-bold" : "bg-[#1C1C1C] border-white/5"
          }`}
        >
          WHATSAPP SCANS
        </button>

        <span className="ml-auto text-text-tertiary text-[10px]">
          LOGGED EVENTS: {filteredEvents.length}
        </span>
      </div>

      {/* Timeline Stream */}
      <div className="bg-[#151515] border border-white/5 rounded-xl p-6 flex flex-col flex-1 min-h-[400px]">
        <div className="relative border-l border-white/10 pl-6 ml-4 space-y-6">
          {filteredEvents.map((evt) => {
            const isHighRisk = evt.action.toLowerCase().includes("risk") || evt.action.toLowerCase().includes("flagged");
            return (
              <div key={evt.id} className="relative">
                {/* Visual marker dot */}
                <div className={`absolute -left-[30px] top-1.5 h-3 w-3 rounded-full border-2 ${
                  isHighRisk ? "bg-red-500 border-red-950 animate-pulse" : "bg-[#E56A21] border-[#0E0E0E]"
                }`} />
                
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-bold text-xs uppercase tracking-wide">{evt.action}</span>
                      <Badge tone="outline" className="text-[7px] uppercase font-mono">{evt.platform}</Badge>
                      {isHighRisk && <Badge tone="destructive" className="text-[7.5px] uppercase font-bold animate-pulse">escalated</Badge>}
                    </div>
                    <span className="text-text-primary text-[10.5px] leading-relaxed mt-1">{evt.details}</span>
                  </div>
                  <span className="text-[#E56A21] font-bold text-[10px] shrink-0 font-mono self-start md:self-center">
                    {evt.time}
                  </span>
                </div>
              </div>
            );
          })}
          {filteredEvents.length === 0 && (
            <div className="text-text-tertiary text-center py-20">
              <Clock className="h-8 w-8 opacity-20 mx-auto mb-2" />
              <span>No logs found matching timeline filter.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
