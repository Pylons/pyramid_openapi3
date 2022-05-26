let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-21.11 on 2022-05-25
    url = "https://github.com/nixos/nixpkgs/archive/cbd40c72b2603ab54e7208f99f9b35fc158bc009.tar.gz";
    sha256 =  "09ffmjs9lwm97p8v8977p319kc8ys2fjnyv08gb99kgbr7gfiyfd";
  };
  pkgs = import nixpkgs { config = { allowUnfree = true; }; };
in

pkgs.mkShell {
  name = "dev-shell";
  buildInputs = [
    pkgs.pipenv
    pkgs.python39Full
    pkgs.codespell

    # C dependencies that python packages need
    pkgs.libffi
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
