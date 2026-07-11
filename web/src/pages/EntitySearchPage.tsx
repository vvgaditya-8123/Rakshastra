import { useState, useEffect, useMemo } from "react";
import {
  Users,
  Network,
  Phone,
  Mail,
  Wallet,
  Clock,
  MessageSquare
} from "lucide-react";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Input } from "@nous-research/ui/ui/components/input";
import { api } from "@/lib/api";

export default function EntitySearchPage() {
  const [identities, setIdentities] = useState<any[]>([]);
  const [conversations, setConversations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchVal, setSearchVal] = useState("");
  const [selectedEntity, setSelectedEntity] = useState<any>(null);

  useEffect(() => {
    async function load() {
      try {
        const [idRes, convRes] = await Promise.all([
          api.getNarcoticsIdentities().catch(() => []),
          api.searchNarcotics("").catch(() => null)
        ]);
        setIdentities(idRes || []);
        if (convRes && convRes.conversations) {
          setConversations(convRes.conversations);
        }
        if (idRes && idRes.length > 0) {
          setSelectedEntity(idRes[0]);
        }
      } catch (err) {
        console.error("Failed to load entities", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filteredEntities = useMemo(() => {
    if (!searchVal.trim()) return identities;
    const sLower = searchVal.toLowerCase().trim();
    return identities.filter(id => {
      const name = (id.name || "").toLowerCase();
      const phone = (id.phone || "").toLowerCase();
      const email = (id.email || "").toLowerCase();
      const wallets = id.wallets || [];
      const profiles = id.profiles || [];
      
      const matchesName = name.includes(sLower);
      const matchesPhone = phone.includes(sLower);
      const matchesEmail = email.includes(sLower);
      const matchesWallet = wallets.some((w: string) => w.toLowerCase().includes(sLower));
      const matchesProfile = profiles.some((p: any) => p.handle.toLowerCase().includes(sLower));
      
      return matchesName || matchesPhone || matchesEmail || matchesWallet || matchesProfile;
    });
  }, [identities, searchVal]);

  // Find all messages linked to any of the profiles of the selected entity
  const entityMessages = useMemo(() => {
    if (!selectedEntity || !conversations) return [];
    
    // Extract JIDs/handles to match
    const handles = selectedEntity.profiles.map((p: any) => p.handle.toLowerCase());
    if (selectedEntity.phone) handles.push(selectedEntity.phone.toLowerCase());
    
    const matched = conversations.filter(c => {
      const sender = (c.username || "").toLowerCase();
      const ph = (c.phone || "").toLowerCase();
      return handles.includes(sender) || handles.includes(ph);
    });

    // Sort by timestamp descending
    return matched.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [selectedEntity, conversations]);

  if (loading) {
    return (
      <div className="flex items-center justify-center flex-1 bg-[#0E0E0E]">
        <div className="flex flex-col items-center gap-3 font-mono text-text-tertiary">
          <div className="h-8 w-8 border-2 border-[#E56A21]/30 border-t-[#E56A21] rounded-full animate-spin" />
          <span className="text-xs tracking-wider uppercase">Gathering cross-platform footprints...</span>
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
            <Network className="h-3.5 w-3.5" />
            CROSS-PLATFORM FOOTPRINTS
          </span>
          <h1 className="text-white text-lg font-bold">UNIFIED SUSPECT DOSSIERS</h1>
        </div>
        <div className="flex gap-2 w-full md:w-auto min-w-[280px]">
          <Input
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            placeholder="Search phone, email, wallet, handle..."
            className="bg-[#0C0C0C] border-white/5 font-mono text-xs focus:border-[#E56A21]"
          />
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        
        {/* Left Side: Merged Entities List */}
        <div className="lg:col-span-1 flex flex-col gap-3 overflow-y-auto pr-1 scrollbar-none max-h-[600px]">
          <span className="text-text-tertiary uppercase text-[10px] font-bold tracking-widest pl-1 mb-1 block">Matched Operator Profiles ({filteredEntities.length})</span>
          {filteredEntities.map((id) => (
            <div
              key={id.id}
              onClick={() => setSelectedEntity(id)}
              className={`bg-[#151515] border rounded-xl p-4 flex flex-col gap-2 cursor-pointer transition-all duration-200 hover:border-[#E56A21]/30 ${
                selectedEntity?.id === id.id ? "border-[#E56A21] bg-[#1C1C1C]/60" : "border-white/5"
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="text-white font-bold text-xs">{id.name}</span>
                <Badge tone={id.role === "seller" ? "destructive" : "warning"} className="text-[7.5px] uppercase font-bold">
                  {id.role}
                </Badge>
              </div>
              <div className="flex items-center gap-2 mt-1">
                {id.profiles.map((p: any) => (
                  <Badge key={p.platform} tone="outline" className="text-[7px] lowercase font-courier">
                    {p.platform}
                  </Badge>
                ))}
              </div>
              <div className="border-t border-white/5 pt-2 mt-1 flex justify-between items-center text-[8px] text-text-tertiary">
                <span>RISK INDEX: <span className="text-red-500 font-bold">{id.risk_score}</span></span>
                <span>BOT PROB: {Math.round(id.bot_probability * 100)}%</span>
              </div>
            </div>
          ))}
          {filteredEntities.length === 0 && (
            <div className="text-text-tertiary text-center py-20 bg-[#151515] border border-white/5 rounded-xl">
              <Users className="h-8 w-8 opacity-20 mx-auto mb-2" />
              <span>No suspect profiles match your search filters.</span>
            </div>
          )}
        </div>

        {/* Right Side: Suspect Profile Dossier & Cross-Platform Message Timeline */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {selectedEntity ? (
            <>
              {/* Dossier Card */}
              <div className="bg-[#151515] border border-white/5 rounded-xl p-5 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-[150px] h-[150px] bg-[#E56A21]/5 rounded-full blur-[80px] pointer-events-none" />
                <div className="flex justify-between items-start border-b border-[#E56A21]/30 pb-3 mb-4">
                  <div>
                    <h2 className="text-white text-base font-bold uppercase">{selectedEntity.name}</h2>
                    <span className="text-text-tertiary text-[9px] uppercase tracking-wider block mt-0.5">Unified Intelligence Dossier ({selectedEntity.id})</span>
                  </div>
                  <div className="flex gap-2">
                    <Badge tone={selectedEntity.role === "seller" ? "destructive" : "warning"} className="text-[9px] font-bold uppercase py-1">
                      {selectedEntity.role.toUpperCase()}
                    </Badge>
                    <Badge tone={selectedEntity.is_bot ? "destructive" : "outline"} className="text-[9px] font-bold uppercase py-1">
                      {selectedEntity.is_bot ? "AUTOMATION TRIGGERED" : "HUMAN TELEMETRY"}
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-[10px] text-text-secondary leading-normal">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Phone className="h-3.5 w-3.5 text-[#E56A21] shrink-0" />
                      <div className="flex flex-col">
                        <span className="text-text-tertiary text-[8px]">CONSOLIDATED MOBILE</span>
                        <span className="text-white font-bold">{selectedEntity.phone || "No phone linked"}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Mail className="h-3.5 w-3.5 text-[#E56A21] shrink-0" />
                      <div className="flex flex-col">
                        <span className="text-text-tertiary text-[8px]">CONSOLIDATED EMAIL</span>
                        <span className="text-white font-bold">{selectedEntity.email || "No email linked"}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Wallet className="h-3.5 w-3.5 text-[#E56A21] shrink-0" />
                      <div className="flex flex-col">
                        <span className="text-text-tertiary text-[8px]">CRYPTO WALLET ADDRESS</span>
                        <span className="text-purple-400 font-courier font-bold text-[9px] break-all">{selectedEntity.wallets?.[0] || "No wallet linked"}</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3 border-t md:border-t-0 md:border-l border-white/5 pt-3 md:pt-0 md:pl-6">
                    <div className="flex flex-col gap-1">
                      <span className="text-text-tertiary text-[8px] uppercase">Cross-platform profile correlation</span>
                      <div className="flex flex-col gap-1.5 mt-1 font-courier text-[9px]">
                        {selectedEntity.profiles.map((p: any) => (
                          <div key={p.platform} className="flex justify-between items-center bg-[#0C0C0C] border border-white/5 rounded px-2.5 py-1">
                            <span className="text-[#E56A21] uppercase font-bold">{p.platform}:</span>
                            <span className="text-white font-bold">{p.handle}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Suspect Activity Timeline across platforms */}
              <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col flex-1 min-h-[300px]">
                <div className="flex justify-between items-center border-b border-white/5 pb-3 mb-4">
                  <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5 text-[#E56A21]" />
                    CROSS-PLATFORM TRANSMISSION LOG TIMELINE
                  </span>
                  <Badge tone="success" className="text-[8px]">{entityMessages.length} CHATS</Badge>
                </div>

                <div className="flex-1 overflow-y-auto space-y-4 pr-1 scrollbar-none max-h-[300px]">
                  {entityMessages.map((msg) => (
                    <div key={msg.id} className="bg-[#0B0B0B] border border-white/5 rounded-lg p-3 flex flex-col gap-2 relative">
                      <div className="flex justify-between items-center text-[8px] text-text-tertiary border-b border-white/5 pb-1">
                        <div className="flex items-center gap-1.5">
                          <Badge tone="outline" className="text-[7.5px] uppercase">{msg.platform}</Badge>
                          <span className="text-text-tertiary font-mono">{msg.channel_or_group || "Direct Message"}</span>
                        </div>
                        <span>{msg.timestamp}</span>
                      </div>
                      <p className="text-text-primary text-[10.5px] italic leading-normal">"{msg.message}"</p>
                      <div className="flex justify-between items-center text-[7.5px] text-text-tertiary border-t border-white/5 pt-1.5 mt-0.5">
                        <span>DETECTOR SCORE: {Math.round(msg.confidence * 100)}% CONFIDENCE</span>
                        <span className="text-red-400 font-bold uppercase">{msg.drug_mention} matched</span>
                      </div>
                    </div>
                  ))}
                  {entityMessages.length === 0 && (
                    <div className="text-text-tertiary text-center py-10">
                      <MessageSquare className="h-6 w-6 opacity-20 mx-auto mb-2" />
                      <span>No communications captured from linked profiles.</span>
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-text-tertiary text-xs">
              <Users className="h-8 w-8 opacity-20 mb-2" />
              <span>Select an operator profile in the suspects list to retrieve detailed intelligence dossiers.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
