import { useState, useEffect, Fragment } from "react";
import {
  ShieldAlert,
  Search,
  Activity,
  Network,
  Cpu,
  Terminal,
  AlertTriangle,
  Play,
  RotateCcw,
  CheckCircle,
  Sliders,
  Globe,
  Database
} from "lucide-react";
import { api } from "@/lib/api";

// Default TTPs for quick selection
const AVAILABLE_TTPS = [
  { id: "T1566.001", name: "Spearphishing Attachment", tactic: "Initial Access" },
  { id: "T1566.002", name: "Spearphishing Link", tactic: "Initial Access" },
  { id: "T1190", name: "Exploit Public Application", tactic: "Initial Access" },
  { id: "T1059.001", name: "PowerShell Execution", tactic: "Execution" },
  { id: "T1053", name: "Scheduled Task/Job", tactic: "Execution" },
  { id: "T1547.001", name: "Registry Run Keys", tactic: "Persistence" },
  { id: "T1505.003", name: "Web Shell", tactic: "Persistence" },
  { id: "T1003.001", name: "LSASS Credential Dumping", tactic: "Credential Access" },
  { id: "T1021.001", name: "Remote Desktop Protocol", tactic: "Lateral Movement" },
  { id: "T1021.002", name: "SMB/Windows Admin Shares", tactic: "Lateral Movement" },
  { id: "T1071.001", name: "Web C2 Protocols (HTTP/S)", tactic: "Command and Control" },
  { id: "T1572", name: "Protocol Tunneling (DNS)", tactic: "Command and Control" },
  { id: "T1041", name: "Exfiltration over C2", tactic: "Exfiltration" },
  { id: "T1486", name: "Data Encrypted (Ransomware)", tactic: "Impact" },
];

export default function APTDashboardPage() {
  // Tabs: 'analysis' | 'graph' | 'intel' | 'soar' | 'ueba'
  const [activeTab, setActiveTab] = useState<"analysis" | "graph" | "intel" | "soar" | "ueba">("analysis");

  // Input states
  const [selectedTTPs, setSelectedTTPs] = useState<string[]>(["T1566.001", "T1059.001"]);
  const [iocInput, setIocInput] = useState<string>("avsvmcloud.com, badnews.dll");
  const [targetSector, setTargetSector] = useState<string>("government");
  const [targetCountry, setTargetCountry] = useState<string>("India");

  // Analysis result states
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // RAG states
  const [ragQuery, setRagQuery] = useState<string>("SideWinder CERT-In");
  const [ragSearchType, setRagSearchType] = useState<string>("general");
  const [ragResults, setRagResults] = useState<any[]>([]);
  const [ragLoading, setRagLoading] = useState(false);

  // SOAR states
  const [incidents, setIncidents] = useState<any[]>([]);
  const [activeIncident, setActiveIncident] = useState<any>(null);
  const [incidentActions, setIncidentActions] = useState<any[]>([]);
  const [soarLoading, setSoarLoading] = useState(false);

  // Attack Graph states
  const [graphPaths, setGraphPaths] = useState<any>(null);
  const [chokepoints, setChokepoints] = useState<any[]>([]);
  const [entryPoint, setEntryPoint] = useState<string>("workstation-01");
  const [targetAsset, setTargetAsset] = useState<string>("domain-controller");
  const [graphLoading, setGraphLoading] = useState(false);

  // UEBA states
  const [uebaEntity, setUebaEntity] = useState<string>("user-admin-01");
  const [uebaPatterns, setUebaPatterns] = useState<any>(null);
  const [uebaTimeline, setUebaTimeline] = useState<any[]>([]);
  const [uebaLoading, setUebaLoading] = useState(false);

  // Load initial data
  useEffect(() => {
    runAnalysis();
    loadIncidents();
    loadChokepoints();
    runRagSearch();
    runUebaScan();
  }, []);

  // ── Actions ─────────────────────────────────────────────────────────

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const iocs = iocInput.split(",").map(i => i.trim()).filter(Boolean);
      const res = await api.aptFullAnalysis({
        observed_ttps: selectedTTPs,
        observed_iocs: iocs,
        target_sector: targetSector || undefined,
        target_country: targetCountry || undefined,
        org_assets: [
          { name: "workstation-01", asset_type: "host", properties: { os: "Windows 11", EDR: true } },
          { name: "web-server-02", asset_type: "web_server", properties: { os: "Ubuntu 22.04", WAF: true } },
          { name: "domain-controller", asset_type: "host", properties: { os: "Windows Server 2022", mfa_enabled: false } }
        ],
        create_incident: true
      });
      setAnalysisResult(res);
      // Reload incidents list to reflect newly created incident
      loadIncidents();
    } catch (err) {
      console.error("APT Analysis failed", err);
    } finally {
      setLoading(false);
    }
  };


  const loadIncidents = async () => {
    try {
      const incs = await api.soarGetIncidents();
      setIncidents(incs || []);
      if (incs && incs.length > 0 && !activeIncident) {
        selectIncident(incs[0].id || incs[0].incident_id);
      }
    } catch (err) {
      console.error("Failed to load incidents", err);
    }
  };

  const selectIncident = async (id: string) => {
    try {
      const inc = await api.soarGetIncident(id);
      setActiveIncident(inc);
      const actions = await api.soarGetIncidentActions(id);
      setIncidentActions(actions || []);
    } catch (err) {
      console.error("Failed to load incident detail", err);
    }
  };

  const executePlaybook = async (incidentId: string, mode: string) => {
    setSoarLoading(true);
    try {
      await api.soarExecutePlaybook({ incident_id: incidentId, mode });
      // Refresh current incident actions
      selectIncident(incidentId);
      loadIncidents();
    } catch (err) {
      console.error("Playbook execution failed", err);
    } finally {
      setSoarLoading(false);
    }
  };

  const runRagSearch = async () => {
    setRagLoading(true);
    try {
      const res = await api.threatIntelSearch({
        query: ragQuery,
        search_type: ragSearchType,
        top_k: 10
      });
      setRagResults(res || []);
    } catch (err) {
      console.error("RAG search failed", err);
    } finally {
      setRagLoading(false);
    }
  };

  const loadChokepoints = async () => {
    try {
      const pts = await api.attackGraphChokepoints();
      setChokepoints(pts || []);
    } catch (err) {
      console.error("Failed to load chokepoints", err);
    }
  };

  const runGraphPathAnalysis = async () => {
    if (!entryPoint || !targetAsset) return;
    setGraphLoading(true);
    try {
      const res = await api.attackGraphPaths({
        entry_point_id: entryPoint,
        target_id: targetAsset,
        max_depth: 8
      });
      setGraphPaths(res);
    } catch (err) {
      console.error("Attack path analysis failed", err);
    } finally {
      setGraphLoading(false);
    }
  };

  const runUebaScan = async () => {
    if (!uebaEntity) return;
    setUebaLoading(true);
    try {
      const patterns = await api.uebaGetAptPatterns(uebaEntity);
      setUebaPatterns(patterns);
      const timeline = await api.uebaGetRiskTimeline(uebaEntity);
      setUebaTimeline(timeline || []);
    } catch (err) {
      console.error("UEBA scan failed", err);
    } finally {
      setUebaLoading(false);
    }
  };

  const toggleTTP = (id: string) => {
    setSelectedTTPs(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    );
  };

  return (
    <div className="flex flex-col gap-6 p-6 min-h-0 min-w-0 flex-1 overflow-y-auto text-text-primary bg-[#0E0E0E] font-mono select-none">
      
      {/* ── HEADER ── */}
      <div className="bg-[#151515] border border-white/5 rounded-xl p-5 relative overflow-hidden flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-[#E56A21]/5 rounded-full blur-[100px] pointer-events-none" />
        <div className="flex-1 flex flex-col gap-1">
          <span className="text-[10px] tracking-widest text-[#E56A21] font-bold uppercase flex items-center gap-1.5 animate-pulse">
            <ShieldAlert className="h-4 w-4" />
            रक्षास्त्र (RAKSHASTRA) ACTIVE THREAT DEFENSE
          </span>
          <h1 className="text-white text-lg font-bold">APT CAMPAIGN ATTRIBUTION & PREDICTION SERVICE</h1>
          <p className="text-text-tertiary text-xs max-w-2xl mt-1">
            Predictive multi-agent threat hunting matrix matching observed indicators to threat actor TTPs, mapping lateral movement pathways, and executing automated containment protocols.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <div className="bg-[#1C1C1C] border border-white/5 px-3 py-1.5 rounded-lg flex flex-col text-right">
            <span className="text-[8px] text-text-tertiary uppercase">MODEL INSTANCE</span>
            <span className="text-white text-xs font-bold uppercase">Gemini 3.5</span>
          </div>
          <div className="bg-[#1C1C1C] border border-white/5 px-3 py-1.5 rounded-lg flex flex-col text-right">
            <span className="text-[8px] text-text-tertiary uppercase">KNOWLEDGE FRAMEWORK</span>
            <span className="text-[#E56A21] text-xs font-bold uppercase">MITRE ATT&CK v14</span>
          </div>
        </div>
      </div>

      {/* ── TABS NAVIGATION ── */}
      <div className="flex border-b border-white/5 gap-2 scrollbar-none overflow-x-auto pb-px">
        {[
          { id: "analysis", label: "CAMPAIGN ATTRIBUTION & PREDICTIONS", icon: Cpu },
          { id: "graph", label: "ATTACK PATHS & CHOKEPOINTS", icon: Network },
          { id: "intel", label: "THREAT INTELLIGENCE (RAG)", icon: Database },
          { id: "soar", label: "SOAR PLAYBOOK ORCHESTRATOR", icon: Terminal },
          { id: "ueba", label: "UEBA ANOMALY MATRIX", icon: Activity },
        ].map(t => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 cursor-pointer transition-all duration-150 uppercase ${
                activeTab === t.id
                  ? "border-[#E56A21] text-[#E56A21] bg-[#E56A21]/5"
                  : "border-transparent text-text-secondary hover:text-white hover:bg-white/[0.02]"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {t.label}
            </button>
          );
        })}
      </div>

      {/* ── TAB CONTENT: ANALYSIS ── */}
      {activeTab === "analysis" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Input Panel */}
          <div className="flex flex-col gap-6 lg:col-span-1">
            <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col gap-4">
              <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5 border-b border-white/5 pb-2 mb-1">
                <Sliders className="h-3.5 w-3.5 text-[#E56A21]" />
                HUNTER INPUT CORRELATOR
              </span>

              {/* Observed TTPs */}
              <div className="flex flex-col gap-2">
                <label className="text-[10px] text-text-tertiary uppercase">Select Observed TTPs (MITRE):</label>
                <div className="max-h-[220px] overflow-y-auto space-y-1.5 border border-white/5 p-2 rounded-lg bg-[#0C0C0C]">
                  {AVAILABLE_TTPS.map(t => {
                    const isSelected = selectedTTPs.includes(t.id);
                    return (
                      <div
                        key={t.id}
                        onClick={() => toggleTTP(t.id)}
                        className={`flex items-center justify-between p-2 rounded cursor-pointer text-[10px] transition-colors border ${
                          isSelected
                            ? "bg-[#E56A21]/10 border-[#E56A21]/40 text-[#E56A21]"
                            : "bg-[#151515] border-transparent hover:bg-white/[0.03] text-text-secondary"
                        }`}
                      >
                        <div className="flex flex-col">
                          <span className="font-bold text-white">{t.id} - {t.name}</span>
                          <span className="text-[8px] text-text-tertiary uppercase">{t.tactic}</span>
                        </div>
                        {isSelected && <CheckCircle className="h-3.5 w-3.5" />}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Observed IOCs */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] text-text-tertiary uppercase">Observed IOCs (Comma Separated):</label>
                <input
                  type="text"
                  value={iocInput}
                  onChange={(e) => setIocInput(e.target.value)}
                  placeholder="e.g., cmd.exe, avsvmcloud.com"
                  className="bg-[#0C0C0C] border border-white/5 p-2 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-[#E56A21] w-full"
                />
              </div>

              {/* Target Sector */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] text-text-tertiary uppercase">Target Sector:</label>
                <input
                  type="text"
                  value={targetSector}
                  onChange={(e) => setTargetSector(e.target.value)}
                  className="bg-[#0C0C0C] border border-white/5 p-2 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-[#E56A21] w-full"
                />
              </div>

              {/* Target Country */}
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] text-text-tertiary uppercase">Target Geography / Country:</label>
                <input
                  type="text"
                  value={targetCountry}
                  onChange={(e) => setTargetCountry(e.target.value)}
                  className="bg-[#0C0C0C] border border-white/5 p-2 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-[#E56A21] w-full"
                />
              </div>

              {/* Run Button */}
              <button
                onClick={runAnalysis}
                disabled={loading}
                className="w-full bg-[#E56A21] hover:bg-[#E56A21]/80 text-white font-bold py-2.5 rounded-lg text-xs tracking-wider transition-colors cursor-pointer disabled:opacity-50 flex items-center justify-center gap-1.5 uppercase"
              >
                {loading ? (
                  <>
                    <div className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    CORRELATING PLAYBOOKS...
                  </>
                ) : (
                  <>
                    <Activity className="h-4 w-4" /> RUN ATTRIBUTION MATRIX
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results Area */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            
            {/* Attribution Status Panel */}
            {analysisResult && (
              <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col gap-4 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-[200px] h-[200px] bg-red-500/5 rounded-full blur-[80px] pointer-events-none" />
                <div className="flex justify-between items-start border-b border-white/5 pb-3">
                  <div>
                    <h2 className="text-white text-base font-bold uppercase">Attribution Diagnosis</h2>
                    <span className="text-[9px] text-text-tertiary uppercase tracking-wider block mt-0.5">Threat Intel Engine Output</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="px-2.5 py-1 text-[9px] font-bold uppercase rounded bg-red-500/20 text-red-500 border border-red-500/30">
                      {analysisResult.attribution?.attribution_status}
                    </span>
                    <span className="text-[8px] text-text-tertiary mt-1 uppercase">Attribution Confidence: {Math.round(analysisResult.attribution?.top_confidence * 100)}%</span>
                  </div>
                </div>

                {/* Candidate Groups */}
                <div className="space-y-3">
                  <span className="text-[10px] text-text-tertiary uppercase">Top Candidate Actors:</span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {analysisResult.attribution?.candidate_groups?.slice(0, 2).map((g: any) => (
                      <div key={g.group_id} className="bg-[#0C0C0C] border border-white/5 rounded-xl p-4 flex flex-col gap-2.5 relative">
                        <div className="flex justify-between items-start">
                          <div>
                            <span className="text-white font-bold text-xs block">{g.group_name}</span>
                            <span className="text-[8px] text-text-tertiary uppercase flex items-center gap-1 mt-0.5">
                              <Globe className="h-2.5 w-2.5" /> ORIGIN: {g.country}
                            </span>
                          </div>
                          <span className="text-white font-bold text-xs">{Math.round(g.confidence * 100)}%</span>
                        </div>
                        {/* Confidence Bar */}
                        <div className="w-full bg-white/[0.02] h-1.5 rounded-full overflow-hidden border border-white/5">
                          <div className="bg-[#E56A21] h-full rounded-full" style={{ width: `${g.confidence * 100}%` }} />
                        </div>
                        <div className="text-[9px] text-text-secondary leading-normal mt-1 border-t border-white/5 pt-2">
                          <span className="text-text-tertiary uppercase block text-[8px] mb-1">Attribution Reason:</span>
                          {g.attribution_reasoning?.[0] || "Infrastructure similarities."}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* predictions Panel */}
            {analysisResult && (
              <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col gap-4">
                <span className="text-[10px] tracking-wider text-text-tertiary uppercase border-b border-white/5 pb-2 mb-1">
                  NEXT-STAGE MOVE PREDICTIONS (MARKOV PATHWAY)
                </span>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Timeline progress */}
                  <div className="flex flex-col gap-3">
                    <span className="text-[9px] text-text-tertiary uppercase">Kill-Chain Progress:</span>
                    <div className="bg-[#0C0C0C] border border-white/5 rounded-xl p-4 flex flex-col gap-3">
                      <div className="flex justify-between text-xs font-bold">
                        <span className="text-text-secondary uppercase">Current attack phase:</span>
                        <span className="text-[#E56A21]">{analysisResult.predictions?.current_phase?.tactic_name}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-text-tertiary uppercase">Estimated Stage:</span>
                        <span className="text-white font-bold">{analysisResult.predictions?.kill_chain_progress?.estimated_attack_stage}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-text-tertiary uppercase">Kill-chain Coverage:</span>
                        <span className="text-white font-bold">{analysisResult.predictions?.kill_chain_progress?.progress_percentage}%</span>
                      </div>
                    </div>
                  </div>

                  {/* Predictions list */}
                  <div className="flex flex-col gap-3">
                    <span className="text-[9px] text-text-tertiary uppercase">Predicted Next Moves:</span>
                    <div className="space-y-2 max-h-[160px] overflow-y-auto pr-1">
                      {analysisResult.predictions?.top_predictions?.map((pred: any) => (
                        <div key={pred.technique_id} className="bg-[#0C0C0C] border border-white/5 rounded-lg p-2.5 flex justify-between items-center text-[10px]">
                          <div className="flex flex-col">
                            <span className="text-white font-bold">{pred.technique_id} - {pred.technique_name}</span>
                            <span className="text-[8px] text-[#E56A21] mt-0.5">{pred.tactic_name}</span>
                          </div>
                          <div className="flex flex-col items-end">
                            <span className="text-red-400 font-bold">{Math.round(pred.probability * 100)}%</span>
                            <span className="text-[8px] text-text-tertiary uppercase">PROBABILITY</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Tactical Actions */}
                <div className="border-t border-white/5 pt-4 mt-2">
                  <span className="text-[10px] text-text-tertiary uppercase block mb-3">Targeted Containment Playbook:</span>
                  <div className="space-y-2">
                    {analysisResult.defensive_actions?.defensive_plan?.slice(0, 2).map((plan: any) => (
                      <div key={plan.tactic_id} className="bg-[#0C0C0C] border border-white/5 rounded-xl p-3 flex flex-col gap-2">
                        <div className="flex justify-between items-center text-[9px] font-bold border-b border-white/5 pb-1.5">
                          <span className="text-white uppercase">{plan.tactic_name} DEFENSIVE VECTOR</span>
                          <span className={`px-1.5 py-0.5 rounded text-[8px] ${
                            plan.urgency === "CRITICAL" ? "bg-red-500/20 text-red-400" : "bg-yellow-500/20 text-yellow-400"
                          }`}>{plan.urgency} URGENCY</span>
                        </div>
                        <ul className="list-disc list-inside space-y-1 text-[9px] text-text-secondary">
                          {plan.actions?.slice(0, 2).map((a: any, idx: number) => (
                            <li key={idx} className="leading-relaxed">
                              {a.action} {a.target_assets && <span className="text-[#E56A21]">[{a.target_assets.join(", ")}]</span>}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            )}
            
            {/* If no analysis, show help */}
            {!analysisResult && (
              <div className="bg-[#151515] border border-white/5 rounded-xl p-12 flex flex-col items-center justify-center text-center">
                <Terminal className="h-10 w-10 text-text-tertiary mb-3 opacity-50" />
                <h3 className="text-white font-bold text-sm uppercase">Threat Engine Standby</h3>
                <p className="text-text-tertiary text-xs mt-1.5 max-w-sm">
                  Select observed TTP techniques and run the attribution matrix to trigger multi-agent analysis.
                </p>
              </div>
            )}

          </div>

        </div>
      )}

      {/* ── TAB CONTENT: GRAPH ── */}
      {activeTab === "graph" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Inputs */}
          <div className="lg:col-span-1 bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col gap-4">
            <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5 border-b border-white/5 pb-2 mb-1">
              <Network className="h-3.5 w-3.5 text-[#E56A21]" />
              PATH CALCULATOR OPTIONS
            </span>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-text-tertiary uppercase">Entry Point Asset ID:</label>
              <input
                type="text"
                value={entryPoint}
                onChange={(e) => setEntryPoint(e.target.value)}
                className="bg-[#0C0C0C] border border-white/5 p-2 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-[#E56A21] w-full"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-text-tertiary uppercase">Target Objective Asset ID:</label>
              <input
                type="text"
                value={targetAsset}
                onChange={(e) => setTargetAsset(e.target.value)}
                className="bg-[#0C0C0C] border border-white/5 p-2 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-[#E56A21] w-full"
              />
            </div>

            <button
              onClick={runGraphPathAnalysis}
              disabled={graphLoading}
              className="w-full bg-[#E56A21] hover:bg-[#E56A21]/80 text-white font-bold py-2 rounded-lg text-xs transition-colors cursor-pointer flex items-center justify-center gap-1 uppercase"
            >
              <Search className="h-3.5 w-3.5" /> CALCULATE PATHS
            </button>

            {/* Chokepoint list */}
            <div className="border-t border-white/5 pt-4 mt-2 flex flex-col gap-3">
              <span className="text-[10px] text-text-tertiary uppercase">Identified Network Chokepoints:</span>
              <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
                {chokepoints.map(cp => (
                  <div key={cp.id} className="bg-[#0C0C0C] border border-white/5 rounded-lg p-2.5 flex flex-col gap-1 text-[10px]">
                    <div className="flex justify-between items-center">
                      <span className="text-white font-bold">{cp.name}</span>
                      <span className="px-1.5 py-0.5 rounded text-[8px] bg-red-500/20 text-red-400 font-bold uppercase">{cp.criticality}</span>
                    </div>
                    <span className="text-[8px] text-text-tertiary uppercase">TYPE: {cp.type} | CONNECTIONS: {cp.connections}</span>
                    <p className="text-[9px] text-[#E56A21] mt-1 leading-relaxed italic">{cp.defensive_recommendation}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Visualizer Output */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col gap-4 min-h-[400px]">
              <span className="text-[10px] tracking-wider text-text-tertiary uppercase border-b border-white/5 pb-2 mb-1">
                ATTACK PATH TOPOLOGY (MERMAID SPEC)
              </span>

              {graphLoading ? (
                <div className="flex-1 flex items-center justify-center">
                  <div className="flex flex-col items-center gap-2 text-text-tertiary">
                    <div className="h-6 w-6 border-2 border-[#E56A21]/30 border-t-[#E56A21] rounded-full animate-spin" />
                    <span className="text-[10px] uppercase">Traversing relation tables...</span>
                  </div>
                </div>
              ) : graphPaths ? (
                <div className="flex-1 flex flex-col gap-4">
                  {/* Summary */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-[#0C0C0C] border border-white/5 p-3 rounded-lg flex flex-col text-[10px]">
                      <span className="text-text-tertiary uppercase">PATHS DETECTED</span>
                      <span className="text-white text-base font-bold mt-1">{graphPaths.total_paths_found}</span>
                    </div>
                    <div className="bg-[#0C0C0C] border border-white/5 p-3 rounded-lg flex flex-col text-[10px]">
                      <span className="text-text-tertiary uppercase">SHORTEST ROUTE</span>
                      <span className="text-[#E56A21] text-base font-bold mt-1">{graphPaths.shortest_path_hops} HOPS</span>
                    </div>
                    <div className="bg-[#0C0C0C] border border-white/5 p-3 rounded-lg flex flex-col text-[10px]">
                      <span className="text-text-tertiary uppercase">EASIEST PATH DIFFICULTY</span>
                      <span className="text-white text-base font-bold mt-1">{graphPaths.easiest_path_score}</span>
                    </div>
                  </div>

                  {/* Mermaid Text */}
                  <div className="flex flex-col gap-2">
                    <span className="text-[9px] text-text-tertiary uppercase">Mermaid Diagram Representation:</span>
                    <pre className="bg-[#0C0C0C] border border-white/5 p-4 rounded-xl text-[9px] font-mono text-green-400 overflow-x-auto whitespace-pre leading-relaxed select-all">
                      {graphPaths.mermaid || "graph LR\n    workstation --> target;"}
                    </pre>
                  </div>

                  {/* Path step list */}
                  <div className="flex flex-col gap-2 border-t border-white/5 pt-3 flex-grow">
                    <span className="text-[9px] text-text-tertiary uppercase">Computed Attack Steps:</span>
                    <div className="space-y-2">
                      {graphPaths.attack_paths?.slice(0, 1).map((p: any, idx: number) => (
                        <div key={idx} className="bg-[#0C0C0C] border border-white/5 rounded-xl p-3 flex flex-col gap-1.5">
                          <span className="text-[10px] text-white font-bold uppercase">Optimal Route (Difficulty: {p.difficulty_score})</span>
                          <div className="flex flex-wrap items-center gap-2 text-[10px]">
                            {p.path.map((node: any, nIdx: number) => (
                              <Fragment key={node.id}>
                                {nIdx > 0 && <span className="text-text-tertiary">→</span>}
                                <span className={`px-2 py-0.5 rounded font-bold border ${
                                  node.type === "unknown" ? "bg-red-500/10 border-red-500/30 text-red-400" : "bg-white/[0.02] border-white/5 text-white"
                                }`}>
                                  {node.name} <span className="text-[7.5px] text-text-tertiary uppercase font-normal">({node.type})</span>
                                </span>
                              </Fragment>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                  <Network className="h-8 w-8 text-text-tertiary mb-2 opacity-30" />
                  <span className="text-text-tertiary text-xs uppercase">Compute paths to scan structural connections.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── TAB CONTENT: INTEL ── */}
      {activeTab === "intel" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Query sidebar */}
          <div className="lg:col-span-1 bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col gap-4">
            <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5 border-b border-white/5 pb-2 mb-1">
              <Database className="h-3.5 w-3.5 text-[#E56A21]" />
              INTELLIGENCE RAG LOADER
            </span>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-text-tertiary uppercase">Search Query (CVE, Actor, or Keyword):</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={ragQuery}
                  onChange={(e) => setRagQuery(e.target.value)}
                  className="bg-[#0C0C0C] border border-white/5 p-2 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-[#E56A21] flex-1"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-text-tertiary uppercase">Index Filter:</label>
              <select
                value={ragSearchType}
                onChange={(e) => setRagSearchType(e.target.value)}
                className="bg-[#0C0C0C] border border-white/5 p-2 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-[#E56A21] w-full"
              >
                <option value="general">All Sources (BM25)</option>
                <option value="cve">CVE Database Matches</option>
                <option value="apt_group">APT Actor Corpus</option>
                <option value="source_type">CERT-In Advisories only</option>
              </select>
            </div>

            <button
              onClick={runRagSearch}
              disabled={ragLoading}
              className="w-full bg-[#E56A21] hover:bg-[#E56A21]/80 text-white font-bold py-2 rounded-lg text-xs transition-colors cursor-pointer flex items-center justify-center gap-1 uppercase"
            >
              <Search className="h-3.5 w-3.5" /> QUERY CORPUS
            </button>
          </div>

          {/* RAG Feed Area */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col gap-4 min-h-[400px]">
              <span className="text-[10px] tracking-wider text-text-tertiary uppercase border-b border-white/5 pb-2 mb-1">
                RETRIEVED DOCUMENT CHUNKS (RAG FEED)
              </span>

              {ragLoading ? (
                <div className="flex-1 flex items-center justify-center">
                  <div className="flex flex-col items-center gap-2 text-text-tertiary">
                    <div className="h-6 w-6 border-2 border-[#E56A21]/30 border-t-[#E56A21] rounded-full animate-spin" />
                    <span className="text-[10px] uppercase">Retrieving indexed threat context...</span>
                  </div>
                </div>
              ) : ragResults.length > 0 ? (
                <div className="space-y-4 max-h-[500px] overflow-y-auto pr-1">
                  {ragResults.map(doc => (
                    <div key={doc.id} className="bg-[#0C0C0C] border border-white/5 rounded-xl p-4 flex flex-col gap-3 relative">
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="text-white font-bold text-xs block">{doc.title}</span>
                          <span className="text-[8px] text-text-tertiary uppercase mt-1 block">
                            DOC ID: {doc.id} | SOURCE: {doc.source_type} | PUBLISHED: {doc.published_date}
                          </span>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-[8px] font-bold border ${
                          doc.severity === "CRITICAL"
                            ? "bg-red-500/20 border-red-500/30 text-red-400"
                            : "bg-yellow-500/20 border-yellow-500/30 text-yellow-400"
                        }`}>{doc.severity}</span>
                      </div>
                      
                      <p className="text-[11px] text-text-secondary leading-relaxed border-t border-white/5 pt-2.5">
                        {doc.content}
                      </p>

                      {/* Tag Metadata */}
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {doc.tags?.map((t: string) => (
                          <span key={t} className="bg-white/[0.02] border border-white/5 text-text-tertiary px-1.5 py-0.5 rounded text-[8px] uppercase">
                            #{t}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                  <Database className="h-8 w-8 text-text-tertiary mb-2 opacity-30" />
                  <span className="text-text-tertiary text-xs uppercase">No intelligence records match query.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── TAB CONTENT: SOAR ── */}
      {activeTab === "soar" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Incident list */}
          <div className="lg:col-span-1 bg-[#151515] border border-white/5 rounded-xl p-4 flex flex-col h-[520px]">
            <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5 border-b border-white/5 pb-2.5 mb-3">
              <Terminal className="h-3.5 w-3.5 text-[#E56A21]" />
              ACTIVE SOAR INCIDENTS
            </span>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {incidents.map(inc => (
                <div
                  key={inc.id || inc.incident_id}
                  onClick={() => selectIncident(inc.id || inc.incident_id)}
                  className={`border p-3 rounded-lg flex flex-col gap-2 cursor-pointer transition-all duration-150 hover:border-[#E56A21]/30 ${
                    activeIncident?.id === (inc.id || inc.incident_id)
                      ? "border-[#E56A21] bg-[#1C1C1C]/40"
                      : "border-white/5 bg-[#0C0C0C]"
                  }`}
                >
                  <div className="flex justify-between items-center text-[8px] text-text-tertiary">
                    <span className="text-white font-bold">{inc.id || inc.incident_id}</span>
                    <span>{inc.created_at?.split("T")[0]}</span>
                  </div>
                  <span className="text-[10.5px] text-white font-bold line-clamp-1 leading-normal">{inc.title}</span>
                  <div className="flex justify-between items-center text-[8px] border-t border-white/5 pt-1.5 mt-0.5">
                    <span className="px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 font-bold uppercase">{inc.severity}</span>
                    <span className="text-text-secondary font-bold uppercase">{inc.status}</span>
                  </div>
                </div>
              ))}

              {incidents.length === 0 && (
                <div className="text-text-tertiary text-center py-20">
                  <span>No active incidents.</span>
                </div>
              )}
            </div>
          </div>

          {/* Incident response action log */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col min-h-[520px]">
              <span className="text-[10px] tracking-wider text-text-tertiary uppercase border-b border-white/5 pb-3 mb-4 block">
                PLAYBOOK RESPONSE LOG
              </span>

              {activeIncident ? (
                <div className="flex-grow flex flex-col gap-5">
                  <div className="flex justify-between items-start border-b border-white/5 pb-3">
                    <div>
                      <h3 className="text-white font-bold text-sm leading-tight">{activeIncident.title}</h3>
                      <span className="text-[9px] text-text-tertiary uppercase mt-1 block">
                        INCIDENT STATUS: {activeIncident.status} | PLAYBOOK: {activeIncident.playbook_id || "PB-001"}
                      </span>
                    </div>
                    
                    {/* Execution Controls */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => executePlaybook(activeIncident.id || activeIncident.incident_id, "simulate")}
                        disabled={soarLoading}
                        className="bg-white/[0.03] hover:bg-white/[0.06] border border-white/10 text-white font-bold px-3 py-1.5 rounded-lg text-[9px] cursor-pointer flex items-center gap-1 uppercase transition-colors"
                      >
                        <RotateCcw className="h-3 w-3" /> SIMULATE
                      </button>
                      <button
                        onClick={() => executePlaybook(activeIncident.id || activeIncident.incident_id, "auto_execute")}
                        disabled={soarLoading}
                        className="bg-[#E56A21] hover:bg-[#E56A21]/80 text-white font-bold px-3 py-1.5 rounded-lg text-[9px] cursor-pointer flex items-center gap-1 uppercase transition-colors"
                      >
                        <Play className="h-3 w-3" /> EXECUTE AUTO
                      </button>
                    </div>
                  </div>

                  {/* Actions log timeline */}
                  <div className="flex-grow flex flex-col gap-3">
                    <span className="text-[10px] text-text-tertiary uppercase">Playbook Steps Execution:</span>
                    <div className="space-y-2 overflow-y-auto max-h-[340px] pr-1">
                      {incidentActions.map(action => (
                        <div key={action.id} className="bg-[#0C0C0C] border border-white/5 rounded-xl p-3 flex justify-between items-center text-[10px]">
                          <div className="flex items-center gap-3">
                            <span className="text-[#E56A21] font-bold">#{action.step_number}</span>
                            <div className="flex flex-col gap-0.5">
                              <span className="text-white font-semibold">{action.action_description}</span>
                              <span className="text-[8px] text-text-tertiary uppercase">TYPE: {action.action_type} | MODE: {action.automated ? "AUTOMATED" : "MANUAL"}</span>
                            </div>
                          </div>
                          
                          <div className="flex flex-col items-end">
                            <span className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase ${
                              action.status === "COMPLETED" || action.status === "SIMULATED"
                                ? "bg-green-500/10 text-green-400"
                                : action.status === "PENDING"
                                ? "bg-yellow-500/10 text-yellow-400"
                                : "bg-sky-500/10 text-sky-400"
                            }`}>{action.status}</span>
                            {action.result && <span className="text-[7.5px] text-text-tertiary mt-1 max-w-[150px] truncate">{action.result}</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                  <Terminal className="h-8 w-8 text-text-tertiary mb-2 opacity-30" />
                  <span className="text-text-tertiary text-xs uppercase">Select an incident to view its playbook execution response.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── TAB CONTENT: UEBA ── */}
      {activeTab === "ueba" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Entity Selector sidebar */}
          <div className="lg:col-span-1 bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col gap-4">
            <span className="text-[10px] tracking-wider text-text-tertiary uppercase flex items-center gap-1.5 border-b border-white/5 pb-2 mb-1">
              <Activity className="h-3.5 w-3.5 text-[#E56A21]" />
              UEBA ANOMALY EXPLORER
            </span>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] text-text-tertiary uppercase">Enter Entity ID (User/Device):</label>
              <input
                type="text"
                value={uebaEntity}
                onChange={(e) => setUebaEntity(e.target.value)}
                className="bg-[#0C0C0C] border border-white/5 p-2 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-[#E56A21] w-full"
              />
            </div>

            <button
              onClick={runUebaScan}
              disabled={uebaLoading}
              className="w-full bg-[#E56A21] hover:bg-[#E56A21]/80 text-white font-bold py-2 rounded-lg text-xs transition-colors cursor-pointer flex items-center justify-center gap-1 uppercase"
            >
              <Search className="h-3.5 w-3.5" /> SCAN BEHAVIOR
            </button>

            {/* Assessment display */}
            {uebaPatterns && (
              <div className="bg-[#0C0C0C] border border-white/5 rounded-xl p-4 flex flex-col gap-2 text-[10px] mt-2">
                <span className="text-text-tertiary uppercase">Overall Assessment:</span>
                <div className="flex justify-between items-center font-bold text-xs mt-1 text-white">
                  <span>APT Risk Index:</span>
                  <span className="text-red-400 font-bold">{Math.round(uebaPatterns.apt_risk_score * 100)}%</span>
                </div>
                <p className="text-[9px] text-[#E56A21] leading-relaxed mt-1.5 border-t border-white/5 pt-2 italic">
                  {uebaPatterns.assessment}
                </p>
              </div>
            )}
          </div>

          {/* Anomaly results view */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            <div className="bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col min-h-[400px]">
              <span className="text-[10px] tracking-wider text-text-tertiary uppercase border-b border-white/5 pb-2 mb-1">
                TEMPORAL ANOMALY TIMELINE & PATTERNS
              </span>

              {uebaLoading ? (
                <div className="flex-1 flex items-center justify-center">
                  <div className="flex flex-col items-center gap-2 text-text-tertiary">
                    <div className="h-6 w-6 border-2 border-[#E56A21]/30 border-t-[#E56A21] rounded-full animate-spin" />
                    <span className="text-[10px] uppercase">Retrieving baseline deviations...</span>
                  </div>
                </div>
              ) : uebaTimeline.length > 0 ? (
                <div className="flex flex-col gap-4 flex-grow">
                  {/* Indicators list */}
                  {uebaPatterns && uebaPatterns.indicators?.length > 0 && (
                    <div className="flex flex-col gap-2">
                      <span className="text-[9px] text-text-tertiary uppercase">Correlated Anomaly Indicators:</span>
                      <div className="space-y-2">
                        {uebaPatterns.indicators.map((ind: any, index: number) => (
                          <div key={index} className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 flex gap-2.5">
                            <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                            <div className="flex flex-col text-[10px]">
                              <span className="text-white font-bold uppercase">{ind.type.replace(/_/g, " ")}</span>
                              <span className="text-text-secondary leading-relaxed mt-0.5">{ind.description}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Anomaly Log */}
                  <div className="flex flex-col gap-2 border-t border-white/5 pt-3 flex-grow">
                    <span className="text-[9px] text-text-tertiary uppercase">Baseline Deviations Log:</span>
                    <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
                      {uebaTimeline.map((ev, index) => (
                        <div key={index} className="bg-[#0C0C0C] border border-white/5 rounded-lg p-2.5 flex justify-between items-center text-[10px]">
                          <div className="flex flex-col gap-0.5">
                            <span className="text-white font-bold">{ev.category} - {ev.feature}</span>
                            <span className="text-[8px] text-text-tertiary uppercase">{ev.timestamp} | MITRE TACTIC: {ev.mitre_tactic || "None"}</span>
                          </div>
                          
                          <div className="flex flex-col items-end">
                            <span className="text-white font-bold">{ev.deviation_score.toFixed(1)}z</span>
                            <span className="text-[8px] text-text-tertiary uppercase">DEVIATION</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                  <Activity className="h-8 w-8 text-text-tertiary mb-2 opacity-30" />
                  <span className="text-text-tertiary text-xs uppercase">No behavioral anomaly records found for this entity.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
