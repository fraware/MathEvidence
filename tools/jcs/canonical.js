#!/usr/bin/env node
/**
 * Third independent mathevidence-jcs-0.2 implementation (JavaScript).
 * Cross-checks evidence/conformance/vectors/canonical_json_vectors.json.
 *
 * Usage: node tools/jcs/canonical.js [vectors.json]
 */
"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

function utf16KeyUnits(key) {
  const units = [];
  for (const ch of key) {
    const cp = ch.codePointAt(0);
    if (cp <= 0xffff) {
      units.push(cp);
    } else {
      const adj = cp - 0x10000;
      units.push(0xd800 + (adj >> 10));
      units.push(0xdc00 + (adj & 0x3ff));
    }
  }
  return units;
}

function compareUtf16(a, b) {
  const ua = utf16KeyUnits(a);
  const ub = utf16KeyUnits(b);
  const n = Math.min(ua.length, ub.length);
  for (let i = 0; i < n; i++) {
    if (ua[i] !== ub[i]) return ua[i] - ub[i];
  }
  return ua.length - ub.length;
}

function escapeString(s) {
  let out = '"';
  for (const ch of s) {
    const o = ch.codePointAt(0);
    if (ch === '"') out += '\\"';
    else if (ch === "\\") out += "\\\\";
    else if (ch === "\b") out += "\\b";
    else if (ch === "\t") out += "\\t";
    else if (ch === "\n") out += "\\n";
    else if (ch === "\f") out += "\\f";
    else if (ch === "\r") out += "\\r";
    else if (o < 0x20) out += "\\u" + o.toString(16).padStart(4, "0");
    else out += ch;
  }
  return out + '"';
}

function canonicalDumps(value) {
  if (value === null) return "null";
  if (value === true) return "true";
  if (value === false) return "false";
  if (typeof value === "string") return escapeString(value);
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new Error("non-finite floats forbidden");
    }
    if (!Number.isInteger(value)) {
      throw new Error("floats forbidden in theorem-binding digests");
    }
    return String(value);
  }
  if (Array.isArray(value)) {
    return "[" + value.map(canonicalDumps).join(",") + "]";
  }
  if (typeof value === "object") {
    const keys = Object.keys(value).sort(compareUtf16);
    const body = keys
      .map((k) => escapeString(k) + ":" + canonicalDumps(value[k]))
      .join(",");
    return "{" + body + "}";
  }
  throw new Error("unsupported JSON type: " + typeof value);
}

function sha256Digest(value) {
  const text = canonicalDumps(value);
  const hex = crypto.createHash("sha256").update(text, "utf8").digest("hex");
  return "sha256:" + hex;
}

function main() {
  const repoRoot = path.resolve(__dirname, "..", "..");
  const vectorsPath =
    process.argv[2] ||
    path.join(
      repoRoot,
      "evidence",
      "conformance",
      "vectors",
      "canonical_json_vectors.json"
    );
  const data = JSON.parse(fs.readFileSync(vectorsPath, "utf8"));
  let failed = 0;
  for (const c of data.cases || []) {
    const canonical = canonicalDumps(c.input);
    const digest = sha256Digest(c.input);
    if (canonical !== c.canonical || digest !== c.digest) {
      console.error("FAIL", c.id);
      console.error("  got canonical", canonical);
      console.error("  exp canonical", c.canonical);
      console.error("  got digest", digest);
      console.error("  exp digest", c.digest);
      failed += 1;
    } else {
      console.log("ok", c.id);
    }
  }
  if (failed) {
    console.error(`jcs js failed (${failed})`);
    process.exit(1);
  }
  console.log(`jcs js ok (${(data.cases || []).length} cases)`);
}

if (require.main === module) {
  main();
}

module.exports = { canonicalDumps, sha256Digest };
