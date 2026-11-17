import VersoSlides
import Slides

open VersoSlides

-- Inline SVG figures so they use the slide font (an SVG loaded via <img> cannot).
def inlineFigure (html file alt svgClass : String) : IO String := do
  let svg ← IO.FS.readFile (System.FilePath.mk "static/images" / file)
  let svg := svg.replace "<svg " s!"<svg class=\"{svgClass}\" "
  let base := (System.FilePath.mk file).fileName.getD file
  let needle := s!"<img src=\"images/{base}\" alt=\"{alt}\""
  -- Newer Verso closes the tag with `/>`, older with `>`.
  -- Figures whose slide was removed are skipped.
  return (html.replace (needle ++ "/>") svg).replace (needle ++ ">") svg

/-- SVG figures to inline. Each entry: (file, alt text exactly as in Slides.lean, CSS class). -/
def figures : List (String × String × String) := [
  ("why-lean.svg", "Why Lean", "fig-full"),
  ("history.svg", "History of Lean", "fig-full"),
  ("architecture.svg", "Architecture of Lean", "fig-full"),
  ("threat-models.svg", "Threat models", "fig-full"),
  ("attacks.svg", "Attacks and defenses", "fig-full"),
  ("comparator.svg", "Comparator", "fig-full"),
  ("checker.svg", "A Lean checker is a type checker", "fig-full"),
  ("judgments.svg", "The three judgments", "fig-large"),
  ("typing-rules.svg", "Typing rules", "fig-large"),
  ("standard-path.svg", "Standard path to consistency", "fig-large"),
  ("interpretation.svg", "The interpretation", "fig-full"),
  ("interpretation2.svg", "The interpretation, continued", "fig-full"),
  ("preservation-take1.svg", "Preservation, take 1", "fig-large"),
  ("well-denoted.svg", "Well-denoted terms", "fig-full"),
  ("preservation-take2.svg", "Preservation, take 2", "fig-large"),
  ("preservation-point.svg", "Preservation up to a point", "fig-large"),
  ("certification-tax.svg", "The certification tax", "fig-large"),
  ("sorts-universes.svg", "Sorts and universes", "fig-large"),
  ("inductive-types.svg", "Inductive types", "fig-full"),
  ("type-theory-sugar.svg", "Lean syntax and its set-theoretic reading", "fig-full"),
  ("checker-family.svg", "The con-leche family of checkers", "fig-full"),
  ("point-not-empty.svg", "Why is the point not the empty set", "fig-large")
]

def main : IO UInt32 := do
  let config : Config := {
    theme := "white", width := 1920, height := 1080,
    slideNumber := true, center := false, margin := 0, transition := "fade"
  }
  let rc ← slidesMain (config := config) (doc := %doc Slides)
  if rc != 0 then return rc
  for file in ["layout.css", "lean-logo.png", "lean-logo-large.png"] do
    let bytes ← IO.FS.readBinFile (System.FilePath.mk "static" / file)
    IO.FS.writeBinFile (config.outputDir / file) bytes
  -- The deck stylesheet, served with its font locally.
  let css ← IO.FS.readFile "static/custom.css"
  let css := css.replace
    "https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@300;400;500;600;700&display=swap"
    "fonts/source-sans-3.css"
  IO.FS.writeFile (config.outputDir / "custom.css") css
  IO.FS.createDirAll (config.outputDir / "fonts")
  for entry in ← System.FilePath.readDir "static/fonts" do
    let bytes ← IO.FS.readBinFile entry.path
    IO.FS.writeBinFile (config.outputDir / "fonts" / entry.fileName) bytes
  let htmlPath := config.outputDir / "index.html"
  let html ← IO.FS.readFile htmlPath
  let html := html.replace "</head>"
    "<link rel=\"stylesheet\" href=\"custom.css\">\n<link rel=\"stylesheet\" href=\"layout.css\">\n</head>"
  let html := html.replace "Reveal.initialize({"
    "Reveal.initialize({\n        disableLayout: true,"
  let mut html := html
  for (file, alt, cls) in figures do
    html ← inlineFigure html file alt cls
  IO.FS.writeFile htmlPath html
  -- Make the generated deck usable as a local file.
  let docsJson ← IO.FS.readFile (config.outputDir / "-verso-docs.json")
  let hlPath := config.outputDir / "lib" / "highlighting.js"
  let hl ← IO.FS.readFile hlPath
  let hl := hl.replace
    "fetch(docsJson).then((resp) => resp.json()).then((versoDocData) => {"
    s!"Promise.resolve({docsJson}).then((versoDocData) => \{"
  let hl := hl.replace
    "await (fetch(\"-verso-docs.json\").then((resp) => resp.json()))"
    docsJson
  let hl := hl.replace "window.onload = () => {" "window.addEventListener('load', () => {"
  IO.FS.writeFile hlPath hl
  let panelPath := config.outputDir / "lib" / "panel.js"
  let panel ← IO.FS.readFile panelPath
  let panel := panel.replace
    "fetch(\"-verso-docs.json\")\n            .then(function (r) {\n                return r.ok ? r.json() : {};\n            })\n            .then(function (j) {\n                docsJson = j;\n            })\n            .catch(function () {\n                docsJson = {};\n            });"
    s!"docsJson = {docsJson};"
  IO.FS.writeFile panelPath panel
  let lightboxPath := config.outputDir / "lib" / "lightbox.js"
  let lightbox ← IO.FS.readFile lightboxPath
  let lightbox := lightbox.replace
    "fetch(\"-verso-docs.json\")\n            .then(function (r) {\n                return r.ok ? r.json() : {};\n            })"
    s!"Promise.resolve({docsJson})"
  IO.FS.writeFile lightboxPath lightbox
  return rc
