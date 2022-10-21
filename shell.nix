let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-22.11 on 2022-11-29
    url = "https://github.com/nixos/nixpkgs/archive/ce5fe99df1f15a09a91a86be9738d68fadfbad82.tar.gz";
    sha256 =  "1zqyq7v1gxrg2b7zizf4npask4vqbs4s7khwffxafgm20gxngb6a";
  };
  poetry2nixsrc = builtins.fetchTarball {
    # https://github.com/nix-community/poetry2nix/commits/master on 2022-11-29
    url = "https://github.com/nix-community/poetry2nix/archive/ce8425ccc2884c1065927a38d1700024f431cf0f.tar.gz";
    sha256 =  "07x48abw18qfxdmsz8hdd762vj8n5l2syh9xm40v851bhidbjswc";
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

  devEnv = poetry2nix.mkPoetryEnv ({
    python = pkgs.python310;
    projectDir = ./.;
    editablePackageSources = {
      pyramid_openapi3 = ./.;
    };
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
  });

in

pkgs.mkShell {
  name = "dev-shell";

  buildInputs = with pkgs; [
      devEnv
      poetry
      gitAndTools.pre-commit
    ];
}
