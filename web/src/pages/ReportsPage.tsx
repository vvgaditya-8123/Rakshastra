import { useState } from "react";
import {
  FileText,
  Download,
  Users
} from "lucide-react";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";

export default function ReportsPage() {
  const [selectedReportId, setSelectedReportId] = useState("NDPS-089");

  const reports = [
    {
      id: "NDPS-089",
      title: "Mumbai-Delhi MDMA/Cocaine Cross-Platform Pipeline",
      compiledDate: "2026-07-06 14:12",
      targetSyndicate: "Mumbai-Delhi Rave Syndicate",
      riskLevel: "CRITICAL",
      status: "VERIFIED",
      summary: "Multilingual OSINT scans intercepted multiple Telegram bots and Instagram handles advertising high-purity MDMA crystals and cocaine Party Pills. The entities share payment wallets and SIM structures linked to Delhi NCR delivery operations. Suspects utilize Hinglish slang and emojis to bypass automated keyword detection.",
      targets: ["Anjali Bose (Seller, Risk Index: 94)", "Rohan Mehra (Seller, Risk Index: 88)", "Kunal Sen (Buyer, Risk Index: 76)"],
      platforms: "Telegram (Connected), Instagram (Monitored), WhatsApp (Active)",
      evidenceCount: 14,
      hash: "8e78a6fa23b2cde8e791cb72de31c775d0505a41cfdece31ef09c12df380db28"
    },
    {
      id: "NDPS-042",
      title: "Punjab Chitta & Mephedrone Distribution Ring",
      compiledDate: "2026-07-05 09:44",
      targetSyndicate: "Punjab Chitta Network",
      riskLevel: "HIGH",
      status: "UNDER INVESTIGATION",
      summary: "Automatic intelligence sweep flagged multiple WhatsApp group threads and Telegram channels promoting bulk Mephedrone (Meow Meow) and local derivatives. Suspects utilize Punjabi slang (chitta) and emoji codes (😼). IP coordinates correlate to transit locations near Punjab highway routes.",
      targets: ["Jaspreet Singh (Seller, Risk Index: 91)", "Amit Sharma (Buyer, Risk Index: 65)"],
      platforms: "WhatsApp (Connected), Telegram (Monitored)",
      evidenceCount: 8,
      hash: "4a2de7fca234125bcf8e09e1e79cb72b380db41cfdece31ef09c1dff380db289"
    }
  ];

  const activeReport = reports.find(r => r.id === selectedReportId) || reports[0];

  const exportReport = (rep: any) => {
    const text = `======================================================================
RAKSHASTRA AGENT - PROSECUTION DOSSIER REPORT
======================================================================
REPORT REFERENCE ID: ${rep.id}
TITLE: ${rep.title}
COMPILED DATE: ${rep.compiledDate}
TARGET SYNDICATE: ${rep.targetSyndicate}
RISK CLASSIFICATION: ${rep.riskLevel}
VERIFICATION STATUS: ${rep.status}

SUMMARY ANALYSIS:
${rep.summary}

SUSPECT TARGET DETAILS:
${rep.targets.map((t: any) => `- ${t}`).join("\n")}

MONITORED SOCIAL CHANNELS:
${rep.platforms}

EVIDENCE AUDIT COUNTS:
${rep.evidenceCount} prosecution files gathered with Section 65B integrity certification.

CHAIN OF CUSTODY INTEGRITY VALUE (SHA-256):
${rep.hash}

======================================================================
DOCUMENT CLASSIFIED AS CONFIDENTIAL LAW ENFORCEMENT OSINT INTELLIGENCE.
======================================================================`;

    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `CASE_DOSSIER_${rep.id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-6 p-6 min-h-0 min-w-0 flex-1 overflow-y-auto text-text-primary bg-[#0E0E0E] font-mono">
      {/* Header */}
      <div className="bg-[#151515] border border-white/5 rounded-xl p-5 relative overflow-hidden flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="absolute top-0 right-0 w-[200px] h-[200px] bg-[#E56A21]/5 rounded-full blur-[80px] pointer-events-none" />
        <div className="flex-1 flex flex-col gap-1">
          <span className="text-[10px] tracking-widest text-[#E56A21] font-bold uppercase flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5" />
            CASE DOSSIERS
          </span>
          <h1 className="text-white text-lg font-bold">INTELLIGENCE REPORTS & DOSSIERS</h1>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        
        {/* Left Side: Reports list */}
        <div className="lg:col-span-1 flex flex-col gap-3">
          <span className="text-text-tertiary uppercase text-[10px] font-bold tracking-widest pl-1">Intelligence Files</span>
          {reports.map((rep) => (
            <div
              key={rep.id}
              onClick={() => setSelectedReportId(rep.id)}
              className={`bg-[#151515] border rounded-xl p-4 flex flex-col gap-2 cursor-pointer transition-all duration-200 hover:border-[#E56A21]/30 ${
                selectedReportId === rep.id ? "border-[#E56A21] bg-[#1C1C1C]/60" : "border-white/5"
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="text-white font-bold text-xs">{rep.id}</span>
                <Badge tone={rep.riskLevel === "CRITICAL" ? "destructive" : "warning"} className="text-[7.5px] font-bold uppercase">
                  {rep.riskLevel}
                </Badge>
              </div>
              <span className="text-white font-semibold text-[10.5px] leading-tight mt-1">{rep.title}</span>
              <span className="text-text-tertiary text-[8.5px] mt-1">{rep.compiledDate}</span>
            </div>
          ))}
        </div>

        {/* Right Side: Detailed Dossier Viewer */}
        <div className="lg:col-span-2 bg-[#151515] border border-white/5 rounded-xl p-5 flex flex-col justify-between min-h-[500px]">
          <div className="flex flex-col gap-4 text-[10px] text-text-secondary overflow-y-auto scrollbar-none pr-1">
            <div className="border-b border-[#E56A21]/30 pb-3 flex justify-between items-start">
              <div>
                <h2 className="text-white text-base font-bold uppercase">{activeReport.title}</h2>
                <span className="text-text-tertiary text-[8.5px] uppercase mt-0.5 block">Forensic Dossier summary ({activeReport.id})</span>
              </div>
              <Badge tone="success" className="text-[8px]">{activeReport.status}</Badge>
            </div>

            <div className="space-y-3">
              <div className="flex flex-col gap-1">
                <span className="text-text-tertiary uppercase text-[8px]">Case Summary Overview</span>
                <p className="bg-[#0B0B0B] border border-white/5 p-3 rounded text-[10px] leading-relaxed text-text-primary">
                  {activeReport.summary}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-white/5 pt-3">
                <div className="space-y-2">
                  <span className="text-text-tertiary uppercase text-[8px] block">Identified Syndicate Targets</span>
                  <div className="flex flex-col gap-1 font-semibold text-white">
                    {activeReport.targets.map((t, idx) => (
                      <div key={idx} className="flex items-center gap-1.5 bg-[#0C0C0C] border border-white/5 rounded p-1.5 text-[9.5px]">
                        <Users className="h-3 w-3 text-[#E56A21]" />
                        <span>{t}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="text-text-tertiary uppercase text-[8px] block">Target Channels Status</span>
                  <span className="text-white font-bold block bg-[#0C0C0C] border border-white/5 rounded p-2 text-[9.5px]">
                    {activeReport.platforms}
                  </span>
                  
                  <div className="flex justify-between text-[9px] mt-2">
                    <span>Evidence files gathered:</span>
                    <span className="text-[#E56A21] font-bold">{activeReport.evidenceCount} certificates</span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-1 border-t border-white/5 pt-3">
                <span className="text-text-tertiary uppercase text-[8px]">Dossier SHA-256 Hash Integrity Value</span>
                <span className="text-purple-300 font-courier text-[8.5px] break-all bg-[#0C0C0C] border border-white/5 p-2 rounded">
                  {activeReport.hash}
                </span>
              </div>
            </div>
          </div>

          <div className="flex gap-4 border-t border-white/5 pt-4 mt-6">
            <Button
              onClick={() => exportReport(activeReport)}
              className="flex-1 bg-[#E56A21] hover:bg-[#E56A21]/80 text-white font-bold text-[10px] py-2"
            >
              <Download className="h-3.5 w-3.5 mr-1.5" /> EXPORT FULL PROSECUTION DOSSIER
            </Button>
          </div>
        </div>

      </div>
    </div>
  );
}
