"use strict";

import * as fs from "fs";
import * as path from "path";
import { execFileSync } from "child_process";
import { enginePaths, engineInstalled } from "../engine";
import { loadConfig, libraryPath } from "../config";

export async function cmdLearn(args: string[]): Promise<number> {
  const source = args[0];
  if (!source) {
    console.error("Usage: video2skill learn <VIDEO_URL | FILE>");
    console.log("Examples:");
    console.log("  video2skill learn https://youtube.com/watch?v=...");
    console.log("  video2skill learn ./tutorial.mp4");
    return 1;
  }

  const config = loadConfig();
  if (!config.providers.some((p) => p.enabled)) {
    console.error("No AI provider is configured. Run `video2skill init` and configure a provider first.");
    return 1;
  }

  if (!engineInstalled()) {
    console.error("Python engine not initialized. Run `video2skill init` first.");
    return 1;
  }

  const { python } = enginePaths();
  const entry = path.join(__dirname, "..", "..", "..", "engine", "bootstrap.py");
  const absEntry = path.resolve(entry);

  if (!fs.existsSync(absEntry)) {
    console.error("Python engine entry point not found. Re-run `video2skill init`.");
    return 1;
  }

  console.log("Video2Skill - learn");
  console.log(`Source: ${source}`);
  console.log(`Library: ${libraryPath(config)}`);

  try {
    execFileSync(python, [absEntry, "discover", source], {
      stdio: "inherit",
      encoding: "utf8",
      timeout: 600000,
    });
  } catch (err: any) {
    console.error(`Discovery failed: ${err?.message ?? String(err)}`);
    return 1;
  }

  console.log("\nDiscovery phase complete. Run `video2skill doctor` to confirm readiness, then proceed with skill generation.");
  return 0;
}
