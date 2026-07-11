"use client";

import React, { useEffect, useState } from "react";
import { ReactLenis } from "lenis/react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

export default function SmoothScrollProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [lenisInstance, setLenisInstance] = useState<any>(null);

  useEffect(() => {
    if (!lenisInstance) return;

    // Register ScrollTrigger plugin
    gsap.registerPlugin(ScrollTrigger);

    // Update ScrollTrigger on Lenis scroll
    lenisInstance.on("scroll", ScrollTrigger.update);

    // Integrate Lenis RAF with GSAP ticker loop
    const updateRaf = (time: number) => {
      lenisInstance.raf(time * 1000);
    };
    
    gsap.ticker.add(updateRaf);
    gsap.ticker.lagSmoothing(0);

    return () => {
      lenisInstance.off("scroll", ScrollTrigger.update);
      gsap.ticker.remove(updateRaf);
      ScrollTrigger.killAll();
    };
  }, [lenisInstance]);

  return (
    <ReactLenis
      ref={(ref) => {
        if (ref) {
          setLenisInstance(ref.lenis);
        }
      }}
      root
      autoRaf={false}
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
