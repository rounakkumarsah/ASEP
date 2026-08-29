import { useQuery } from "@tanstack/react-query";
import { controlPlaneService } from "../services/control-plane";

export const controlPlaneKeys = {
  all: ["controlPlane"] as const,
  overview: () => [...controlPlaneKeys.all, "overview"] as const,
};

export function useSystemOverview() {
  return useQuery({
    queryKey: controlPlaneKeys.overview(),
    queryFn: async () => {
      const response = await controlPlaneService.getSystemOverview();
      return response.data;
    },
    refetchInterval: 15000, // Efficient 15s refresh
    refetchOnWindowFocus: false,
  });
}
