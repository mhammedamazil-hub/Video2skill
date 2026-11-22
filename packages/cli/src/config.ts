"use strict";

import * as fs from "fs";
import * as path from "path";
import * as os from "os";

export interface Video2SkillConfig {
  version: number;
  providers: ProviderConfig[];
  defaultProvider: string | null;
  sandbox: SandboxConfig;
  library: LibraryConfig;
  perception: PerceptionConfig;
  updatedAt: string;
}

export interface ProviderConfig {
  id: string;
  name: string;
  type: "anthropic" | "openai" | "google" | "openai-compatible" | "local";
  apiKeyEnv: string;
  baseUrl: string | null;
  defaultModel: string;
  enabled: boolean;
}

export interface SandboxConfig {
  enabled: boolean;
  driver: "none" | "bubblewrap" | "seatbelt" | "appcontainer" | "lpac";
  timeoutMs: number;
  maxMemoryMb: number;
  network: boolean;
}

export interface LibraryConfig {
  path: string;
}

export interface PerceptionConfig {
  whisperModel: string;
  keyframeIntervalSec: number;
  adaptiveSampling: boolean;
}

export const DEFAULT_CONFIG: Video2SkillConfig = {
  version: 1,
  providers: [
    {
      id: "anthropic",
      name: "Anthropic",
      type: "anthropic",
      apiKeyEnv: "ANTHROPIC_API_KEY",
      baseUrl: null,
      defaultModel: "claude-3-5-sonnet-20241022",
      enabled: false,
    },
    {
      id: "openai",
      name: "OpenAI",
      type: "openai",
      apiKeyEnv: "OPENAI_API_KEY",
      baseUrl: null,
      defaultModel: "gpt-4o",
      enabled: false,
    },
    {
      id: "google",
      name: "Google Gemini",
      type: "google",
      apiKeyEnv: "GEMINI_API_KEY",
      baseUrl: null,
      defaultModel: "gemini-1.5-pro",
      enabled: false,
    },
    {
      id: "openai-compatible",
      name: "OpenAI-compatible",
      type: "openai-compatible",
      apiKeyEnv: "OPENAI_COMPATIBLE_API_KEY",
      baseUrl: null,
      defaultModel: "local-model",
      enabled: false,
    },
    {
      id: "local",
      name: "Local inference server",
      type: "local",
      apiKeyEnv: "",
      baseUrl: "http://localhost:11434",
      defaultModel: "llama3.1",
      enabled: false,
    },
  ],
  defaultProvider: null,
  sandbox: {
    enabled: true,
    driver: "none",
    timeoutMs: 300000,
    maxMemoryMb: 2048,
    network: false,
  },
  library: {
    path: "",
  },
  perception: {
    whisperModel: "base",
    keyframeIntervalSec: 5,
    adaptiveSampling: true,
  },
  updatedAt: new Date().toISOString(),
};

export function configDir(): string {
  return process.env.VIDEO2SKILL_CONFIG_DIR ?? path.join(os.homedir(), ".video2skill");
}

export function configPath(): string {
  return path.join(configDir(), "config.json");
}

export function libraryPath(config: Video2SkillConfig): string {
  return config.library.path || path.join(configDir(), "library");
}

export function loadConfig(): Video2SkillConfig {
  try {
    const raw = fs.readFileSync(configPath(), "utf8");
    const parsed = JSON.parse(raw) as Partial<Video2SkillConfig>;
    return {
      ...DEFAULT_CONFIG,
      ...parsed,
      providers: parsed.providers ?? DEFAULT_CONFIG.providers,
      updatedAt: parsed.updatedAt ?? DEFAULT_CONFIG.updatedAt,
    };
  } catch {
    return { ...DEFAULT_CONFIG };
  }
}

export function saveConfig(config: Video2SkillConfig): void {
  const dir = configDir();
  fs.mkdirSync(dir, { recursive: true });
  const out = { ...config, updatedAt: new Date().toISOString() };
  fs.writeFileSync(configPath(), JSON.stringify(out, null, 2) + "\n", "utf8");
}

export function ensureDefaultConfig(): Video2SkillConfig {
  const existing = loadConfig();
  const cfg = {
    ...existing,
    library: { ...existing.library, path: libraryPath(existing) },
    updatedAt: existing.updatedAt ?? DEFAULT_CONFIG.updatedAt,
  };
  saveConfig(cfg);
  fs.mkdirSync(cfg.library.path, { recursive: true });
  return cfg;
}
