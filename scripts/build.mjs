import { build } from "esbuild";
import { cp, mkdir, rm } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const source = resolve(root, "src", "extension");
const outdir = resolve(root, "dist", "chrome-extension");

await rm(outdir, { recursive: true, force: true });
await mkdir(outdir, { recursive: true });
await cp(resolve(source, "manifest.json"), resolve(outdir, "manifest.json"));
await cp(resolve(source, "popup.html"), resolve(outdir, "popup.html"));
await cp(resolve(source, "popup.css"), resolve(outdir, "popup.css"));

await Promise.all([
  build({
    entryPoints: [resolve(source, "content.ts")],
    outfile: resolve(outdir, "content.js"),
    bundle: true,
    format: "iife",
    target: "chrome120",
    sourcemap: true
  }),
  build({
    entryPoints: [resolve(source, "content-generic.ts")],
    outfile: resolve(outdir, "content-generic.js"),
    bundle: true,
    format: "iife",
    target: "chrome120",
    sourcemap: true
  }),
  build({
    entryPoints: [resolve(source, "service-worker.ts")],
    outfile: resolve(outdir, "service-worker.js"),
    bundle: true,
    format: "esm",
    target: "chrome120",
    sourcemap: true
  }),
  build({
    entryPoints: [resolve(source, "popup.ts")],
    outfile: resolve(outdir, "popup.js"),
    bundle: true,
    format: "iife",
    target: "chrome120",
    sourcemap: true
  })
]);
