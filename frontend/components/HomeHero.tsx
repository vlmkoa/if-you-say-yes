 "use client";

 import * as React from "react";

 export function HomeHero() {
   const [offset, setOffset] = React.useState(0);

   React.useEffect(() => {
     const handleScroll = () => {
       const y = window.scrollY || 0;
       setOffset(Math.min(y * 0.08, 40));
     };
     handleScroll();
     window.addEventListener("scroll", handleScroll, { passive: true });
     return () => window.removeEventListener("scroll", handleScroll);
   }, []);

   return (
     <section className="app-shell py-12 sm:py-16 md:py-24">
       <div
         className="relative flex flex-col items-center text-center"
         style={{
           transform: `translateY(${offset * -0.4}px)`,
           transition: "transform 80ms linear",
         }}
       >
         <div className="pointer-events-none absolute -top-10 left-1/2 h-24 w-24 -translate-x-1/2 -rotate-6 rounded-full bg-gradient-to-tr from-rose-300/50 via-amber-200/60 to-yellow-100/80 blur-2xl" />
         <h1 className="relative text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl md:text-6xl drop-shadow-[0_12px_40px_rgba(15,23,42,0.35)]">
           If you say &quot;Yes&quot;
         </h1>
         <p className="mt-4 max-w-2xl text-sm sm:text-base leading-7 text-slate-800">
           Most of us are told to say no to drugs. This space is for the people who already said yes — to understand
           what they&apos;re taking, how substances can collide, and how to avoid overdose, misuse, or addiction.
         </p>
       </div>
     </section>
   );
 }

