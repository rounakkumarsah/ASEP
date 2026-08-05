import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Cpu } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center space-y-6 bg-[#090B0F] px-4 text-center text-[#F5F7FA]">
      <div className="flex items-center space-x-2 mb-2">
        <div className="p-2 rounded-md bg-[#111720] border border-[#202833] text-[#22D3EE]">
          <Cpu className="h-8 w-8" />
        </div>
        <span className="text-2xl font-mono font-bold tracking-wider">ASEP</span>
      </div>
      <div className="space-y-2 max-w-md font-mono">
        <h1 className="text-4xl font-extrabold tracking-tight text-[#F5F7FA]">
          404 — Route Not Found
        </h1>
        <p className="text-xs text-[#9CA6B5] leading-relaxed">
          The requested control plane endpoint does not exist or has been relocated.
        </p>
      </div>
      <Link href="/">
        <Button className="font-mono text-xs font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] h-10 px-6">
          Return to Overview
        </Button>
      </Link>
    </div>
  );
}
