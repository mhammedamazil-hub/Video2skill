#!/usr/bin/env node
"use strict";

import { probeSystem } from "./engine";
import { loadConfig, ensureDefaultConfig, configDir, libraryPath } from "./config";
import { cmdInit } from "./commands/init";
import { cmdDoctor } from "./commands/doctor";
import { cmdLearn } from "./commands/learn";
import { cmdTest } from "./commands/test";
import { cmdEvolve } from "./commands/evolve";
import { cmdList } from "./commands/list";
import { cmdInspect } from "./commands/inspect";
import { cmdUpdate } from "./commands/update";
import { cmdConfig } from "./commands/config";

const COMMANDS: Record<string, (args: string[]) => Promise<number>> = {
  init: cmdInit,
  learn: cmdLearn,
  test: cmdTest,
  evolve: cmdEvolve,
  list: cmdList,
  inspect: cmdInspect,
  doctor: cmdDoctor,
  update: cmdUpdate,
  config: cmdConfig,
  help: cmdHelp,
  "--help": cmdHelp,
  "-h": cmdHelp,
};

function printHelp(): void {
  console.log(`
Video2Skill - Autonomous multimodal skill acquisition, learning, testing & evolution engine

Usage: video2skill <command> [options]

Commands:
  init                          Initialize the local engine and configuration
  learn <VIDEO_URL | FILE>      Acquire a skill from a video demonstration
  test <skill-name>             Run the examination suite for a skill
  evolve <skill-name>           Improve an existing skill from failure evidence
  list                          List skills in the local library
  inspect <skill-name>          Show skill details and evaluation history
  doctor                        Run diagnostics on the environment
  update                        Update engine components
  config                        Show/manage configuration (show | provider <id> [options])
  help                          Show this help

Environment:
  VIDEO2SKILL_CONFIG_DIR        Override the configuration directory
                              (default: ~/.video2skill)

Examples:
  video2skill init
  video2skill learn https://youtube.com/watch?v=...
  video2skill learn ./tutorial.mp4
  video2skill test blender-basics
  video2skill doctor
`);
}

async function cmdHelp(): Promise<number> {
  printHelp();
  return 0;
}

async function main(): Promise<number> {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    printHelp();
    return 0;
  }

  const [name, ...rest] = args;
  const fn = COMMANDS[name.toLowerCase()];
  if (!fn) {
    console.error(`Unknown command: ${name}`);
    console.error("Run 'video2skill help' for usage.");
    return 1;
  }

  try {
    return await fn(rest);
  } catch (err: any) {
    console.error(`video2skill: ${err?.message ?? String(err)}`);
    return 1;
  }
}

main().then((code) => process.exit(code));
