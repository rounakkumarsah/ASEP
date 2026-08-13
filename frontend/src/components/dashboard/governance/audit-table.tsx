"use client";
import * as React from "react";
import { AuditRecord } from "@/lib/api/types";
import { CheckCircle2, XCircle, ShieldBan, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

export function AuditTable({ audits }: { audits: AuditRecord[] }) {
  return (
    <div className="w-full overflow-hidden rounded-xl border border-[#202833] bg-[#0D1117] shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-[#9CA6B5]">
          <thead className="border-b border-[#202833] bg-[#111720]/80 font-mono text-xs uppercase tracking-wider text-[#F5F7FA]">
            <tr>
              <th className="px-6 py-4 font-medium">Action</th>
              <th className="px-6 py-4 font-medium">Actor</th>
              <th className="px-6 py-4 font-medium">Target</th>
              <th className="px-6 py-4 font-medium text-right">Status</th>
              <th className="px-6 py-4 font-medium text-right">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#202833]">
            {audits.map((audit, i) => {
              const timestamp = new Date(audit.timestamp).toLocaleString(undefined, {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              });

              let statusIcon = <CheckCircle2 className="w-4 h-4 text-[#2DD4A3]" />;
              let statusText = "Success";
              let statusBg = "bg-[#2DD4A3]/10 text-[#2DD4A3] border-[#2DD4A3]/20";

              if (audit.status === "failure") {
                statusIcon = <XCircle className="w-4 h-4 text-[#F05252]" />;
                statusText = "Failed";
                statusBg = "bg-[#F05252]/10 text-[#F05252] border-[#F05252]/20";
              } else if (audit.status === "blocked") {
                statusIcon = <ShieldBan className="w-4 h-4 text-[#FF8A4C]" />;
                statusText = "Blocked";
                statusBg = "bg-[#FF8A4C]/10 text-[#FF8A4C] border-[#FF8A4C]/20";
              }

              return (
                <motion.tr
                  key={audit.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2, delay: i * 0.05 }}
                  className="group hover:bg-[#111720]/50 transition-colors"
                >
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="rounded-md bg-[#22D3EE]/10 p-1.5 border border-[#22D3EE]/20 text-[#22D3EE] group-hover:bg-[#22D3EE]/20 transition-colors">
                        <Terminal className="h-4 w-4" />
                      </div>
                      <span className="font-semibold text-[#F5F7FA]">{audit.action}</span>
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 font-mono text-xs">
                    {audit.actor}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 font-mono text-xs text-[#22D3EE]">
                    {audit.target}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right">
                    <div className="flex justify-end">
                      <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium font-mono uppercase tracking-widest", statusBg)}>
                        {statusIcon}
                        {statusText}
                      </span>
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right tabular-nums font-mono text-xs">
                    {timestamp}
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
