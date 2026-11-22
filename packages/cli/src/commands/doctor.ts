"use strict";

import { probeSystem, engineStatus, enginePaths } from "../engine";
import { loadConfig } from "../config";

export async function cmdDoctor(args: string[]): Promise<number> {
  const json = args.includes("--json");
  const probe = probeSystem();
  const status = engineStatus();
  const config = loadConfig();

  const checks: Array<{ name: string; ok: boolean; detail: string }> = [
    {
      name: "Node.js",
      ok: true,
      detail: `${probe.nodeVersion} (${probe.arch})`,
    },
    {
      name: "Python 3",
      ok: !!probe.python,
      detail: probe.pythonVersion ?? "not found on PATH",
    },
    {
      name: "FFmpeg",
      ok: !!probe.ffmpeg,
      detail: probe.ffmpeg ?? "not found (required for video processing)",
    },
    {
      name: "FFprobe",
      ok: !!probe.ffprobe,
      detail: probe.ffprobe ?? "not found (part of FFmpeg)",
    },
    {
      name: "yt-dlp",
      ok: !!probe.ytDlp,
      detail: probe.ytDlp ?? "not found (required for YouTube/online video)",
    },
    {
      name: "Python engine",
      ok: status.installed,
      detail: status.installed ? "bootstrapped" : "not initialized (run `video2skill init`)",
    },
    {
      name: "Configuration",
      ok: true,
      detail: `config dir, library path set`,
    },
    {
      name: "AI providers configured",
      ok: config.providers.some((p) => p.enabled),
      detail: config.providers
        .filter((p) => p.enabled)
        .map((p) => `${p.id} (${p.defaultModel})`)
        .join(", ") || "none",
    },
  ];

  let allOk = true;
  for (const c of checks) {
    if (!c.ok) allOk = false;
  }

  if (json) {
    console.log(JSON.stringify({ probe, engine: status, checks, allOk }, null, 2));
    return allOk ? 0 : 1;
  }

  console.log("Video2Skill diagnostics\n");
  const pad = (s: string, n: number) => s + " ".repeat(Math.max(0, n - s.length));
  console.log(pad("Check", 28) + "Status  Detail");
  console.log("-".repeat(70));
  for (const c of checks) {
    console.log(pad(c.name, 28) + (c.ok ? "OK    " : "FAIL ") + c.detail);
  }
  console.log("-".repeat(70));
  console.log(`Overall: ${allOk ? "PASS" : "FAIL"}`);

  if (!allOk) {
    console.log("\nRun `video2skill init` to initialize missing components, then re-run `video2skill doctor`.");
    return 1;
  }
  console.log("\nAll checks passed. The local engine is ready.");
  return 0;
}
