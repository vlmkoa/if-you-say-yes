 "use client";

 import * as React from "react";

 type Props = { children: React.ReactNode };

 const STORAGE_KEY = "ify-disclaimer-ack";

 export function DisclaimerGate({ children }: Props) {
   const [open, setOpen] = React.useState(false);
   const [ready, setReady] = React.useState(false);

   React.useEffect(() => {
     try {
       if (typeof window === "undefined") return;
       const stored = window.localStorage.getItem(STORAGE_KEY);
       if (!stored) {
         setOpen(true);
       }
     } catch {
       // ignore storage errors; still show page
     } finally {
       setReady(true);
     }
   }, []);

   function handleAccept() {
     try {
       window.localStorage.setItem(STORAGE_KEY, "1");
     } catch {
       // ignore storage errors
     }
     setOpen(false);
   }

   return (
     <>
       {children}
       {ready && open && (
         <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/70 backdrop-blur-sm">
           <div className="mx-4 max-w-md rounded-2xl border border-white/10 bg-slate-950/95 p-6 shadow-2xl">
             <h2 className="text-lg font-semibold text-white">
               Harm reduction disclaimer
             </h2>
             <p className="mt-3 text-sm leading-6 text-slate-300">
               This project does <span className="font-semibold text-rose-200">not</span> encourage or endorse the use of drugs.
               It exists solely for harm reduction and education — to help people understand interactions and avoid overdose,
               misuse, or addiction.
             </p>
             <p className="mt-3 text-xs text-slate-400">
               Information here is not medical advice and does not replace a conversation with a qualified clinician or local
               harm reduction service.
             </p>
             <button
               type="button"
               onClick={handleAccept}
               className="mt-5 inline-flex w-full items-center justify-center rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
             >
               I understand and want to continue
             </button>
           </div>
         </div>
       )}
     </>
   );
 }

