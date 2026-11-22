"use strict";

import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import assert from "node:assert/strict";
import {
  configDir,
  configPath,
  loadConfig,
  saveConfig,
  ensureDefaultConfig,
  libraryPath,
  DEFAULT_CONFIG,
} from "./config";

const TMP_DIR = path.join(os.tmpdir(), "v2s-config-test");

function withConfigDir(fn: () => void): void {
  const prev = process.env.VIDEO2SKILL_CONFIG_DIR;
  process.env.VIDEO2SKILL_CONFIG_DIR = TMP_DIR;
  try {
    fs.rmSync(TMP_DIR, { recursive: true, force: true });
    fn();
  } finally {
    if (prev === undefined) {
      delete process.env.VIDEO2SKILL_CONFIG_DIR;
    } else {
      process.env.VIDEO2SKILL_CONFIG_DIR = prev;
    }
  }
}

async function main(): Promise<void> {
  // 1. Defaults when no config exists.
  withConfigDir(() => {
    assert.equal(fs.existsSync(configPath()), false);
    const cfg = loadConfig();
    assert.equal(cfg.version, DEFAULT_CONFIG.version);
    assert.equal(cfg.defaultProvider, null);
    assert.equal(cfg.providers.length, DEFAULT_CONFIG.providers.length);
    assert.equal(cfg.providers.filter((p) => p.enabled).length, 0);
  });

  // 2. Save + load round trip.
  withConfigDir(() => {
    const cfg = ensureDefaultConfig();
    cfg.providers[0].enabled = true;
    cfg.defaultProvider = "anthropic";
    saveConfig(cfg);

    const loaded = loadConfig();
    assert.equal(loaded.providers[0].enabled, true);
    assert.equal(loaded.defaultProvider, "anthropic");
    assert.equal(libraryPath(loaded), path.join(TMP_DIR, "library"));
  });

  // 3. ensureDefaultConfig creates library path and is idempotent.
  withConfigDir(() => {
    const a = ensureDefaultConfig();
    const b = ensureDefaultConfig();
    assert.equal(a.library.path, path.join(TMP_DIR, "library"));
    assert.equal(b.library.path, a.library.path);
    assert.equal(fs.existsSync(path.join(TMP_DIR, "config.json")), true);
    assert.equal(fs.existsSync(a.library.path), true);
  });

  console.log("config.test.ts: OK");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
