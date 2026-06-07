let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-25.11 on 2026-06-07
    url = "https://github.com/NixOS/nixpkgs/archive/535f3e6942cb1cead3929c604320d3db54b542b9.tar.gz";
    sha256 = "0f9137a4dggpm5p6ikzh5zvigjnlyfwpi3ssskhx5rwsii7nbzys";
  };
  poetry2nixsrc = builtins.fetchTarball {
    # https://github.com/nix-community/poetry2nix on 2026-06-07
    url = "https://github.com/nix-community/poetry2nix/archive/ce2369db77f45688172384bbeb962bc6c2ea6f94.tar.gz";
    sha256 = "0xq52gq2920xnv7n8rchy3myxbijfpap8z0sd572ifla9dnpqzvi";
  };

  pkgs = import nixpkgs { };
  poetry2nix = import poetry2nixsrc { inherit pkgs; };

  commonPoetryArgs = {
    projectDir = ./.;
    preferWheels = true;
    editablePackageSources = {
      pyramid_openapi3 = ./.;
    };
    overrides = poetry2nix.overrides.withDefaults (self: super: {
      # poetry2nix's default mypy override unconditionally adds `types-typed-ast`
      # to mypy's buildInputs, but nixpkgs 25.11 removed that package. mypy
      # installs from a wheel here (preferWheels), so the stub is never used;
      # provide an empty placeholder so the reference resolves.
      types-typed-ast = self.buildPythonPackage {
        pname = "types-typed-ast";
        version = "0";
        src = builtins.toFile "empty" "";
        unpackPhase = "true";
        format = "other";
        installPhase = "mkdir -p $out";
      };
    });
  };

  devEnv_312 = poetry2nix.mkPoetryEnv (commonPoetryArgs // {
    python = pkgs.python312;
  });

  devEnv_310 = poetry2nix.mkPoetryEnv (commonPoetryArgs // {
    python = pkgs.python310;
    pyproject = ./py310/pyproject.toml;
    poetrylock = ./py310/poetry.lock;
  });

in

pkgs.mkShell {
  name = "dev-shell";

  buildInputs = with pkgs; [
    devEnv_312
    devEnv_310
    poetry
    git
    pre-commit
    nixpkgs-fmt
  ];
}
