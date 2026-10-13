import { existsSync } from "node:fs";
import { spawn } from "node:child_process";
import { join } from "node:path";

const isWindows = process.platform === "win32";
const apiDirectory = "apps/api";
const pythonExecutable = isWindows ? join(".venv", "Scripts", "python.exe") : ".venv/bin/python";
const pythonPath = join(apiDirectory, pythonExecutable);

if (!existsSync(pythonPath)) {
  console.error("API virtual environment is missing. Complete the API setup in README.md first.");
  process.exit(1);
}

const child = spawn(pythonExecutable, ["-m", "pytest", "tests"], {
  cwd: apiDirectory,
  shell: isWindows,
  stdio: "inherit",
});

child.on("exit", (code) => process.exit(code ?? 1));
