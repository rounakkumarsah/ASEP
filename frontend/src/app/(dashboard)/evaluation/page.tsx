"use client";

import * as React from "react";
import { apiClient } from "@/lib/api/client";
import { 
  Play, 
  Loader2, 
  AlertTriangle,
  History,
  Award
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

interface EvaluationDataset {
  name: string;
  description: string;
  total_cases: number;
  tags?: string[];
}

interface EvaluationHistory {
  dataset_name: string;
  total_cases: number;
  passed: number;
  pass_rate: number;
  avg_overall_score: number;
  generated_at: string;
}

export default function EvaluationPage() {
  const [datasets, setDatasets] = React.useState<EvaluationDataset[]>([]);
  const [history, setHistory] = React.useState<EvaluationHistory[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const [running, setRunning] = React.useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const [dsRes, histRes] = await Promise.all([
        apiClient.get("/api/v1/evaluations"),
        apiClient.get("/api/v1/evaluations/history")
      ]);
      setDatasets(dsRes.data || []);
      setHistory(histRes.data || []);
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to load evaluation datasets.");
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchData();
  }, []);

  const handleRun = async (datasetName: string) => {
    setRunning(datasetName);
    setError("");
    try {
      await apiClient.post("/api/v1/evaluations/run", {
        dataset_name: datasetName
      });
      // Refresh history
      const histRes = await apiClient.get("/api/v1/evaluations/history");
      setHistory(histRes.data || []);
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to execute evaluation dataset.");
    } finally {
      setRunning(null);
    }
  };

  if (loading) {
    return (
      <div className="h-[400px] w-full flex flex-col items-center justify-center text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p>Discovering evaluation datasets...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Evaluations & Benchmarks</h1>
        <p className="text-muted-foreground mt-1">
          Verify agent accuracy, latency parameters, and compute run costs against assertion test suites.
        </p>
      </div>

      {error && (
        <div className="p-4 border border-destructive/20 bg-destructive/10 text-destructive text-sm rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Grid of registered datasets */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Award className="h-5 w-5 text-primary" />
          <span>Registered Evaluation Suites ({datasets.length})</span>
        </h2>

        {datasets.length === 0 ? (
          <Card className="border-dashed p-10 text-center flex flex-col items-center justify-center bg-card/10">
            <Award className="h-10 w-10 text-primary mb-3" />
            <CardTitle className="text-lg font-bold text-foreground">Create First Benchmark</CardTitle>
            <CardDescription className="max-w-md mx-auto mt-2 mb-6">
              Establish validation benchmarks to assert model output accuracies, latency limits, and agent execution paths. Create your first evaluation suite to start tracking metrics.
            </CardDescription>
            <Button className="font-semibold" onClick={() => alert("To register custom benchmarks, add EvaluationDataset schemas to backend src/evaluation/registry.py or upload a validation JSON suite.")}>
              Register Evaluation Suite
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {datasets.map(ds => (
              <Card key={ds.name} className="border-border/40 bg-card/30">
                <CardHeader>
                  <CardTitle className="text-lg font-bold text-foreground">{ds.name}</CardTitle>
                  <CardDescription className="pt-1">{ds.description || "No description provided."}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 pt-0">
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <span>Test Cases: <span className="font-bold text-foreground">{ds.total_cases}</span></span>
                    <Button
                      size="sm"
                      onClick={() => handleRun(ds.name)}
                      disabled={running === ds.name}
                      className="gap-1.5 font-semibold"
                    >
                      {running === ds.name ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          <span>Running...</span>
                        </>
                      ) : (
                        <>
                          <Play className="h-3.5 w-3.5 fill-current" />
                          <span>Run Suite</span>
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* History table */}
      <div className="space-y-4 pt-6">
        <h2 className="text-xl font-bold flex items-center gap-2 text-muted-foreground">
          <History className="h-5 w-5" />
          <span>Evaluation History ({history.length})</span>
        </h2>

        {history.length === 0 ? (
          <Card className="border border-dashed p-10 text-center text-muted-foreground">
            <CardTitle className="text-base font-bold">No history available</CardTitle>
            <CardDescription className="mt-1">
              Select an evaluation suite above and launch it to review metrics history logs.
            </CardDescription>
          </Card>
        ) : (
          <div className="border border-border/30 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/40 border-b border-border/30">
                  <th className="text-left p-3 font-semibold text-xs text-muted-foreground">Dataset</th>
                  <th className="text-left p-3 font-semibold text-xs text-muted-foreground">Total / Passed</th>
                  <th className="text-left p-3 font-semibold text-xs text-muted-foreground">Pass Rate</th>
                  <th className="text-left p-3 font-semibold text-xs text-muted-foreground">Average Score</th>
                  <th className="text-right p-3 font-semibold text-xs text-muted-foreground">Date</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h, i) => (
                  <tr key={i} className="border-b border-border/20 last:border-0">
                    <td className="p-3 font-medium">{h.dataset_name}</td>
                    <td className="p-3 text-xs text-muted-foreground">
                      {h.passed} / {h.total_cases}
                    </td>
                    <td className="p-3 text-xs font-semibold">
                      <span className={`px-2 py-0.5 rounded ${
                        h.pass_rate >= 0.8 ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
                      }`}>
                        {(h.pass_rate * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="p-3 text-xs font-mono">{h.avg_overall_score.toFixed(2)}</td>
                    <td className="p-3 text-right text-xs text-muted-foreground">
                      {new Date(h.generated_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
