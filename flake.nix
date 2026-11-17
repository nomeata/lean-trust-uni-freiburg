{
  description = "Lean – Architecture, Meaning and Trust (slides)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (pkgs: {
        # mkShell brings a C compiler (`cc`), which MD4Lean needs.
        default = pkgs.mkShell {
          packages = with pkgs; [
            elan          # lean, lake (version from lean-toolchain)
            python3       # tools/figures.py, tools/serve.py
            nodejs        # export-pdf.mjs (npm install for playwright)
            chromium      # PDF export and screenshots
            poppler-utils # pdfunite
            texliveFull # latex and dvisvgm, for the formulas in tools/figures.py
          ];
          # Playwright uses this browser instead of downloading its own.
          CHROME = "${pkgs.chromium}/bin/chromium";
          PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = "1";
        };
      });
    };
}
