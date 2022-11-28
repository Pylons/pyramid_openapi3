let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-22.05 on 2022-11-28
    url = "https://github.com/nixos/nixpkgs/archive/fecf05d4861f3985e8dee73f08bc82668ef75125.tar.gz";
    sha256 =  "0f55nj4x8splycfy32p4sjv1if2kg5wp90m9h90wpwrkm3sn9yqs";
  };
  poetry2nixsrc = builtins.fetchTarball {
    # https://github.com/nix-community/poetry2nix/commits/master on 2022-11-15
    url = "https://github.com/nix-community/poetry2nix/archive/023b9fc37f17cf67b3d88ed4b7ff6bcc64d2a200.tar.gz";
    sha256 =  "01bphniyb0h8x4q2glvjpvpx4cdjvbg8k9j8nip36myj9irmldkx";
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
    overrides = poetry2nix.defaultPoetryOverrides.extend ( self: super: {
      autoflake = super.autoflake.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.hatchling ];
          postInstall = ''
          rm -f $out/lib/python3*/site-packages/LICENSE
        '';
        }
      );
      exceptiongroup = super.exceptiongroup.overridePythonAttrs (
        old: {
          buildInputs = (old.buildInputs or [ ]) ++ [ self.flit_scm ];
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
