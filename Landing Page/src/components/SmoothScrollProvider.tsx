"use client";

import React, { useEffect, useRef } from "react";
import { ReactLenis } from "lenis/react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

export default function SmoothScrollProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const lenisRef = useRef<any>(null);

  useEffect(() => {
    // Register ScrollTrigger plugin
    gsap.registerPlugin(ScrollTrigger);

    const lenis = lenisRef.current?.lenis;
    if (lenis) {
      // Update ScrollTrigger on Lenis scroll
      lenis.on("scroll", ScrollTrigger.update);

      // Integrate Lenis RAF with GSAP ticker loop
      const updateRaf = (time: number) => {
        lenis.raf(time * 1000);
      };
      
      gsap.ticker.add(updateRaf);
      gsap.ticker.lagSmoothing(0);

      return () => {
        lenis.off("scroll", ScrollTrigger.update);
        gsap.ticker.remove(updateRaf);
        ScrollTrigger.killAll();
      };
    }
  }, []);

  return (
    <ReactLenis
      ref={lenisRef}
      root
      options={{
        lerp: 0.1,
        duration: 1.2,
        smoothWheel: true,
      }}
    >
      {children}
    </ReactLenis>
  );
}
