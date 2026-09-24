import { motion } from "framer-motion";
import type { ReactNode } from "react";

const variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

/** Wraps a routed page so navigating between pages fades/slides instead of
 * hard-cutting (see App.tsx's AnimatePresence around <Routes>). Purely a
 * presentational shell -- it doesn't touch what any page renders or fetches. */
export function PageTransition({ children }: { children: ReactNode }) {
  return (
    <motion.div variants={variants} initial="initial" animate="animate" exit="exit" transition={{ duration: 0.22, ease: "easeInOut" }}>
      {children}
    </motion.div>
  );
}
