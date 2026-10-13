import { existsSync } from "node:fs";
import { spawn } from "node:child_process";
import { join } from "node:path";

const isWindows = process.platform === "win32";
const apiDirectory = "apps/api";
const webDirectory = "apps/web";
const apiExecutable = isWindows ? ".venv/Scripts/uvicorn.exe" : ".venv/bin/uvicorn";
const apiPath = join(apiDirectory, apiExecutable);
const apiOnly = process.argv.includes("--api-only");
const processes = [];

if (!existsSync(apiPath)) {
  console.error("API virtual environment is missing. Complete the API setup in README.md first.");
  process.exit(1);
}

function start(command, args, cwd) {
  const child = spawn(command, args, {
    cwd,
    shell: isWindows,
    stdio: "inherit",
  });
  processes.push(child);
  child.on("exit", (code) => {
    if (code && code !== 0) process.exitCode = code;
    stop();
  });
}

function stop() {
  for (const child of processes) {
    if (!child.killed) child.kill();
  }
}

process.on("SIGINT", stop);
process.on("SIGTERM", stop);

start(apiExecutable, ["app.main:app", "--reload"], apiDirectory);
if (!apiOnly) start(isWindows ? "npm.cmd" : "npm", ["run", "dev"], webDirectory);
