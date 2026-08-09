import type { ClipboardPayload } from "./types";

const BLOCK_TAGS = new Set(["p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote", "pre", "table", "tr", "hr"]);
const ALLOWED_TAGS = new Set([
  "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote", "pre", "code",
  "strong", "em", "a", "table", "thead", "tbody", "tfoot", "tr", "th", "td", "br", "hr"
]);
const DROP_TAGS = new Set(["script", "style", "button", "svg", "canvas", "img", "video", "audio", "iframe", "form", "input"]);
const WRAPPER_TAGS = new Set(["div", "section", "article", "main", "aside", "header", "footer", "span"]);

function cleanHref(value: string): string | null {
  try {
    const url = new URL(value, "https://clean-paste.invalid");
    if (!(["http:", "https:", "mailto:"].includes(url.protocol))) return null;
    for (const key of [...url.searchParams.keys()]) {
      if (/^(utm_|ref$|ref_|source$|mc_)/i.test(key)) url.searchParams.delete(key);
    }
    return url.hostname === "clean-paste.invalid" ? value : url.toString();
  } catch {
    return null;
  }
}

function appendChildren(input: Node, output: Node, document: Document, inPre = false): void {
  for (const child of [...input.childNodes]) appendNode(child, output, document, inPre);
}

function appendNode(input: Node, output: Node, document: Document, inPre = false): void {
  if (input.nodeType === Node.TEXT_NODE) {
    const text = inPre ? input.textContent ?? "" : (input.textContent ?? "").replace(/\s+/g, " ");
    if (text) output.appendChild(document.createTextNode(text));
    return;
  }
  if (input.nodeType !== Node.ELEMENT_NODE) return;

  const element = input as Element;
  const tag = element.tagName.toLowerCase();
  if (DROP_TAGS.has(tag) || element.matches("[data-testid*='copy' i], [aria-label*='copy' i], [class*='toolbar' i], [class*='actions' i]")) return;

  if (WRAPPER_TAGS.has(tag) || !ALLOWED_TAGS.has(tag)) {
    const hasBlockChildren = [...element.children].some((child) => BLOCK_TAGS.has(child.tagName.toLowerCase()));
    if (hasBlockChildren || tag === "span") {
      appendChildren(element, output, document, inPre);
    } else {
      const paragraph = document.createElement("p");
      appendChildren(element, paragraph, document, inPre);
      if (paragraph.textContent?.trim()) output.appendChild(paragraph);
    }
    return;
  }

  const normalizedTag = tag === "b" ? "strong" : tag === "i" ? "em" : tag;
  const next = document.createElement(normalizedTag);
  if (normalizedTag === "a") {
    const href = element.getAttribute("href");
    if (href) {
      const safe = cleanHref(href);
      if (safe) next.setAttribute("href", safe);
    }
  }
  if (["ol", "li"].includes(normalizedTag) && element.hasAttribute("start")) next.setAttribute("start", element.getAttribute("start") ?? "1");
  appendChildren(element, next, document, inPre || normalizedTag === "pre");
  if (normalizedTag === "br" || normalizedTag === "hr" || next.textContent?.trim() || next.children.length) output.appendChild(next);
}

function normalizeRoot(inputHtml: string): HTMLElement {
  const parser = new DOMParser();
  const source = parser.parseFromString(inputHtml, "text/html");
  const output = source.createElement("div");
  appendChildren(source.body, output, source);
  for (const empty of [...output.querySelectorAll("p, li, td, th, blockquote")]) {
    if (!empty.textContent?.trim() && !empty.querySelector("br, hr")) empty.remove();
  }
  return output;
}

function plainText(root: HTMLElement): string {
  const lines: string[] = [];
  const visit = (node: Node, level = 0): void => {
    if (node.nodeType === Node.TEXT_NODE) {
      const text = node.textContent?.replace(/\s+/g, " ") ?? "";
      if (text) lines.push(text);
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    const element = node as Element;
    const tag = element.tagName.toLowerCase();
    if (tag === "br") {
      lines.push("\n");
      return;
    }
    if (tag === "hr") {
      lines.push("\n---\n");
      return;
    }
    if (tag === "pre") {
      lines.push(`\n${element.textContent?.trimEnd() ?? ""}\n`);
      return;
    }
    if (tag === "li") {
      lines.push(`\n${"  ".repeat(level)}${element.parentElement?.tagName === "OL" ? "1. " : "- "}`);
      for (const child of [...element.childNodes]) visit(child, level + 1);
      lines.push("\n");
      return;
    }
    if (tag === "tr") {
      lines.push("\n");
      for (const cell of [...element.children]) lines.push(`${cell.textContent?.trim() ?? ""}\t`);
      return;
    }
    if (BLOCK_TAGS.has(tag)) lines.push("\n");
    for (const child of [...element.childNodes]) visit(child, tag === "li" ? level + 1 : level);
    if (BLOCK_TAGS.has(tag)) lines.push("\n");
  };
  for (const node of [...root.childNodes]) visit(node);
  return lines.join("").replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}

export function normalizeSelection(html: string): ClipboardPayload {
  const root = normalizeRoot(html);
  return { html: root.innerHTML.trim(), plainText: plainText(root) };
}
