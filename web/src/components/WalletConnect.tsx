import { useState, useEffect } from "react";
import { 
  Wallet, 
  Coins, 
  ArrowRightLeft, 
  Copy, 
  Loader2, 
  QrCode,
  ShieldCheck,
  Zap
} from "lucide-react";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";

interface TransactionItem {
  id: string;
  timestamp: string;
  endpoint: string;
  amountAlgo: number;
}

export function WalletConnect() {
  const [connected, setConnected] = useState(false);
  const [address, setAddress] = useState("");
  const [balance, setBalance] = useState(120.45);
  const [showQrModal, setShowQrModal] = useState(false);
  
  // Transaction signing state
  const [signing, setSigning] = useState(false);
  const [selectedEndpoint, setSelectedEndpoint] = useState("/api/v1/threat/analyze-text");
  const [activeTxId, setActiveTxId] = useState("");
  const [txHistory, setTxHistory] = useState<TransactionItem[]>([]);
  
  // Pricing map
  const pricing: Record<string, number> = {
    "/api/v1/threat/analyze-text": 0.05,
    "/api/v1/entity/correlate": 0.10,
    "/api/v1/report/generate": 0.15,
  };

  // Load state from localStorage on mount
  useEffect(() => {
    const savedConnected = localStorage.getItem("rakshastra.walletConnected") === "true";
    const savedAddress = localStorage.getItem("rakshastra.walletAddress") || "";
    const savedBalance = parseFloat(localStorage.getItem("rakshastra.walletBalance") || "120.45");
    const savedTxId = localStorage.getItem("rakshastra.algoTxId") || "";
    const savedHistory = JSON.parse(localStorage.getItem("rakshastra.txHistory") || "[]");

    if (savedConnected && savedAddress) {
      setConnected(true);
      setAddress(savedAddress);
      setBalance(savedBalance);
      setActiveTxId(savedTxId);
      setTxHistory(savedHistory);
    }
  }, []);

  const handleConnectWallet = () => {
    setShowQrModal(true);
    
    // Simulate connection flow with Pera Wallet QR code scanning
    setTimeout(() => {
      const mockAddr = "PERAUSERJ7U6MZQ3B346YV3Z6EX2L7SDR74G2K3K5NJV3Z6EX2L7SDR2345";
      setConnected(true);
      setAddress(mockAddr);
      setBalance(120.45);
      setShowQrModal(false);
      
      localStorage.setItem("rakshastra.walletConnected", "true");
      localStorage.setItem("rakshastra.walletAddress", mockAddr);
      localStorage.setItem("rakshastra.walletBalance", "120.45");
    }, 2500);
  };

  const handleDisconnect = () => {
    setConnected(false);
    setAddress("");
    setBalance(120.45);
    setActiveTxId("");
    setTxHistory([]);
    
    localStorage.removeItem("rakshastra.walletConnected");
    localStorage.removeItem("rakshastra.walletAddress");
    localStorage.removeItem("rakshastra.walletBalance");
    localStorage.removeItem("rakshastra.algoTxId");
    localStorage.removeItem("rakshastra.txHistory");
  };

  const handleSignTransaction = () => {
    if (!connected) return;
    setSigning(true);
    
    const cost = pricing[selectedEndpoint] || 0.05;
    
    // Simulate transaction signing delay on Pera App
    setTimeout(() => {
      // Generate mock Algorand transaction ID format (Base32, length 52, starts with MOCK_TX_ for backend mock bypass)
      const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
      let randPart = "";
      for (let i = 0; i < 40; i++) {
        randPart += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
      }
      const newTxId = `MOCK_TX_${randPart}`;
      
      const newBalance = Math.max(0, parseFloat((balance - cost).toFixed(2)));
      const timestamp = new Date().toLocaleTimeString();
      
      const newTxItem: TransactionItem = {
        id: newTxId,
        timestamp,
        endpoint: selectedEndpoint,
        amountAlgo: cost
      };
      
      const updatedHistory = [newTxItem, ...txHistory].slice(0, 10);
      
      setBalance(newBalance);
      setActiveTxId(newTxId);
      setTxHistory(updatedHistory);
      setSigning(false);
      
      localStorage.setItem("rakshastra.walletBalance", String(newBalance));
      localStorage.setItem("rakshastra.algoTxId", newTxId);
      localStorage.setItem("rakshastra.txHistory", JSON.stringify(updatedHistory));
    }, 2000);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const truncateAddress = (addr: string) => {
    if (addr.length <= 12) return addr;
    return `${addr.slice(0, 6)}...${addr.slice(-6)}`;
  };

  return (
    <div className="bg-[#151515] border border-white/5 rounded-xl p-5 relative overflow-hidden flex flex-col gap-4 font-mono text-xs select-none">
      <div className="absolute top-0 right-0 w-[150px] h-[150px] bg-[#6F00FF]/5 rounded-full blur-[60px] pointer-events-none" />
      
      {/* Header */}
      <div className="flex justify-between items-center border-b border-white/5 pb-3">
        <div className="flex flex-col gap-0.5">
          <span className="text-[9px] tracking-widest text-[#00F0FF] font-bold uppercase flex items-center gap-1">
            <Zap className="h-3 w-3 animate-pulse" /> x402 Micropayments
          </span>
          <h2 className="text-white font-bold">ALGORAND BILLING HUB</h2>
        </div>
        <Badge tone={connected ? "success" : "outline"} className="text-[8px] uppercase tracking-wider font-bold">
          {connected ? "LIVE" : "UNLINKED"}
        </Badge>
      </div>

      {/* Wallet Connection Status */}
      {!connected ? (
        <div className="bg-[#0B0B0B] border border-white/5 rounded-lg p-5 flex flex-col items-center gap-3 text-center">
          <Wallet className="h-8 w-8 text-white/30 animate-bounce" />
          <div className="flex flex-col gap-0.5">
            <span className="text-white text-[11px] font-bold">No Wallet Linked</span>
            <span className="text-[9px] text-text-tertiary">Link your Pera wallet to authorize micropayments.</span>
          </div>
          <Button 
            onClick={handleConnectWallet}
            className="w-full bg-[#6F00FF] hover:bg-[#6F00FF]/80 text-white text-[10px] font-bold tracking-widest uppercase transition-all duration-300"
          >
            Connect Pera Wallet
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {/* Connection Stats */}
          <div className="bg-[#0B0B0B] border border-white/5 rounded-lg p-3 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
              <div className="flex flex-col">
                <span className="text-white font-bold text-[10px]">{truncateAddress(address)}</span>
                <span className="text-[8px] text-text-tertiary">Pera Wallet Connect</span>
              </div>
            </div>
            <div className="flex flex-col items-end">
              <span className="text-[#00F0FF] font-bold text-[13px] flex items-center gap-1">
                <Coins className="h-3.5 w-3.5" /> {balance} ALGO
              </span>
              <button 
                onClick={handleDisconnect}
                className="text-[8px] text-red-400 hover:text-red-300 mt-0.5 cursor-pointer underline"
              >
                Disconnect
              </button>
            </div>
          </div>

          {/* Endpoint Authorization Selector */}
          <div className="flex flex-col gap-1.5">
            <span className="text-[8px] text-text-tertiary uppercase">Target Endpoint</span>
            <select
              value={selectedEndpoint}
              onChange={(e) => setSelectedEndpoint(e.target.value)}
              className="bg-[#0B0B0B] border border-white/5 rounded-lg p-2 text-white font-mono text-[10px] focus:outline-none focus:border-[#6F00FF] w-full"
            >
              <option value="/api/v1/threat/analyze-text">threat/analyze-text (0.05 ALGO)</option>
              <option value="/api/v1/entity/correlate">entity/correlate (0.10 ALGO)</option>
              <option value="/api/v1/report/generate">report/generate (0.15 ALGO)</option>
            </select>
          </div>

          {/* Authorize Transaction */}
          <Button
            onClick={handleSignTransaction}
            disabled={signing}
            className="w-full bg-[#00F0FF] hover:bg-[#00F0FF]/80 text-[#0E0E0E] text-[10px] font-bold tracking-widest uppercase transition-all duration-300 flex items-center justify-center gap-1.5"
          >
            {signing ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" /> Signing via Pera Mobile...
              </>
            ) : (
              <>
                <ArrowRightLeft className="h-3 w-3" /> Authorize micro-payment
              </>
            )}
          </Button>

          {/* Active Transaction Display */}
          {activeTxId && (
            <div className="bg-[#121212] border border-[#00F0FF]/20 rounded-lg p-2.5 flex flex-col gap-1.5 relative overflow-hidden">
              <div className="flex justify-between items-center">
                <span className="text-[#00F0FF] text-[8px] font-bold uppercase flex items-center gap-1">
                  <ShieldCheck className="h-3.5 w-3.5" /> ACTIVE CREDIT TRANSACTION
                </span>
                <button 
                  onClick={() => copyToClipboard(activeTxId)}
                  className="text-text-tertiary hover:text-white cursor-pointer"
                  title="Copy Transaction ID"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
              </div>
              <span className="text-white text-[9px] break-all select-all pr-5">{activeTxId}</span>
              <span className="text-[8px] text-text-tertiary">All subsequent API requests carry this active validation voucher.</span>
            </div>
          )}
        </div>
      )}

      {/* Transaction History Ledger */}
      {txHistory.length > 0 && (
        <div className="flex flex-col gap-2 border-t border-white/5 pt-3">
          <span className="text-[8px] text-text-tertiary uppercase tracking-wider">Transaction Ledger</span>
          <div className="max-h-[110px] overflow-y-auto space-y-1.5 pr-1 scrollbar-none text-[8px] text-text-secondary">
            {txHistory.map((tx) => (
              <div key={tx.id} className="bg-[#0B0B0B] border border-white/5 rounded p-1.5 flex justify-between items-center">
                <div className="flex flex-col gap-0.5">
                  <span className="text-white font-bold truncate max-w-[170px]" title={tx.endpoint}>
                    {tx.endpoint.replace("/api/v1/", "")}
                  </span>
                  <span className="text-text-tertiary truncate max-w-[170px]">{tx.id.substring(0, 15)}...</span>
                </div>
                <div className="flex flex-col items-end">
                  <span className="text-[#00F0FF] font-bold">-{tx.amountAlgo} ALGO</span>
                  <span className="text-text-tertiary">{tx.timestamp}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connection Loader Modal Overlay */}
      {showQrModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in font-mono">
          <div className="bg-[#121212] border border-white/10 rounded-xl p-6 max-w-sm w-full flex flex-col items-center gap-4 text-center relative overflow-hidden shadow-2xl">
            <div className="absolute top-0 right-0 w-[100px] h-[100px] bg-[#6F00FF]/10 rounded-full blur-[40px]" />
            <h3 className="text-white text-xs font-bold tracking-widest uppercase">Link Pera Wallet</h3>
            
            {/* Mock QR Code */}
            <div className="bg-white p-3 rounded-lg flex items-center justify-center border border-white/20">
              <QrCode className="h-[140px] w-[140px] text-[#121212]" />
            </div>
            
            <div className="flex flex-col gap-1 text-[9px]">
              <span className="text-white font-bold flex items-center justify-center gap-1.5">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-[#00F0FF]" /> Scan using your Pera Mobile App
              </span>
              <span className="text-text-tertiary">Establishing secure wallet handshake...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
