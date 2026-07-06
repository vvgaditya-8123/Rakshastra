"use client";

import { motion } from "framer-motion";
import { useTheme } from "next-themes";
import React, { createContext, useContext, useCallback, useEffect, useState, useRef } from "react";

// Local CSS classes helper
const cn = (...classes: any[]) => classes.filter(Boolean).join(" ");

// Custom SVG replace for lucide-react GripHorizontal
const GripHorizontal = ({ className }: { className?: string }) => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <circle cx="12" cy="9" r="1" />
    <circle cx="19" cy="9" r="1" />
    <circle cx="5" cy="9" r="1" />
    <circle cx="12" cy="15" r="1" />
    <circle cx="19" cy="15" r="1" />
    <circle cx="5" cy="15" r="1" />
  </svg>
);

export type AnimationVariant =
  | "circle"
  | "rectangle"
  | "gif"
  | "polygon"
  | "circle-blur";
export type AnimationStart =
  | "top-left"
  | "top-right"
  | "bottom-left"
  | "bottom-right"
  | "center"
  | "top-center"
  | "bottom-center"
  | "bottom-up"
  | "top-down"
  | "left-right"
  | "right-left";

interface Animation {
  name: string;
  css: string;
}

// React Context for sharing transition configurations
interface TransitionConfig {
  variant: AnimationVariant;
  start: AnimationStart;
  blur: boolean;
  gifType: "1" | "2" | "3" | "custom";
  gifUrl: string;
  setVariant: (v: AnimationVariant) => void;
  setStart: (s: AnimationStart) => void;
  setBlur: (b: boolean) => void;
  setGifType: (t: "1" | "2" | "3" | "custom") => void;
  setGifUrl: (u: string) => void;
}

const TransitionContext = createContext<TransitionConfig | null>(null);

export function TransitionProvider({ children }: { children: React.ReactNode }) {
  const [variant, setVariant] = useState<AnimationVariant>("circle");
  const [start, setStart] = useState<AnimationStart>("center");
  const [blur, setBlur] = useState<boolean>(false);
  const [gifType, setGifType] = useState<"1" | "2" | "3" | "custom">("1");
  const [gifUrl, setGifUrl] = useState<string>(
    "https://media.giphy.com/media/KBbr4hHl9DSahKvInO/giphy.gif?cid=790b76112m5eeeydoe7et0cr3j3ekb1erunxozyshuhxx2vl&ep=v1_stickers_search&rid=giphy.gif&ct=s",
  );

  return (
    <TransitionContext.Provider
      value={{
        variant,
        start,
        blur,
        gifType,
        gifUrl,
        setVariant,
        setStart,
        setBlur,
        setGifType,
        setGifUrl,
      }}
    >
      {children}
    </TransitionContext.Provider>
  );
}

export function useTransitionContext() {
  const ctx = useContext(TransitionContext);
  if (!ctx) {
    return {
      variant: "circle" as AnimationVariant,
      start: "center" as AnimationStart,
      blur: false,
      gifType: "1" as const,
      gifUrl: "",
      setVariant: () => {},
      setStart: () => {},
      setBlur: () => {},
      setGifType: () => {},
      setGifUrl: () => {},
    };
  }
  return ctx;
}

const getPositionCoords = (position: AnimationStart) => {
  switch (position) {
    case "top-left":
      return { cx: "0", cy: "0" };
    case "top-right":
      return { cx: "40", cy: "0" };
    case "bottom-left":
      return { cx: "0", cy: "40" };
    case "bottom-right":
      return { cx: "40", cy: "40" };
    case "top-center":
      return { cx: "20", cy: "0" };
    case "bottom-center":
      return { cx: "20", cy: "40" };
    case "bottom-up":
    case "top-down":
    case "left-right":
    case "right-left":
      return { cx: "20", cy: "20" };
  }
};

const generateSVG = (variant: AnimationVariant, start: AnimationStart) => {
  if (variant === "circle-blur") {
    if (start === "center") {
      return `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><defs><filter id="blur"><feGaussianBlur stdDeviation="2"/></filter></defs><circle cx="20" cy="20" r="18" fill="white" filter="url(%23blur)"/></svg>`;
    }
    const positionCoords = getPositionCoords(start);
    if (!positionCoords) return "";
    const { cx, cy } = positionCoords;
    return `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><defs><filter id="blur"><feGaussianBlur stdDeviation="2"/></filter></defs><circle cx="${cx}" cy="${cy}" r="18" fill="white" filter="url(%23blur)"/></svg>`;
  }

  if (start === "center") return "";
  if (variant === "rectangle") return "";

  const positionCoords = getPositionCoords(start);
  if (!positionCoords) return "";
  const { cx, cy } = positionCoords;

  if (variant === "circle") {
    return `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><circle cx="${cx}" cy="${cy}" r="20" fill="white"/></svg>`;
  }

  return "";
};

const getTransformOrigin = (start: AnimationStart) => {
  switch (start) {
    case "top-left":
      return "top left";
    case "top-right":
      return "top right";
    case "bottom-left":
      return "bottom left";
    case "bottom-right":
      return "bottom right";
    case "top-center":
      return "top center";
    case "bottom-center":
      return "bottom center";
    case "bottom-up":
    case "top-down":
    case "left-right":
    case "right-left":
      return "center";
  }
};

export const createAnimation = (
  variant: AnimationVariant,
  start: AnimationStart = "center",
  blur = false,
  url?: string,
): Animation => {
  const svg = generateSVG(variant, start);
  const transformOrigin = getTransformOrigin(start);

  if (variant === "rectangle") {
    const getClipPath = (direction: AnimationStart) => {
      switch (direction) {
        case "bottom-up":
          return {
            from: "polygon(0% 100%, 100% 100%, 100% 100%, 0% 100%)",
            to: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
          };
        case "top-down":
          return {
            from: "polygon(0% 0%, 100% 0%, 100% 0%, 0% 0%)",
            to: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
          };
        case "left-right":
          return {
            from: "polygon(0% 0%, 0% 0%, 0% 100%, 0% 100%)",
            to: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
          };
        case "right-left":
          return {
            from: "polygon(100% 0%, 100% 0%, 100% 100%, 100% 100%)",
            to: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
          };
        case "top-left":
          return {
            from: "polygon(0% 0%, 0% 0%, 0% 0%, 0% 0%)",
            to: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
          };
        case "top-right":
          return {
            from: "polygon(100% 0%, 100% 0%, 100% 0%, 100% 0%)",
            to: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
          };
        case "bottom-left":
          return {
            from: "polygon(0% 100%, 0% 100%, 0% 100%, 0% 100%)",
            to: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
          };
        case "bottom-right":
          return {
            from: "polygon(100% 100%, 100% 100%, 100% 100%, 100% 100%)",
            to: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
          };
        default:
          return {
            from: "polygon(0% 100%, 100% 100%, 100% 100%, 0% 100%)",
            to: "polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)",
          };
      }
    };

    const clipPath = getClipPath(start);

    return {
      name: `${variant}-${start}${blur ? "-blur" : ""}`,
      css: `
       ::view-transition-group(root) {
        animation-duration: 0.7s;
        animation-timing-function: var(--expo-out);
      }
            
      ::view-transition-new(root) {
        animation-name: reveal-light-${start}${blur ? "-blur" : ""};
        ${blur ? "filter: blur(2px);" : ""}
      }

      ::view-transition-old(root),
      .dark::view-transition-old(root) {
        animation: none;
        z-index: -1;
      }
      .dark::view-transition-new(root) {
        animation-name: reveal-dark-${start}${blur ? "-blur" : ""};
        ${blur ? "filter: blur(2px);" : ""}
      }

      @keyframes reveal-dark-${start}${blur ? "-blur" : ""} {
        from {
          clip-path: ${clipPath.from};
          ${blur ? "filter: blur(8px);" : ""}
        }
        ${blur ? "50% { filter: blur(4px); }" : ""}
        to {
          clip-path: ${clipPath.to};
          ${blur ? "filter: blur(0px);" : ""}
        }
      }

      @keyframes reveal-light-${start}${blur ? "-blur" : ""} {
        from {
          clip-path: ${clipPath.from};
          ${blur ? "filter: blur(8px);" : ""}
        }
        ${blur ? "50% { filter: blur(4px); }" : ""}
        to {
          clip-path: ${clipPath.to};
          ${blur ? "filter: blur(0px);" : ""}
        }
      }
      `,
    };
  }

  if (variant === "circle" && start === "center") {
    return {
      name: `${variant}-${start}${blur ? "-blur" : ""}`,
      css: `
       ::view-transition-group(root) {
        animation-duration: 0.7s;
        animation-timing-function: var(--expo-out);
      }
            
      ::view-transition-new(root) {
        animation-name: reveal-light${blur ? "-blur" : ""};
        ${blur ? "filter: blur(2px);" : ""}
      }

      ::view-transition-old(root),
      .dark::view-transition-old(root) {
        animation: none;
        z-index: -1;
      }
      .dark::view-transition-new(root) {
        animation-name: reveal-dark${blur ? "-blur" : ""};
        ${blur ? "filter: blur(2px);" : ""}
      }

      @keyframes reveal-dark${blur ? "-blur" : ""} {
        from {
          clip-path: circle(0% at 50% 50%);
          ${blur ? "filter: blur(8px);" : ""}
        }
        ${blur ? "50% { filter: blur(4px); }" : ""}
        to {
          clip-path: circle(100.0% at 50% 50%);
          ${blur ? "filter: blur(0px);" : ""}
        }
      }

      @keyframes reveal-light${blur ? "-blur" : ""} {
        from {
           clip-path: circle(0% at 50% 50%);
           ${blur ? "filter: blur(8px);" : ""}
        }
        ${blur ? "50% { filter: blur(4px); }" : ""}
        to {
          clip-path: circle(100.0% at 50% 50%);
          ${blur ? "filter: blur(0px);" : ""}
        }
      }
      `,
    };
  }

  if (variant === "gif") {
    return {
      name: `${variant}-${start}`,
      css: `
      ::view-transition-group(root) {
        animation-timing-function: var(--expo-in);
      }

      ::view-transition-new(root) {
        mask: url('${url}') center / 0 no-repeat;
        animation: scale 3s;
      }

      ::view-transition-old(root),
      .dark::view-transition-old(root) {
        animation: scale 3s;
      }

      @keyframes scale {
        0% {
          mask-size: 0;
        }
        10% {
          mask-size: 50vmax;
        }
        90% {
          mask-size: 50vmax;
        }
        100% {
          mask-size: 2000vmax;
        }
      }`,
    };
  }

  if (variant === "circle-blur") {
    if (start === "center") {
      return {
        name: `${variant}-${start}`,
        css: `
        ::view-transition-group(root) {
          animation-timing-function: var(--expo-out);
        }

        ::view-transition-new(root) {
          mask: url('${svg}') center / 0 no-repeat;
          mask-origin: content-box;
          animation: scale 1s;
          transform-origin: center;
        }

        ::view-transition-old(root),
        .dark::view-transition-old(root) {
          animation: scale 1s;
          transform-origin: center;
          z-index: -1;
        }

        @keyframes scale {
          to {
            mask-size: 350vmax;
          }
        }
        `,
      };
    }

    return {
      name: `${variant}-${start}`,
      css: `
      ::view-transition-group(root) {
        animation-timing-function: var(--expo-out);
      }

      ::view-transition-new(root) {
        mask: url('${svg}') ${start.replace("-", " ")} / 0 no-repeat;
        mask-origin: content-box;
        animation: scale 1s;
        transform-origin: ${transformOrigin};
      }

      ::view-transition-old(root),
      .dark::view-transition-old(root) {
        animation: scale 1s;
        transform-origin: ${transformOrigin};
        z-index: -1;
      }

      @keyframes scale {
        to {
          mask-size: 350vmax;
        }
      }
      `,
    };
  }

  if (variant === "polygon") {
    const getPolygonClipPaths = (position: AnimationStart) => {
      switch (position) {
        case "top-left":
          return {
            darkFrom: "polygon(50% -71%, -50% 71%, -50% 71%, 50% -71%)",
            darkTo: "polygon(50% -71%, -50% 71%, 50% 171%, 171% 50%)",
            lightFrom: "polygon(171% 50%, 50% 171%, 50% 171%, 171% 50%)",
            lightTo: "polygon(171% 50%, 50% 171%, -50% 71%, 50% -71%)",
          };
        case "top-right":
          return {
            darkFrom: "polygon(150% -71%, 250% 71%, 250% 71%, 150% -71%)",
            darkTo: "polygon(150% -71%, 250% 71%, 50% 171%, -71% 50%)",
            lightFrom: "polygon(-71% 50%, 50% 171%, 50% 171%, -71% 50%)",
            lightTo: "polygon(-71% 50%, 50% 171%, 250% 71%, 150% -71%)",
          };
        default:
          return {
            darkFrom: "polygon(50% -71%, -50% 71%, -50% 71%, 50% -71%)",
            darkTo: "polygon(50% -71%, -50% 71%, 50% 171%, 171% 50%)",
            lightFrom: "polygon(171% 50%, 50% 171%, 50% 171%, 171% 50%)",
            lightTo: "polygon(171% 50%, 50% 171%, -50% 71%, 50% -71%)",
          };
      }
    };

    const clipPaths = getPolygonClipPaths(start);

    return {
      name: `${variant}-${start}${blur ? "-blur" : ""}`,
      css: `
      ::view-transition-group(root) {
        animation-duration: 0.7s;
        animation-timing-function: var(--expo-out);
      }
            
      ::view-transition-new(root) {
        animation-name: reveal-light-${start}${blur ? "-blur" : ""};
        ${blur ? "filter: blur(2px);" : ""}
      }

      ::view-transition-old(root),
      .dark::view-transition-old(root) {
        animation: none;
        z-index: -1;
      }
      .dark::view-transition-new(root) {
        animation-name: reveal-dark-${start}${blur ? "-blur" : ""};
        ${blur ? "filter: blur(2px);" : ""}
      }

      @keyframes reveal-dark-${start}${blur ? "-blur" : ""} {
        from {
          clip-path: ${clipPaths.darkFrom};
          ${blur ? "filter: blur(8px);" : ""}
        }
        ${blur ? "50% { filter: blur(4px); }" : ""}
        to {
          clip-path: ${clipPaths.darkTo};
          ${blur ? "filter: blur(0px);" : ""}
        }
      }

      @keyframes reveal-light-${start}${blur ? "-blur" : ""} {
        from {
          clip-path: ${clipPaths.lightFrom};
          ${blur ? "filter: blur(8px);" : ""}
        }
        ${blur ? "50% { filter: blur(4px); }" : ""}
        to {
          clip-path: ${clipPaths.lightTo};
          ${blur ? "filter: blur(0px);" : ""}
        }
      }
      `,
    };
  }

  if (variant === "circle" && start !== "center") {
    const getClipPathPosition = (position: AnimationStart) => {
      switch (position) {
        case "top-left":
          return "0% 0%";
        case "top-right":
          return "100% 0%";
        case "bottom-left":
          return "0% 100%";
        case "bottom-right":
          return "100% 100%";
        case "top-center":
          return "50% 0%";
        case "bottom-center":
          return "50% 100%";
        default:
          return "50% 50%";
      }
    };

    const clipPosition = getClipPathPosition(start);

    return {
      name: `${variant}-${start}${blur ? "-blur" : ""}`,
      css: `
       ::view-transition-group(root) {
        animation-duration: 1s;
        animation-timing-function: var(--expo-out);
      }
            
      ::view-transition-new(root) {
        animation-name: reveal-light-${start}${blur ? "-blur" : ""};
        ${blur ? "filter: blur(2px);" : ""}
      }

      ::view-transition-old(root),
      .dark::view-transition-old(root) {
        animation: none;
        z-index: -1;
      }
      .dark::view-transition-new(root) {
        animation-name: reveal-dark-${start}${blur ? "-blur" : ""};
        ${blur ? "filter: blur(2px);" : ""}
      }

      @keyframes reveal-dark-${start}${blur ? "-blur" : ""} {
        from {
          clip-path: circle(0% at ${clipPosition});
          ${blur ? "filter: blur(8px);" : ""}
        }
        ${blur ? "50% { filter: blur(4px); }" : ""}
        to {
          clip-path: circle(150.0% at ${clipPosition});
          ${blur ? "filter: blur(0px);" : ""}
        }
      }

      @keyframes reveal-light-${start}${blur ? "-blur" : ""} {
        from {
           clip-path: circle(0% at ${clipPosition});
           ${blur ? "filter: blur(8px);" : ""}
        }
        ${blur ? "50% { filter: blur(4px); }" : ""}
        to {
          clip-path: circle(150.0% at ${clipPosition});
          ${blur ? "filter: blur(0px);" : ""}
        }
      }
      `,
    };
  }

  return {
    name: `${variant}-${start}${blur ? "-blur" : ""}`,
    css: `
      ::view-transition-group(root) {
        animation-timing-function: var(--expo-in);
      }
      ::view-transition-new(root) {
        mask: url('${svg}') ${start.replace("-", " ")} / 0 no-repeat;
        mask-origin: content-box;
        animation: scale-${start}${blur ? "-blur" : ""} 1s;
        transform-origin: ${transformOrigin};
        ${blur ? "filter: blur(2px);" : ""}
      }
      ::view-transition-old(root),
      .dark::view-transition-old(root) {
        animation: scale-${start}${blur ? "-blur" : ""} 1s;
        transform-origin: ${transformOrigin};
        z-index: -1;
      }
      @keyframes scale-${start}${blur ? "-blur" : ""} {
        from {
          ${blur ? "filter: blur(8px);" : ""}
        }
        ${blur ? "50% { filter: blur(4px); }" : ""}
        to {
          mask-size: 2000vmax;
          ${blur ? "filter: blur(0px);" : ""}
        }
      }
    `,
  };
};

export const useThemeToggle = ({
  variant = "circle",
  start = "center",
  blur = false,
  gifUrl = "",
}: {
  variant?: AnimationVariant;
  start?: AnimationStart;
  blur?: boolean;
  gifUrl?: string;
} = {}) => {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    setIsDark(resolvedTheme === "dark");
  }, [resolvedTheme]);

  const styleId = "theme-transition-styles";

  const updateStyles = useCallback((css: string, name: string) => {
    if (typeof window === "undefined") return;

    let styleElement = document.getElementById(styleId) as HTMLStyleElement;

    if (!styleElement) {
      styleElement = document.createElement("style");
      styleElement.id = styleId;
      document.head.appendChild(styleElement);
    }

    styleElement.textContent = css;
  }, []);

  const toggleTheme = useCallback(() => {
    const nextIsDark = !isDark;
    setIsDark(nextIsDark);

    const animation = createAnimation(variant, start, blur, gifUrl);
    updateStyles(animation.css, animation.name);

    if (typeof window === "undefined") return;

    const switchTheme = () => {
      setTheme(theme === "light" ? "dark" : "light");
    };

    const doc = document as any;
    if (!doc.startViewTransition) {
      switchTheme();
      return;
    }

    doc.startViewTransition(switchTheme);
  }, [
    theme,
    setTheme,
    variant,
    start,
    blur,
    gifUrl,
    updateStyles,
    isDark,
    setIsDark,
  ]);

  return {
    isDark,
    setIsDark,
    toggleTheme,
  };
};

export const ThemeToggleButton = ({
  className = "",
}: {
  className?: string;
}) => {
  const { variant, start, blur, gifUrl } = useTransitionContext();
  const { isDark, toggleTheme } = useThemeToggle({
    variant,
    start,
    blur,
    gifUrl,
  });

  return (
    <button
      type="button"
      className={cn(
        "size-9 cursor-pointer rounded-full bg-white dark:bg-black p-0 border border-black/10 dark:border-white/10 transition-all duration-300 active:scale-95 flex items-center justify-center",
        className,
      )}
      onClick={toggleTheme}
      aria-label="Toggle theme"
      style={{ minWidth: "36px", height: "36px" }}
    >
      <span className="sr-only">Toggle theme</span>
      <svg viewBox="0 0 240 240" fill="none" xmlns="http://www.w3.org/2000/svg" className="size-5">
        <motion.g
          animate={{ rotate: isDark ? -180 : 0 }}
          transition={{ ease: "easeInOut", duration: 0.5 }}
        >
          <path
            d="M120 67.5C149.25 67.5 172.5 90.75 172.5 120C172.5 149.25 149.25 172.5 120 172.5"
            fill={isDark ? "white" : "black"}
          />
          <path
            d="M120 67.5C90.75 67.5 67.5 90.75 67.5 120C67.5 149.25 90.75 172.5 120 172.5"
            fill={isDark ? "black" : "white"}
          />
        </motion.g>
        <motion.path
          animate={{ rotate: isDark ? 180 : 0 }}
          transition={{ ease: "easeInOut", duration: 0.5 }}
          d="M120 3.75C55.5 3.75 3.75 55.5 3.75 120C3.75 184.5 55.5 236.25 120 236.25C184.5 236.25 236.25 184.5 236.25 120C236.25 55.5 184.5 3.75 120 3.75ZM120 214.5V172.5C90.75 172.5 67.5 149.25 67.5 120C67.5 90.75 90.75 67.5 120 67.5V25.5C172.5 25.5 214.5 67.5 214.5 120C214.5 172.5 172.5 214.5 120 214.5Z"
          fill={isDark ? "white" : "black"}
        />
      </svg>
    </button>
  );
};

export const Options = () => {
  const {
    variant,
    start,
    blur,
    gifType,
    gifUrl,
    setVariant,
    setStart,
    setBlur,
    setGifType,
    setGifUrl,
  } = useTransitionContext();

  const [isOpen, setIsOpen] = useState(false);

  return (
    <div style={{ position: "fixed", bottom: "24px", right: "24px", zIndex: 100 }}>
      {/* Floating Settings Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          style={{
            background: "rgba(32, 31, 30, 0.7)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "50%",
            width: "44px",
            height: "44px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            color: "var(--fg-2)",
            boxShadow: "0 10px 25px rgba(0,0,0,0.3)",
            transition: "all 0.3s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "var(--coral)";
            e.currentTarget.style.transform = "scale(1.05)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = "var(--fg-2)";
            e.currentTarget.style.transform = "scale(1)";
          }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.1a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        </button>
      )}

      {/* Floating Card Options Panel */}
      {isOpen && (
        <motion.div
          drag
          dragMomentum={false}
          className="flex w-[245px] flex-col gap-3 rounded-2xl border p-4 backdrop-blur-md theme-settings-panel"
        >
          <div
            className="flex items-center justify-between"
            style={{ borderBottom: "1px solid var(--bg-4)", paddingBottom: "8px" }}
          >
            <div className="flex items-center gap-1.5">
              <span
                className="cursor-grab active:cursor-grabbing"
                style={{ color: "var(--fg-4)", display: "flex" }}
              >
                <GripHorizontal className="size-4" />
              </span>
              <p
                style={{
                  fontSize: "0.75rem",
                  fontFamily: "var(--font-mono)",
                  fontWeight: "bold",
                  color: "var(--coral)",
                }}
              >
                TRANSITION_SETTINGS
              </p>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: "none",
                border: "none",
                color: "var(--fg-4)",
                cursor: "pointer",
                fontSize: "1rem",
                display: "flex",
                alignItems: "center",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--fg-1)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--fg-4)")}
            >
              ×
            </button>
          </div>

          <div
            className="flex flex-col gap-3"
            style={{ fontSize: "0.72rem", color: "var(--fg-3)" }}
          >
            {/* Variant Option */}
            <div className="flex justify-between items-start">
              <span style={{ fontFamily: "var(--font-mono)", color: "var(--fg-4)" }}>VARIANT:</span>
              <div className="flex flex-wrap justify-end gap-x-1.5 gap-y-1 max-w-[150px]">
                {(["circle", "rectangle", "gif", "polygon", "circle-blur"] as AnimationVariant[]).map((v) => (
                  <button
                    key={v}
                    onClick={() => setVariant(v)}
                    style={{
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      fontSize: "0.7rem",
                      color: variant === v ? "var(--turquoise)" : "var(--fg-4)",
                      fontWeight: variant === v ? "bold" : "normal",
                      padding: 0,
                    }}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>

            {/* Blur Option */}
            <div className="flex justify-between items-center">
              <span style={{ fontFamily: "var(--font-mono)", color: "var(--fg-4)" }}>BLUR:</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setBlur(false)}
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "0.7rem",
                    color: !blur ? "var(--turquoise)" : "var(--fg-4)",
                    fontWeight: !blur ? "bold" : "normal",
                  }}
                >
                  OFF
                </button>
                <button
                  onClick={() => setBlur(true)}
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "0.7rem",
                    color: blur ? "var(--turquoise)" : "var(--fg-4)",
                    fontWeight: blur ? "bold" : "normal",
                  }}
                >
                  ON
                </button>
              </div>
            </div>

            {/* Start Directions Option */}
            {(variant === "circle" ||
              variant === "rectangle" ||
              variant === "polygon" ||
              variant === "circle-blur") && (
              <div className="flex justify-between items-start">
                <span style={{ fontFamily: "var(--font-mono)", color: "var(--fg-4)" }}>START:</span>
                <div className="flex flex-wrap justify-end gap-x-1.5 gap-y-1 max-w-[150px]">
                  {(variant === "circle" || variant === "circle-blur") && (
                    <button
                      onClick={() => setStart("center")}
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        color: start === "center" ? "var(--turquoise)" : "var(--fg-4)",
                        fontWeight: start === "center" ? "bold" : "normal",
                      }}
                    >
                      center
                    </button>
                  )}
                  {variant === "rectangle" && (
                    <>
                      {["bottom-up", "top-down", "left-right", "right-left"].map((dir) => (
                        <button
                          key={dir}
                          onClick={() => setStart(dir as AnimationStart)}
                          style={{
                            background: "none",
                            border: "none",
                            cursor: "pointer",
                            color: start === dir ? "var(--turquoise)" : "var(--fg-4)",
                            fontWeight: start === dir ? "bold" : "normal",
                          }}
                        >
                          {dir}
                        </button>
                      ))}
                    </>
                  )}
                  {(variant === "circle" || variant === "polygon" || variant === "circle-blur") && (
                    <>
                      {["top-left", "top-right"].map((dir) => (
                        <button
                          key={dir}
                          onClick={() => setStart(dir as AnimationStart)}
                          style={{
                            background: "none",
                            border: "none",
                            cursor: "pointer",
                            color: start === dir ? "var(--turquoise)" : "var(--fg-4)",
                            fontWeight: start === dir ? "bold" : "normal",
                          }}
                        >
                          {dir}
                        </button>
                      ))}
                      {variant !== "polygon" && (
                        <>
                          {["bottom-left", "bottom-right"].map((dir) => (
                            <button
                              key={dir}
                              onClick={() => setStart(dir as AnimationStart)}
                              style={{
                                background: "none",
                                border: "none",
                                cursor: "pointer",
                                color: start === dir ? "var(--turquoise)" : "var(--fg-4)",
                                fontWeight: start === dir ? "bold" : "normal",
                              }}
                            >
                              {dir}
                            </button>
                          ))}
                        </>
                      )}
                    </>
                  )}
                  {(variant === "circle" || variant === "circle-blur") && (
                    <>
                      {["top-center", "bottom-center"].map((dir) => (
                        <button
                          key={dir}
                          onClick={() => setStart(dir as AnimationStart)}
                          style={{
                            background: "none",
                            border: "none",
                            cursor: "pointer",
                            color: start === dir ? "var(--turquoise)" : "var(--fg-4)",
                            fontWeight: start === dir ? "bold" : "normal",
                          }}
                        >
                          {dir}
                        </button>
                      ))}
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Gif Option */}
            {variant === "gif" && (
              <div className="flex justify-between items-start">
                <span style={{ fontFamily: "var(--font-mono)", color: "var(--fg-4)" }}>GIF TYPE:</span>
                <div className="flex gap-2">
                  {(["1", "2", "3", "custom"] as const).map((t) => (
                    <button
                      key={t}
                      onClick={() => {
                        setGifType(t);
                        if (t === "1")
                          setGifUrl(
                            "https://media.giphy.com/media/KBbr4hHl9DSahKvInO/giphy.gif?cid=790b76112m5eeeydoe7et0cr3j3ekb1erunxozyshuhxx2vl&ep=v1_stickers_search&rid=giphy.gif&ct=s",
                          );
                        if (t === "2")
                          setGifUrl(
                            "https://media.giphy.com/media/5PncuvcXbBuIZcSiQo/giphy.gif?cid=ecf05e47j7vdjtytp3fu84rslaivdun4zvfhej6wlvl6qqsz&ep=v1_stickers_search&rid=giphy.gif&ct=s",
                          );
                        if (t === "3")
                          setGifUrl(
                            "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZ3JwcXdzcHd5MW92NWprZXVpcTBtNXM5cG9obWh0N3I4NzFpaDE3byZlcD12MV9zdGlja2Vyc19zZWFyY2gmY3Q9cw/WgsVx6C4N8tjy/giphy.gif",
                          );
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        fontSize: "0.7rem",
                        color: gifType === t ? "var(--turquoise)" : "var(--fg-4)",
                        fontWeight: gifType === t ? "bold" : "normal",
                      }}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Custom Gif Input */}
            {variant === "gif" && gifType === "custom" && (
              <div className="flex flex-col gap-1">
                <span style={{ fontFamily: "var(--font-mono)", color: "var(--fg-4)" }}>GIF URL:</span>
                <input
                  type="text"
                  value={gifUrl}
                  onChange={(e) => setGifUrl(e.target.value)}
                  placeholder="Enter GIF URL"
                  style={{
                    background: "var(--bg-3)",
                    border: "1px solid var(--bg-5)",
                    borderRadius: "4px",
                    padding: "3px 6px",
                    fontSize: "0.65rem",
                    color: "var(--fg-1)",
                    width: "100%",
                    outline: "none",
                  }}
                />
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
};
