"use client";

import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import { ThemeToggleButton } from "@/components/ThemeToggle";

export default function Header() {
  return (
    <header className="site-header">
      <div className="header-inner">
        <a href="/" className="logo">
          <span className="logo-mark">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </span>
          Rakshastra
        </a>

        <NavHeader />

        <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <ThemeToggleButton />
          <a href="#download" className="btn-accent" style={{ padding: '0.5rem 1.25rem', fontSize: '0.85rem' }}>Download</a>
        </div>
      </div>
    </header>
  );
}

function NavHeader() {
  const [position, setPosition] = useState({
    left: 0,
    width: 0,
    opacity: 0,
  });

  return (
    <ul
      className="nav-motion-ul"
      onMouseLeave={() => setPosition((pv) => ({ ...pv, opacity: 0 }))}
    >
      <Tab href="#problem" setPosition={setPosition}>Mission</Tab>
      <Tab href="#live-console" setPosition={setPosition}>Console</Tab>
      <Tab href="#capabilities" setPosition={setPosition}>Capabilities</Tab>
      <Tab href="#roadmap" setPosition={setPosition}>Roadmap</Tab>

      <Cursor position={position} />
    </ul>
  );
}

const Tab = ({
  children,
  href,
  setPosition,
}: {
  children: React.ReactNode;
  href: string;
  setPosition: any;
}) => {
  const ref = useRef<HTMLLIElement>(null);
  return (
    <li
      ref={ref}
      onMouseEnter={() => {
        if (!ref.current) return;
        const { width } = ref.current.getBoundingClientRect();
        setPosition({
          width,
          opacity: 1,
          left: ref.current.offsetLeft,
        });
      }}
      className="nav-motion-li"
    >
      <a href={href} className="absolute inset-0 z-20" />
      <span className="relative z-10">{children}</span>
    </li>
  );
};

const Cursor = ({ position }: { position: any }) => {
  return (
    <motion.li
      animate={position}
      className="nav-motion-cursor"
      style={{
        top: "4px",
        height: "calc(100% - 8px)",
      }}
    />
  );
};
