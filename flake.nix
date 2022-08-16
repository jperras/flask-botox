{
  description = "Nix flake for flask-botox";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    {
      # Nixpkgs overlay providing the application
      overlay = nixpkgs.lib.composeManyExtensions [
        poetry2nix.overlay
        (final: prev: {
          # The application
          myapp = prev.poetry2nix.mkPoetryApplication {
            projectDir = ./.;
          };

          # The environment
          env = prev.poetry2nix.mkPoetryEnv {
            projectDir = ./.;
            editablePackageSources = { flask-botox-app = ./flask_botox; };
            python = prev.python3;
          };
        })
      ];
    } // (flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlay ];
        };
      in
      {
        apps = {
          myapp = pkgs.myapp;
        };

        defaultApp = pkgs.myapp;

        devShell = pkgs.mkShell {
          name = "flask-botox";
          # Add anything in here if you want it to run when we run `nix develop`.
          shellHook = "";

          # Additional packages list here for devShell
          buildInputs = with pkgs; [
            env # Our application environment
            poetry # Python package manager
            pkgs.nodePackages.pyright # Language server
            nixpkgs-fmt # For formatting nix files
            black
            black-macchiato
          ];
        };
      }));
}
