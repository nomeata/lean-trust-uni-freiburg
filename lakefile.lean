import Lake
open System Lake DSL

require «verso-slides» from git
  "https://github.com/leanprover/verso-slides.git"@"main"

package «lean-trust-freiburg-slides» where
  version := v!"0.1.0"

lean_lib Slides

@[default_target] lean_exe «lean-trust-freiburg-slides» where root := `Main
