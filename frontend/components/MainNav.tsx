 "use client";

 import Link from "next/link";
 import { usePathname } from "next/navigation";

 const links = [
   { href: "/dashboard", label: "Dashboard" },
   { href: "/", label: "Home" },
   { href: "/reagent", label: "Reagent test" },
 ];

 export function MainNav() {
   const pathname = usePathname() || "/";

   return (
     <nav className="flex items-center justify-center gap-4 text-sm">
       {links.map((link) => {
         const isActive =
           link.href === "/"
             ? pathname === "/"
             : pathname === link.href || pathname.startsWith(link.href + "/");
         const baseClasses =
           "px-3 py-1.5 sm:px-4 text-xs sm:text-sm font-medium transition-colors";

         const activeClasses =
           "text-amber-50 underline underline-offset-4 decoration-2";
         const inactiveClasses =
           "text-slate-200 hover:text-amber-100";

         return (
           <Link
             key={link.href}
             href={link.href}
             className={`${baseClasses} ${isActive ? activeClasses : inactiveClasses}`}
           >
             {link.label}
           </Link>
         );
       })}
     </nav>
   );
 }


