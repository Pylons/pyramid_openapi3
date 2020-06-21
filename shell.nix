let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-20.03 on 2020-06-21
    # TODO: make sure this matches the commit has in config.yml
    url = "https://github.com/nixos/nixpkgs/archive/2b417708c282d84316366f4125b00b29c49df10f.tar.gz";
    sha256 = "1pclh0hvma66g3yxrrh9rlzpscqk5ylypnmiczz1bwwrl8n21q33";
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
  '';
}
