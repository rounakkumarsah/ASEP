"use client";
import * as React from "react";
import { GovernancePolicy } from "@/lib/api/types";
import { FileWarning } from "lucide-react";
import { RiskBadge } from "./risk-badge";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

export function PolicyTable({ policies }: { policies: GovernancePolicy[] }) {
  return (
    <div className="w-full overflow-hidden rounded-xl border border-[#202833] bg-[#0D1117] shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-[#9CA6B5]">
          <thead className="border-b border-[#202833] bg-[#111720]/80 font-mono text-xs uppercase tracking-wider text-[#F5F7FA]">
            <tr>
              <th className="px-6 py-4 font-medium">Policy Name</th>
              <th className="px-6 py-4 font-medium">Description</th>
              <th className="px-6 py-4 font-medium text-center">Risk Threshold</th>
              <th className="px-6 py-4 font-medium text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#202833]">
            {policies.map((policy, i) => (
              <motion.tr
                key={policy.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: i * 0.05 }}
                className="group hover:bg-[#111720]/50 transition-colors"
              >
                <td className="whitespace-nowrap px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-md bg-[#22D3EE]/10 p-1.5 border border-[#22D3EE]/20 text-[#22D3EE] group-hover:bg-[#22D3EE]/20 transition-colors">
                      <FileWarning className="h-4 w-4" />
                    </div>
                    <span className="font-semibold text-[#F5F7FA]">{policy.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-xs font-sans max-w-sm truncate">
                  {policy.description}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-center">
                  <RiskBadge level={policy.riskThreshold} />
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right">
                  <button
                    type="button"
                    role="switch"
                    aria-checked={policy.isActive}
                    className={cn(
                      "peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none",
                      policy.isActive ? "bg-[#2DD4A3]" : "bg-[#202833]"
                    )}
                  >
                    <span
                      className={cn(
                        "pointer-events-none block h-4 w-4 rounded-full bg-[#090B0F] shadow-lg ring-0 transition-transform",
                        policy.isActive ? "translate-x-4" : "translate-x-0"
                      )}
                    />
                  </button>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
