"use strict";

import * as fs from "fs";
import { loadConfig, saveConfig, configDir } from "../config";

function parseArgs(args: string[]): { [key: string]: string } {
  const opts: { [key: string]: string } = {};
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a.startsWith("--") && a.includes("=")) {
      const [k, v] = a.slice(2).split("=");
      opts[k] = v;
    } else if (a.startsWith("--") && i + 1 < args.length && !args[i + 1].startsWith("-")) {
      opts[a.slice(2)] = args[++i];
    } else if (a.startsWith("--")) {
      // Boolean flag (e.g. --set-default, --enable) with no value => "true".
      opts[a.slice(2)] = "true";
    }
  }
  return opts;
}

export async function cmdConfig(args: string[]): Promise<number> {
  const sub = args[0];
  const rest = args.slice(1);

  if (!sub || sub === "show") {
    const config = loadConfig();
    console.log(`Config directory: ${configDir()}`);
    console.log(JSON.stringify(config, null, 2));
    return 0;
  }

  if (sub === "provider") {
    // usage: config provider <id> [--api-key-env <VAR>] [--default-model <model>] [--base-url <url>] [--enable|--disable] [--set-default]
    const id = rest[0];
    if (!id) {
      console.error("Usage: video2skill config provider <id> [options]");
      return 1;
    }
    const opts = parseArgs(rest.slice(1));
    const config = loadConfig();
    const provider = config.providers.find((p) => p.id === id);
    if (!provider) {
      console.error(`Unknown provider: ${id}`);
      console.log(`Available: ${config.providers.map((p) => p.id).join(", ")}`);
      return 1;
    }
    if (opts["api-key-env"]) provider.apiKeyEnv = opts["api-key-env"];
    if (opts["base-url"]) provider.baseUrl = opts["base-url"];
    if (opts["default-model"]) provider.defaultModel = opts["default-model"];
    if (opts["enable"] !== undefined) provider.enabled = opts["enable"] !== "false";
    if (opts["disable"]) provider.enabled = false;
    if (opts["set-default"] !== undefined) {
      config.defaultProvider = opts["set-default"] !== "false" ? id : null;
    }
    provider.enabled = true; // configuring a provider enables it
    saveConfig(config);
    console.log(`Provider '${id}' updated.`);
    console.log(`  enabled: ${provider.enabled}`);
    console.log(`  default model: ${provider.defaultModel}`);
    console.log(`  API key env: ${provider.apiKeyEnv || "(none)"}`);
    console.log(`  base URL: ${provider.baseUrl || "(default)"}`);
    console.log(`  default provider: ${config.defaultProvider}`);
    console.log("\nSet the actual API key in your shell, e.g.:");
    console.log(`  export ${provider.apiKeyEnv || "LOCAL_MODEL_BASE_URL"}=...`);
    return 0;
  }

  console.error(`Unknown config subcommand: ${sub}`);
  console.log("Available: show, provider");
  return 1;
}
