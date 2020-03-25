let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-19.09 on 2019-11-24
    # TODO: make sure this matches the commit has in config.yml
    url = "https://github.com/nixos/nixpkgs/archive/4ad6f1404a8cd69a11f16edba09cc569e5012e42.tar.gz";
    sha256 = "1pclh0hvma66g3yxrrh9rlzpscqk5ylypnmiczz1bwwrl8n21q3h";
  };
  pkgs = import nixpkgs { config = { allowUnfree = true; }; };
in

pkgs.mkShell {
  name = "dev-shell";
  buildInputs = [
    pkgs.pipenv
    pkgs.python37Full
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

  # TODO: Potentially remove when Nixos 20.03 is released:
  # https://github.com/NixOS/nixpkgs/issues/73254
  unset PYTHONPATH
  '';
}
