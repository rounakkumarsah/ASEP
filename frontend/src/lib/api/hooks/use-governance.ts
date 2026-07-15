import { useQuery } from "@tanstack/react-query";
import { governanceService } from "../services/governance";

export const governanceKeys = {
  all: ["governance"] as const,
  approvals: () => [...governanceKeys.all, "approvals"] as const,
  policies: () => [...governanceKeys.all, "policies"] as const,
  audits: () => [...governanceKeys.all, "audits"] as const,
};

export function useApprovals() {
  return useQuery({
    queryKey: governanceKeys.approvals(),
    queryFn: async () => {
      const response = await governanceService.getApprovals();
      return response.data;
    },
  });
}

export function usePolicies() {
  return useQuery({
    queryKey: governanceKeys.policies(),
    queryFn: async () => {
      const response = await governanceService.getPolicies();
      return response.data;
    },
  });
}

export function useAudits() {
  return useQuery({
    queryKey: governanceKeys.audits(),
    queryFn: async () => {
      const response = await governanceService.getAudits();
      return response.data;
    },
  });
}
