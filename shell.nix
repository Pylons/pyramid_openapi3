let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-26.05 on 2026-06-08
    url = "https://github.com/NixOS/nixpkgs/archive/bd0ff2d3eac24699c3664d5966b9ef36f388e2ca.tar.gz";
    sha256 = "0i4ymrwz6aanx3byjnignx13sdrdp1v1llgg81jn3mjz5q89ik5b";
  };

  pkgs = import nixpkgs { };
in

pkgs.mkShell {
  name = "dev-shell";

  # The supported Python range (3.11-3.14); uv uses these directly.
  packages = with pkgs; [
    git
    python311
    python314
    uv

    # Linters and formatters used by the pre-commit hooks
    actionlint
    codespell
    deadnix
    detect-secrets
    nixfmt
    prek
    ruff
    shellcheck
    statix
    tombi
    ty
    yamlfmt
    zizmor
  ];

  # Use the Nix-provided interpreters instead of uv-managed downloads, which do
  # not run on NixOS without extra patching.
  UV_PYTHON_DOWNLOADS = "never";
}
