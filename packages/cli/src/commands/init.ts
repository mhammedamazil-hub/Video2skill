"use strict";

import * as fs from "fs";
import * as path from "path";
import { bootstrapEngine, engineStatus, probeSystem } from "../engine";
import { ensureDefaultConfig, configDir, libraryPath, loadConfig, saveConfig } from "../config";

export async function cmdInit(args: string[]): Promise<number> {
  const force = args.includes("--force") || args.includes("-f");
  const yes = args.includes("--yes") || args.includes("-y");

  console.log("Video2Skill - initializing local engine");
  console.log(`Config directory: ${configDir()}`);

  const probe = probeSystem();
  console.log(`Platform: ${probe.platform} ${probe.arch}`);
  console.log(`Node: ${probe.nodeVersion}`);
  console.log(`Python: ${probe.python ?? "not found"}`);
  console.log(`FFmpeg: ${probe.ffmpeg ?? "not found"}`);
  console.log(`yt-dlp: ${probe.ytDlp ?? "not found"}`);

  const status = engineStatus();
  if (status.installed && !force) {
    console.log("Python engine already initialized.");
  } else {
    const result = bootstrapEngine();
    if (!result.ok) {
      console.error(`Error: ${result.message}`);
      return 1;
    }
    console.log(result.message);
  }

  const config = ensureDefaultConfig();
  const lib = libraryPath(config);
  fs.mkdirSync(lib, { recursive: true });
  console.log(`Skill library: ${lib}`);

  // Print provider setup hints.
  const configured = config.providers.filter((p) => p.enabled);
  if (configured.length === 0) {
    console.log("\nNo AI providers configured yet.");
    console.log("Configure one with: video2skill config provider <id> --api-key-env <VAR>");
    console.log("At least one provider is required before `learn` can run.");
  } else {
    console.log(`\nConfigured providers: ${configured.map((p) => p.id).join(", ")}`);
    console.log(`Default provider: ${config.defaultProvider ?? "none"}`);
  }

  const missing: string[] = [];
  if (!probe.ffmpeg) missing.push("ffmpeg");
  if (!probe.ytDlp) missing.push("yt-dlp");
  if (missing.length > 0) {
    console.log(`\nOptional tools not found: ${missing.join(", ")}`);
    console.log("Install them for full video ingestion support, then run `video2skill doctor`.");
  }

  console.log("\nInitialization complete. Next: `video2skill doctor` to verify, then `video2skill learn <video>`.");
  return 0;
}
