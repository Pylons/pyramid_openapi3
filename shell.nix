let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-26.05 on 2026-10-21
    url = "https://github.com/NixOS/nixpkgs/archive/da6dc0e7b26060f2f71ce3ef7088fb56ee44fa36.tar.gz";
    sha256 = "0hlv2n0gcpcxmjka021806iswd7mlmpq1gpnvff2mr2fmmyx2nrj";
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
    cacert
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
