{
  description = "橋の構造100選 - Interactive Bridge FEM Analysis";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          fastapi uvicorn numpy pillow playwright
        ]);
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.nodejs_20
            pkgs.ffmpeg
            pkgs.git
          ];
          shellHook = ''
            echo "橋の構造100選 dev shell ready"
            echo "  python3 -> ${pythonEnv}/bin/python3"
            echo "  uvicorn -> ${pythonEnv}/bin/uvicorn"
            echo "  node    -> ${pkgs.nodejs_20}/bin/node"
            echo "  ffmpeg  -> ${pkgs.ffmpeg}/bin/ffmpeg"
            
            export REPO_ROOT=$(pwd)
            export PYTHONPATH="$REPO_ROOT/backend:$PYTHONPATH"
          '';
        };

        packages.default = pkgs.stdenv.mkDerivation {
          pname = "bridge100";
          version = "0.1.0";
          src = ./.;
          buildInputs = [ pythonEnv pkgs.makeWrapper ];
          installPhase = ''
            mkdir -p $out/share/bridge100
            cp -r backend frontend scripts $out/share/bridge100/
            mkdir -p $out/bin
            makeWrapper ${pythonEnv}/bin/uvicorn $out/bin/bridge100-server \
              --add-flags "backend.main:app" \
              --add-flags "--host" --add-flags "0.0.0.0" \
              --add-flags "--port" --add-flags "8000" \
              --set PYTHONPATH "$out/share/bridge100/backend"
          '';
        };
      });
}
