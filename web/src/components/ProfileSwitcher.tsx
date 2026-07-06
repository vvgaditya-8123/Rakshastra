import { useState } from "react";
import { FolderOpen } from "lucide-react";
import {
  Select,
  SelectOption,
} from "@nous-research/ui/ui/components/select";
import { cn } from "@/lib/utils";

export function ProfileSwitcher({ collapsed }: ProfileSwitcherProps) {
  const [activeCase, setActiveCase] = useState("CASE-2026-NDPS-089");

  if (collapsed) {
    return (
      <div className="flex justify-center border-b border-current/10 py-3 text-[#E56A21]">
        <FolderOpen className="h-4 w-4" />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col gap-1 border-b border-current/10 px-4 py-3 bg-[#0F0F0F]",
      )}
      title="Current Investigation Case"
    >
      <div className="flex items-center gap-1.5 text-[10px] font-mono tracking-wider text-text-tertiary uppercase">
        <FolderOpen className="h-3 w-3 text-[#E56A21]" />
        <span>CURRENT CASE</span>
      </div>

      <Select
        className={cn(
          "min-w-0 flex-1",
          "[&_button]:h-8 [&_button]:border-border [&_button]:bg-background [&_button]:px-2 [&_button]:text-[11px]",
          "[&_button]:font-mono [&_button]:uppercase [&_button]:tracking-wider [&_button]:border-orange-500/20 [&_button]:text-orange-500",
          "[&_[role=listbox]>div]:font-mono [&_[role=listbox]>div]:text-[11px]",
        )}
        id="rakshastra-case-switcher"
        onValueChange={setActiveCase}
        value={activeCase}
      >
        <SelectOption value="CASE-2026-NDPS-089">CASE-2026-NDPS-089</SelectOption>
        <SelectOption value="CASE-2026-HEROIN-042">CASE-2026-HEROIN-042</SelectOption>
        <SelectOption value="CASE-2026-DARKWEB-115">CASE-2026-DARKWEB-115</SelectOption>
        <SelectOption value="CASE-2026-COCAINE-309">CASE-2026-COCAINE-309</SelectOption>
      </Select>
    </div>
  );
}

interface ProfileSwitcherProps {
  collapsed?: boolean;
}
