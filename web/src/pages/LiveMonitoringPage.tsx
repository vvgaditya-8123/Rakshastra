import { useState, useEffect, useMemo } from "react";
import {
  Activity,
  MessageSquare,
  SlidersHorizontal,
  Info
} from "lucide-react";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Input } from "@nous-research/ui/ui/components/input";
import { api } from "@/lib/api";

export default function LiveMonitoringPage() {
  const [conversations, setConversations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedChat, setSelectedChat] = useState<any>(null);
  
  // Filters
  const [searchVal, setSearchVal] = useState("");
  const [selectedDrug, setSelectedDrug] = useState("ALL");
  const [selectedLabel, setSelectedLabel] = useState("ALL");
  const [selectedPlatform, setSelectedPlatform] = useState("ALL");

  useEffect(() => {
    async function loadData() {
      try {
        const evRes = await api.getNarcoticsEvidence().catch(() => []);
        // Get all conversations
        const res = await api.searchNarcotics("").catch(() => null);
        
        // Combine them to get a comprehensive list
        let list: any[] = evRes || [];
        if (res && res.conversations) {
          // Merge lists and remove duplicates
          const seen = new Set(list.map(c => c.id || c.conv_id));
          res.conversations.forEach((c: any) => {
            const cid = c.id || c.conv_id;
            if (cid && !seen.has(cid)) {
              list.push(c);
            }
          });
        }
        
        // Sort by timestamp descending
        list.sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        setConversations(list);
      } catch (err) {
        console.error("Failed to load live monitor logs", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
    const timer = setInterval(loadData, 8000);
    return () => clearInterval(timer);
  }, []);

  const filteredConversations = useMemo(() => {
    return conversations.filter(c => {
      const msg = (c.message || "").toLowerCase();
      const sender = (c.display_name || "").toLowerCase();
      const username = (c.username || "").toLowerCase();
      const sLower = searchVal.toLowerCase();
      
      const matchesSearch = msg.includes(sLower) || sender.includes(sLower) || username.includes(sLower);
      const matchesDrug = selectedDrug === "ALL" || (c.drug && c.drug.toUpperCase() === selectedDrug) || (c.drug_mention && c.drug_mention.toUpperCase() === selectedDrug);
      const matchesLabel = selectedLabel === "ALL" || (c.label && c.label.toLowerCase() === selectedLabel.toLowerCase());
      const matchesPlatform = selectedPlatform === "ALL" || (c.platform && c.platform.toLowerCase() === selectedPlatform.toLowerCase());
      
      return matchesSearch && matchesDrug && matchesLabel && matchesPlatform;
    });
  }, [conversations, searchVal, selectedDrug, selectedLabel, selectedPlatform]);

  if (loading) {
    return (
      <div className="flex items-center justify-center flex-1 bg-[#0E0E0E]">
        <div className="flex flex-col items-center gap-3 font-mono text-text-tertiary">
          <div className="h-8 w-8 border-2 border-[#E56A21]/30 border-t-[#E56A21] rounded-full animate-spin" />
          <span className="text-xs tracking-wider uppercase">Connecting to Multilingual Probes...</span>
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
            <Activity className="h-3.5 w-3.5 animate-pulse" />
            LIVE TRAFFIC MONITORS
          </span>
          <h1 className="text-white text-lg font-bold">MULTILINGUAL CONVERSATION STREAM</h1>
        </div>
        
        <div className="flex gap-2 w-full md:w-auto min-w-[280px]">
          <Input
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            placeholder="Search keywords, users, phone..."
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

        {/* Drug filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-text-tertiary">Drug:</span>
          <select
            value={selectedDrug}
            onChange={(e) => setSelectedDrug(e.target.value)}
            className="bg-[#0C0C0C] border border-white/5 text-white rounded px-2.5 py-1"
          >
            <option value="ALL">ALL DRUGS</option>
            <option value="MDMA">MDMA</option>
            <option value="LSD">LSD</option>
            <option value="COCAINE">COCAINE</option>
            <option value="CANNABIS">CANNABIS</option>
            <option value="MEPHEDRONE">MEPHEDRONE</option>
            <option value="HEROIN">HEROIN</option>
          </select>
        </div>

        {/* Intent Label filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-text-tertiary">Intent:</span>
          <select
            value={selectedLabel}
            onChange={(e) => setSelectedLabel(e.target.value)}
            className="bg-[#0C0C0C] border border-white/5 text-white rounded px-2.5 py-1"
          >
            <option value="ALL">ALL INTENTS</option>
            <option value="SELLER">SELLER</option>
            <option value="BUYER">BUYER</option>
            <option value="NEUTRAL">NEUTRAL</option>
            <option value="SPAM">SPAM/BOT</option>
          </select>
        </div>

        {/* Platform filter */}
        <div className="flex items-center gap-1.5">
          <span className="text-text-tertiary">Platform:</span>
          <select
            value={selectedPlatform}
            onChange={(e) => setSelectedPlatform(e.target.value)}
            className="bg-[#0C0C0C] border border-white/5 text-white rounded px-2.5 py-1"
          >
            <option value="ALL">ALL PLATFORMS</option>
            <option value="TELEGRAM">TELEGRAM</option>
            <option value="WHATSAPP">WHATSAPP</option>
            <option value="INSTAGRAM">INSTAGRAM</option>
          </select>
        </div>

        <span className="ml-auto text-text-tertiary text-[10px]">
          SHOWING {filteredConversations.length} OF {conversations.length} RECORDED CHATS
        </span>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        
        {/* Left Side: Live Feed List */}
        <div className="lg:col-span-2 flex flex-col gap-4 overflow-y-auto pr-1 scrollbar-none max-h-[600px]">
          {filteredConversations.map((chat) => {
            const isSeller = chat.label === "seller";
            const isBuyer = chat.label === "buyer";
            
            return (
              <div
                key={chat.id || chat.conv_id}
                onClick={() => setSelectedChat(chat)}
                className={`bg-[#151515] border rounded-xl p-4 flex flex-col gap-2.5 cursor-pointer transition-all duration-200 hover:border-[#E56A21]/30 ${
                  selectedChat?.id === chat.id || selectedChat?.conv_id === chat.conv_id
                    ? "border-[#E56A21] bg-[#1C1C1C]/60"
                    : "border-white/5"
                }`}
              >
                <div className="flex justify-between items-center border-b border-white/5 pb-2">
                  <div className="flex items-center gap-2">
                    <Badge
                      tone={
                        chat.platform === "telegram"
                          ? "outline"
                          : chat.platform === "whatsapp"
                          ? "success"
                          : "destructive"
                      }
                      className="text-[7.5px] uppercase tracking-wider"
                    >
                      {chat.platform}
                    </Badge>
                    <span className="text-white font-bold text-[10px]">{chat.display_name}</span>
                    <span className="text-text-tertiary text-[8.5px]">{chat.username}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-text-tertiary text-[8px]">
                      {chat.timestamp ? new Date(chat.timestamp).toLocaleTimeString() : "N/A"}
                    </span>
                    <Badge
                      tone={isSeller ? "destructive" : isBuyer ? "warning" : "outline"}
                      className="text-[7.5px] uppercase tracking-widest font-bold"
                    >
                      {chat.label || "user"}
                    </Badge>
                  </div>
                </div>

                <p className="text-text-primary text-[10.5px] leading-relaxed italic">
                  "{chat.message}"
                </p>

                <div className="flex justify-between items-center text-[8px] text-text-tertiary border-t border-white/5 pt-2">
                  <div className="flex gap-3">
                    {chat.drug && <span>TARGET: <span className="text-[#E56A21] font-bold">{chat.drug}</span></span>}
                    {chat.phone && <span>PHONE: {chat.phone}</span>}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[7.5px]">CONFIDENCE:</span>
                    <span className="text-white font-bold">{Math.round((chat.confidence || 0) * 100)}%</span>
                  </div>
                </div>
              </div>
            );
          })}
          {filteredConversations.length === 0 && (
            <div className="text-text-tertiary text-center py-20 bg-[#151515] border border-white/5 rounded-xl">
              <MessageSquare className="h-8 w-8 opacity-20 mx-auto mb-2" />
              <span>No conversations match filters.</span>
            </div>
          )}
        </div>

        {/* Right Side: Deep Intelligence Inspector */}
        <div className="lg:col-span-1 bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col max-h-[600px] overflow-y-auto scrollbar-none">
          <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5 mb-3 border-b border-white/5 pb-3">
            <Info className="h-3.5 w-3.5 text-[#E56A21]" />
            INTELLIGENCE DEEP ANALYSIS
          </span>

          {selectedChat ? (
            <div className="flex flex-col gap-4 text-[10px] text-text-secondary">
              <div className="flex justify-between items-center border-b border-white/5 pb-2">
                <div>
                  <span className="text-white text-xs font-bold block">{selectedChat.display_name}</span>
                  <span className="text-text-tertiary text-[9px]">{selectedChat.username}</span>
                </div>
                <Badge tone={selectedChat.label === "seller" ? "destructive" : "warning"} className="text-[7.5px] uppercase">
                  {selectedChat.label?.toUpperCase() || "USER"}
                </Badge>
              </div>

              <div className="space-y-2 border-b border-white/5 pb-3">
                <div className="flex justify-between">
                  <span className="text-text-tertiary">PLATFORM:</span>
                  <span className="text-white uppercase font-bold">{selectedChat.platform}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-tertiary">TIMESTAMP:</span>
                  <span className="text-white">{new Date(selectedChat.timestamp).toLocaleString()}</span>
                </div>
                {selectedChat.phone && (
                  <div className="flex justify-between">
                    <span className="text-text-tertiary">PHONE:</span>
                    <span className="text-white font-bold">{selectedChat.phone}</span>
                  </div>
                )}
                {selectedChat.email && (
                  <div className="flex justify-between">
                    <span className="text-text-tertiary">EMAIL:</span>
                    <span className="text-white truncate max-w-[150px]">{selectedChat.email}</span>
                  </div>
                )}
                {selectedChat.location && (
                  <div className="flex justify-between">
                    <span className="text-text-tertiary">DETECTED LOCATION:</span>
                    <span className="text-white font-bold">{selectedChat.location}</span>
                  </div>
                )}
                {selectedChat.wallet_address && (
                  <div className="flex flex-col gap-0.5 mt-1">
                    <span className="text-text-tertiary">CRYPTO WALLET:</span>
                    <span className="text-purple-400 font-courier break-all text-[8.5px]">{selectedChat.wallet_address}</span>
                  </div>
                )}
              </div>

              {/* AI Explainability */}
              <div className="flex flex-col gap-1 border-b border-white/5 pb-3">
                <span className="text-text-tertiary text-[9px] font-bold uppercase tracking-wider">AI explainability (reasoning)</span>
                <p className="leading-relaxed text-text-primary text-[9.5px] bg-[#0C0C0C] border border-white/5 p-2 rounded">
                  {selectedChat.reasoning}
                </p>
                <div className="flex justify-between text-[8px] text-text-tertiary mt-1">
                  <span>Matched Drug: {selectedChat.drug || selectedChat.drug_mention || "N/A"}</span>
                  <span>Confidence: {Math.round((selectedChat.confidence || 0) * 100)}%</span>
                </div>
              </div>

              {/* Bot Detection Metrics */}
              <div className="flex flex-col gap-1">
                <span className="text-text-tertiary text-[9px] font-bold uppercase tracking-wider">Bot / automation analysis</span>
                <p className="leading-relaxed text-text-primary text-[9.5px] bg-[#0C0C0C] border border-white/5 p-2 rounded">
                  {selectedChat.bot_detection_reason || "Automated response rate and template matching within normal human profiles."}
                </p>
                <div className="flex justify-between items-center text-[8px] text-text-tertiary mt-2">
                  <span>BOT PROBABILITY: {Math.round((selectedChat.bot_probability || 0) * 100)}%</span>
                  <Badge tone={selectedChat.bot_probability >= 0.7 ? "destructive" : "outline"} className="text-[7px]">
                    {selectedChat.bot_probability >= 0.7 ? "AUTOMATION LIKELY" : "HUMAN TELEMETRY"}
                  </Badge>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-text-tertiary text-xs">
              <MessageSquare className="h-6 w-6 opacity-30 mb-2" />
              <span>Select any message in the feed to inspect prosecution indicators.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
