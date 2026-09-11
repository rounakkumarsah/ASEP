import { Metadata } from "next";
import PlaygroundClient from "./PlaygroundClient";

export const metadata: Metadata = {
  title: "AI Engineering Workspace | ASEP",
  description: "Advanced AI engineering environment for testing models, running agents, and exploring code.",
};

export default function PlaygroundPage() {
  return <PlaygroundClient />;
}
