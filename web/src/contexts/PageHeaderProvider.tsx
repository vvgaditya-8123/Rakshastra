import { useLayoutEffect, useMemo, useState, useEffect, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { PageHeaderContext } from "./page-header-context";
import { resolvePageTitle } from "@/lib/resolve-page-title";
import { cn } from "@/lib/utils";
import { useI18n } from "@/i18n";
import { Search, Bell, User, Shield, Cpu, FolderOpen, Radio } from "lucide-react";
import { api } from "@/lib/api";
import type { StatusResponse } from "@/lib/api";

export function PageHeaderProvider({
  children,
  pluginTabs,
}: {
  children: ReactNode;
  pluginTabs: { path: string; label: string }[];
}) {
  const { pathname } = useLocation();
  const { t } = useI18n();
  const [titleOverride, setTitleOverride] = useState<string | null>(null);
  const [afterTitle, setAfterTitle] = useState<ReactNode>(null);
  const [end, setEnd] = useState<ReactNode>(null);
  const [searchValue, setSearchValue] = useState("");

  // Dynamic status & case info
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [activeProfile, setActiveProfile] = useState<string>("default");
  const [modelLabel, setModelLabel] = useState<string>("AUTO");
  const [userDisplay, setUserDisplay] = useState<string>("INVESTIGATOR");

  useLayoutEffect(() => {
    setTitleOverride(null);
    setAfterTitle(null);
    setEnd(null);
  }, [pathname]);

  const defaultTitle = useMemo(
    () => resolvePageTitle(pathname, t, pluginTabs),
    [pathname, t, pluginTabs],
  );
  const displayTitle = titleOverride ?? defaultTitle;

  const isChatRoute = pathname === "/chat" || pathname === "/chat/";

  // Load dynamic header data
  useEffect(() => {
    const fetchStatus = () => {
      api.getStatus()
        .then(setStatus)
        .catch(() => {});
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);

    // Active Profile
    api.getActiveProfile()
      .then((info) => {
        if (info && info.active) {
          setActiveProfile(info.active);
        }
      })
      .catch(() => {});

    // Config for default model
    api.getConfig()
      .then((cfg) => {
        if (cfg) {
          const modelCfg = cfg.model;
          let model = "";
          if (typeof modelCfg === "object" && modelCfg !== null) {
            model = (modelCfg as any).default || (modelCfg as any).name || "";
          } else if (typeof modelCfg === "string") {
            model = modelCfg;
          }
          if (model) {
            setModelLabel(model);
          }
        }
      })
      .catch(() => {});

    // Current logged-in user details
    api.getAuthMe()
      .then((user) => {
        if (user) {
          setUserDisplay(user.display_name || user.email || user.user_id || "INVESTIGATOR");
        }
      })
      .catch(() => {});

    return () => clearInterval(interval);
  }, []);

  // Compute active platforms/devices
  const activeDevicesLabel = useMemo(() => {
    if (!status || !status.gateway_running || !status.gateway_platforms) {
      return "WEB";
    }
    const list = Object.entries(status.gateway_platforms)
      .filter(([_, info]) => info.state === "connected" || info.state === "running" || info.state === "starting")
      .map(([name]) => name.toUpperCase());
    return list.length > 0 ? list.join(", ") : "WEB";
  }, [status]);

  const isNominal = status?.gateway_running ?? false;

  const value = useMemo(
    () => ({
      setAfterTitle,
      setEnd,
      setTitle: setTitleOverride,
    }),
    [],
  );

  return (
    <PageHeaderContext.Provider value={value}>
      <div className="flex min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden">
        {/* REDESIGNED TOP HEADER - ENTERPRISE SECURITY DESIGN */}
        <header className="z-10 w-full shrink-0 border-b border-current/10 bg-[#0E0E0E] px-6 py-2.5 flex flex-col gap-2">
          <div className="flex w-full items-center justify-between gap-4">
            {/* Left: Large Search */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-text-tertiary" />
              <input
                type="text"
                placeholder="Search JIDs, phone numbers, wallets, entities..."
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                className="w-full bg-[#151515] border border-current/15 rounded-md py-1.5 pl-9 pr-4 text-xs text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-[#E56A21]/50 focus:ring-1 focus:ring-[#E56A21]/30 font-mono transition-all"
              />
            </div>

            {/* Middle: Investigation Info & AI Model & Connected Platforms */}
            <div className="hidden xl:flex items-center gap-2.5 font-mono text-[10px] tracking-wider">
              <div className="flex items-center gap-1.5 bg-[#1A1A1A] border border-[#E56A21]/20 px-2.5 py-1 rounded-md text-[#E56A21]">
                <FolderOpen className="h-3 w-3" />
                <span>CASE: {activeProfile.toUpperCase()}</span>
              </div>
              <div className="flex items-center gap-1.5 bg-[#1A1A1A] border border-current/5 px-2.5 py-1 rounded-md text-amber-500">
                <Cpu className="h-3 w-3" />
                <span>AI: {modelLabel.toUpperCase()}</span>
              </div>
              <div className="flex items-center gap-1.5 bg-[#1A1A1A] border border-current/5 px-2.5 py-1 rounded-md text-emerald-500">
                <Radio className="h-3 w-3 animate-pulse" />
                <span>DEVICES: {activeDevicesLabel}</span>
              </div>
            </div>

            {/* Right: Notifications, User, Status */}
            <div className="flex items-center gap-4">
              {/* Notification Center */}
              <button className="relative p-1.5 text-text-secondary hover:text-white transition-colors bg-transparent border-0 cursor-pointer">
                <Bell className="h-4 w-4" />
                <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-[#E56A21] animate-ping" />
                <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-[#E56A21]" />
              </button>

              {/* Current User */}
              <div className="flex items-center gap-2 border-l border-current/10 pl-4 font-mono text-xs">
                <User className="h-5 w-5 text-text-secondary rounded-full bg-[#1A1A1A] p-0.5" />
                <div className="flex flex-col text-left">
                  <span className="text-[11px] font-bold text-text-primary leading-tight uppercase">{userDisplay.split("@")[0]}</span>
                  <span className="text-[8px] text-text-tertiary leading-none uppercase">Admin</span>
                </div>
              </div>

              {/* System Status */}
              <div className="hidden md:flex items-center gap-2 bg-[#151515] border border-current/10 px-2.5 py-1 rounded-md text-xs font-mono">
                <Shield className={cn("h-3.5 w-3.5", isNominal ? "text-emerald-500" : "text-amber-500")} />
                <span className={cn("font-bold text-[10px] tracking-wider uppercase", isNominal ? "text-emerald-500" : "text-amber-500")}>
                  {isNominal ? "NOMINAL" : "OFFLINE"}
                </span>
                <span className={cn("h-1.5 w-1.5 rounded-full", isNominal ? "bg-emerald-500 animate-pulse" : "bg-amber-500")} />
              </div>
            </div>
          </div>
        </header>

        {/* Compatibility Header for Page Title & Toolbar Actions */}
        {(displayTitle || afterTitle || end) && (
          <header className="z-1 w-full shrink-0 border-b border-current/10 bg-background-base min-h-[2.5rem] py-1.5 flex items-center justify-between px-6">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              <h2 className="font-expanded text-xs font-bold tracking-[0.1em] text-text-tertiary uppercase">
                {displayTitle}
              </h2>
              {afterTitle && (
                <div className="shrink-0 overflow-visible">
                  {afterTitle}
                </div>
              )}
            </div>
            {end && (
              <div className="flex min-w-0 justify-end">
                {end}
              </div>
            )}
          </header>
        )}

        <main
          className={cn(
            "min-h-0 w-full min-w-0 flex-1 flex flex-col",
            isChatRoute
              ? "overflow-hidden"
              : "overflow-y-auto overflow-x-hidden [scrollbar-gutter:stable]",
          )}
        >
          {children}
        </main>
      </div>
    </PageHeaderContext.Provider>
  );
}
