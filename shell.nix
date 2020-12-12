let
  nixpkgs = builtins.fetchTarball {
    # https://github.com/NixOS/nixpkgs/tree/nixos-20.09 on 2020-12-12
    url = "https://github.com/nixos/nixpkgs/archive/65c9cc79f1d179713c227bf447fb0dac384cdcda.tar.gz";
    sha256 =  "0whxlm098vas4ngq6hm3xa4mdd2yblxcl5x5ny216zajp08yp1wf";
  };
  pkgs = import nixpkgs { config = { allowUnfree = true; }; };
in

pkgs.mkShell {
  name = "dev-shell";
  buildInputs = [
    pkgs.pipenv
    pkgs.python38Full
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

  # https://github.com/NixOS/nixpkgs/issues/73254
  unset PYTHONPATH
  '';
}
