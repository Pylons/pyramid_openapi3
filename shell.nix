let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-22.11 on 2023-03-23
    url = "https://github.com/nixos/nixpkgs/archive/9ef6e7727f4c31507627815d4f8679c5841efb00.tar.gz";
    sha256 = "0w2r5cfrpqmjmjy8azllrbgr5d92if87i9ybgvpk6din4w79ibal";
  };
  poetry2nixsrc = builtins.fetchTarball {
    # https://github.com/nix-community/poetry2nix/commits/master on 2023-03-23
    url = "https://github.com/nix-community/poetry2nix/archive/50ec694c27a12bc178fff961c4dd927fa6a47f18.tar.gz";
    sha256 = "1s596k78sbzjmh5l7rzaf27f97r87dia1zyxkadir5s8vvjvw4ya";
  };

  # Fix for installing PasteDeploy from https://github.com/nix-community/poetry2nix/issues/750
  preDefaults = self: super: {
    # Unset pastedeploy/PasteDeploy and rename to pastedeploy_ to avoid infinite recursion
    # then in postDefaults we set `pastedeploy_` back to `pastedeploy`
    pastedeploy = null;
    PasteDeploy = null;
    pastedeploy_ = super.pastedeploy;
  };
  postDefaults = self: super: {
    # Avoid infinite recursion
    pastedeploy = super.pastedeploy_;
  };

  pkgs = import nixpkgs { };
  poetry2nix = import poetry2nixsrc {
    inherit pkgs;
    inherit (pkgs) poetry;
  };

  commonPoetryArgs = {
    projectDir = ./.;
    overrides = ((poetry2nix.defaultPoetryOverrides.overrideOverlay preDefaults).extend postDefaults).extend (self: super: {

      openapi-core = super.openapi-core.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.poetry ];
        }
      );
      pastedeploy = super.pastedeploy.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      pyrepl = super.pyrepl.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      fancycompleter = super.fancycompleter.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      typecov = super.typecov.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      wmctrl = super.wmctrl.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      pdbpp = super.pdbpp.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      types-pytest-lazy-fixture = super.types-pytest-lazy-fixture.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      flake8-assertive = super.flake8-assertive.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      flake8-builtins = super.flake8-builtins.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      flake8-deprecated = super.flake8-deprecated.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      flake8-ensure-ascii = super.flake8-ensure-ascii.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      flake8-comprehensions = super.flake8-comprehensions.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      flake8-mutable = super.flake8-mutable.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      flake8-plone-hasattr = super.flake8-plone-hasattr.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      flake8-tuple = super.flake8-tuple.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      flake8-super-call = super.flake8-super-call.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.setuptools ];
        }
      );
      autoflake = super.autoflake.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.hatchling ];
          postInstall = ''
            rm -f $out/lib/python3*/site-packages/LICENSE
          '';
        }
      );

    });
  };

  devEnv_311 = poetry2nix.mkPoetryEnv (commonPoetryArgs // {
    python = pkgs.python311;
  });

  devEnv_38 = poetry2nix.mkPoetryEnv (commonPoetryArgs // {
    python = pkgs.python38;
  });

in

pkgs.mkShell {
  name = "dev-shell";

  buildInputs = with pkgs; [
    devEnv_311
    devEnv_38
    poetry
    gitAndTools.pre-commit
    nixpkgs-fmt
  ];
}
