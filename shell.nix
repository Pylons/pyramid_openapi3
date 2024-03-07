let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-23.11 on 2024-03-07
    url = "https://github.com/nixos/nixpkgs/archive/880992dcc006a5e00dd0591446fdf723e6a51a64.tar.gz";
    sha256 = "1rsbjwbjgnrh0gm54w7nlshkkgp5718d5rk4x8kvklpfivlpfb5n";
  };
  poetry2nixsrc = builtins.fetchTarball {
    # https://github.com/nix-community/poetry2nix/commits/master on 2024-03-07
    url = "https://github.com/nix-community/poetry2nix/archive/3c92540611f42d3fb2d0d084a6c694cd6544b609.tar.gz";
    sha256 = "1jfrangw0xb5b8sdkimc550p3m98zhpb1fayahnr7crg74as4qyq";
  };

  pkgs = import nixpkgs { };
  poetry2nix = import poetry2nixsrc {
    inherit pkgs;
    # inherit (pkgs) poetry;
  };

  commonPoetryArgs = {
    projectDir = ./.;
    preferWheels = true;
    editablePackageSources = {
      pyramid_openapi3 = ./.;
    };
    overrides = poetry2nix.overrides.withDefaults (self: super: {

      ruamel-yaml = super.ruamel-yaml.overridePythonAttrs (
        old: {
          propagatedBuildInputs = [ ];
        }
      );

    });
  };

  devEnv_311 = poetry2nix.mkPoetryEnv (commonPoetryArgs // {
    python = pkgs.python311;
  });

  devEnv_39 = poetry2nix.mkPoetryEnv (commonPoetryArgs // {
    python = pkgs.python39;
    pyproject = ./py39/pyproject.toml;
    poetrylock = ./py39/poetry.lock;
  });

in

pkgs.mkShell {
  name = "dev-shell";

  buildInputs = with pkgs; [
    devEnv_311
    devEnv_39
    poetry
    gitAndTools.pre-commit
    nixpkgs-fmt
  ];
}
