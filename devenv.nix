{
  pkgs,
  lib,
  config,
  ...
}:
{
  # https://devenv.sh/languages/
  languages.python = {
    enable = true;
    uv.enable = true;
  };
  # https://devenv.sh/packages/
  packages = [
    pkgs.python3Packages.jupyter
    pkgs.python3Packages.notebook
    pkgs.libxml2
    pkgs.quarto
  ];
  # https://devenv.sh/scripts/
  scripts.notebook.exec = "jupyter notebook";
  # See full reference at https://devenv.sh/reference/options/
}
