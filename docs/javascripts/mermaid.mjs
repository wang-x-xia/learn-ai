import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"

mermaid.initialize({
  startOnLoad: false,
  securityLevel: "loose",
})

// Necessary to make it visible to Zensical
window.mermaid = mermaid
