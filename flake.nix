{
  description = "tcard - tabletop cards for a thermal printer";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      each = nixpkgs.lib.genAttrs systems;
    in {
      packages = each (system: {
        default = nixpkgs.legacyPackages.${system}.callPackage ./default.nix { };
        tcard = self.packages.${system}.default;
      });

      checks = each (system: {
        tests = self.packages.${system}.default.passthru.tests;
      });
    };
}
