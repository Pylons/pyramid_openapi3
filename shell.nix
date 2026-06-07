let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-25.11 on 2026-06-07
    url = "https://github.com/NixOS/nixpkgs/archive/535f3e6942cb1cead3929c604320d3db54b542b9.tar.gz";
    sha256 = "0f9137a4dggpm5p6ikzh5zvigjnlyfwpi3ssskhx5rwsii7nbzys";
  };

  pkgs = import nixpkgs { };
in

pkgs.mkShell {
  name = "dev-shell";

  buildInputs = with pkgs; [
    # The supported Python range (3.10-3.12); uv uses these directly.
    python310
    python311
    python312
    uv
    git
    pre-commit
    nixpkgs-fmt
  ];

  # Use the Nix-provided interpreters instead of uv-managed downloads.
  UV_PYTHON_DOWNLOADS = "never";
}
