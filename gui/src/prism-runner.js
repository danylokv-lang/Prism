const { execFile } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");

const CANDIDATE_PATHS = [
  "prism",
  `${os.homedir()}/.local/bin/prism`,
  "/usr/local/bin/prism",
  "/opt/homebrew/bin/prism",
];

function resolvePrismBinary() {
  for (const candidate of CANDIDATE_PATHS) {
    if (candidate === "prism" || fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return "prism";
}

function runPrism(args) {
  return new Promise((resolve) => {
    execFile(resolvePrismBinary(), args, { timeout: 60000, maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
      if (error) {
        resolve({ ok: false, error: stderr?.trim() || error.message });
        return;
      }
      try {
        resolve({ ok: true, data: JSON.parse(stdout) });
      } catch {
        resolve({ ok: false, error: "Couldn't parse prism output as JSON." });
      }
    });
  });
}

module.exports = { runPrism };
