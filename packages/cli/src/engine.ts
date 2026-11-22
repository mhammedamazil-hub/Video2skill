"use strict";

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { execFileSync } from "child_process";
import { configDir, loadConfig, saveConfig } from "./config";

export interface SystemProbe {
  node: string;
  nodeVersion: string;
  python: string | null;
  pythonVersion: string | null;
  ffmpeg: string | null;
  ffprobe: string | null;
  ytDlp: string | null;
  platform: string;
  arch: string;
}

export function probeSystem(): SystemProbe {
  const which = (cmd: string): string | null => {
    try {
      return execFileSync("which", [cmd], { encoding: "utf8", stdio: ["pipe", "pipe", "ignore"] }).trim() || null;
    } catch {
      return null;
    }
  };
  const version = (cmd: string, args: string[] = ["--version"]): string | null => {
    try {
      const out = execFileSync(cmd, args, { encoding: "utf8", stdio: ["pipe", "pipe", "ignore"] });
      return out.toString().trim().split("\n")[0] ?? null;
    } catch {
      return null;
    }
  };

  const python = which("python3") || which("python");
  const ffmpeg = which("ffmpeg");
  const ffprobe = which("ffprobe");
  const ytDlp = which("yt-dlp");

  const ffmpegVersion = ffmpeg ? version(ffmpeg, ["-version"]) : null;
  const ffprobeVersion = ffprobe ? version(ffprobe, ["-version"]) : null;

  return {
    node: process.version,
    nodeVersion: process.version,
    python: python ?? null,
    pythonVersion: python ? version(python, ["--version"]) : null,
    ffmpeg: ffmpegVersion ? ffmpegVersion.split("\n")[0] : null,
    ffprobe: ffprobeVersion ? ffprobeVersion.split("\n")[0] : null,
    ytDlp: ytDlp ?? null,
    platform: os.platform(),
    arch: os.arch(),
  };
}

export interface EnginePaths {
  root: string;
  python: string;
  venv: string;
  packages: string;
}

export function engineRoot(): string {
  return path.join(configDir(), "engine");
}

export function enginePaths(): EnginePaths {
  const root = engineRoot();
  return {
    root,
    python: path.join(root, ".venv", "bin", "python"),
    venv: path.join(root, ".venv"),
    packages: path.join(root, "packages"),
  };
}

export function engineInstalled(): boolean {
  const { python } = enginePaths();
  return fs.existsSync(python);
}

export function engineStatus(): { installed: boolean; python: string | null; probe: SystemProbe } {
  return {
    installed: engineInstalled(),
    python: engineInstalled() ? enginePaths().python : null,
    probe: probeSystem(),
  };
}

export function bootstrapEngine(): { ok: boolean; message: string; paths?: EnginePaths } {
  const probe = probeSystem();
  const paths = enginePaths();

  if (!probe.python) {
    return { ok: false, message: "Python 3 is required but was not found on PATH. Install Python 3.9+ and re-run `video2skill init`." };
  }

  try {
    fs.mkdirSync(paths.root, { recursive: true });
    fs.mkdirSync(paths.packages, { recursive: true });

    // Create a Python venv if it does not exist.
    if (!fs.existsSync(paths.python)) {
      execFileSync(probe.python, ["-m", "venv", paths.venv], {
        stdio: ["pipe", "pipe", "pipe"],
        encoding: "utf8",
        timeout: 180000,
      });
    }

    const pip = path.join(path.dirname(paths.python), "pip");
    // Install pinned engine dependencies (kept minimal; heavy perception deps are optional).
    execFileSync(pip, ["install", "--upgrade", "pip"], {
      stdio: ["pipe", "pipe", "pipe"],
      encoding: "utf8",
      timeout: 300000,
    });
    execFileSync(pip, ["install", "pyyaml", "requests"], {
      stdio: ["pipe", "pipe", "pipe"],
      encoding: "utf8",
      timeout: 300000,
    });

    const config = loadConfig();
    config.library.path = config.library.path || path.join(configDir(), "library");
    saveConfig(config);

    return { ok: true, message: "Python engine bootstrapped successfully.", paths };
  } catch (err: any) {
    return {
      ok: false,
      message: `Failed to bootstrap Python engine: ${err?.message ?? String(err)}`,
    };
  }
}
