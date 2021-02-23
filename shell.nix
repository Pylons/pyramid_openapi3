let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-20.09 on 2021-02-17
    url = "https://github.com/nixos/nixpkgs/archive/95ce0f52ec10cbfa2b72a2d8623e6a363e77e4dd.tar.gz";
    sha256 =  "0r1pm0yrxf6ygmgaq9g5ha2kg0wik4yyaj2idjwsh7aar9mqzfjy";
  };
  pkgs = import nixpkgs { config = { allowUnfree = true; }; };
in

pkgs.mkShell {
  name = "dev-shell";
  buildInputs = [
    pkgs.pipenv
    pkgs.python39Full
    pkgs.codespell
  ];

  shellHook = ''
  # create virtualenv in ./.venv
  export PIPENV_VENV_IN_PROJECT=1

  # pipenv reports it needs this
  export LANG=en_US.UTF-8

  # support for building wheels:
  # https://nixos.org/nixpkgs/manual/#python-setup.py-bdist_wheel-cannot-create-.whl
  unset SOURCE_DATE_EPOCH
  '';
}
