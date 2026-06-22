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
  // Check known install locations first -- a GUI app launched from Finder/Dock
  // does not inherit the interactive shell's PATH, so the bare "prism" lookup
  // below would miss pipx's default ~/.local/bin install. Bare "prism" is only
  // a last resort in case PATH happens to include it (e.g. launched from a terminal).
  for (const candidate of CANDIDATE_PATHS) {
    if (candidate !== "prism" && fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return "prism";
}

function runPrism(args) {
  return new Promise((resolve) => {
    execFile(resolvePrismBinary(), args, { timeout: 60000, maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
      if (error) {
        resolve({ ok: false, error: stderr?.trim() || error.message, notFound: error.code === "ENOENT" });
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

function checkPrismAvailable() {
  return new Promise((resolve) => {
    execFile(resolvePrismBinary(), ["--help"], { timeout: 5000 }, (error) => {
      resolve(!error || error.code !== "ENOENT");
    });
  });
}

module.exports = { runPrism, checkPrismAvailable, resolvePrismBinary };
