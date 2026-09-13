{
	description = "Development environment for seriousdb";

	inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
	inputs.flake-parts.url = "github:hercules-ci/flake-parts";
	inputs.git-hooks-nix.url = "github:cachix/git-hooks.nix";
	inputs.git-hooks-nix.inputs.nixpkgs.follows = "nixpkgs";

	outputs = inputs@{ flake-parts, ... }:
	flake-parts.lib.mkFlake {
		inherit inputs;
	} {
		systems = inputs.nixpkgs.lib.systems.flakeExposed;

		imports = [
			inputs.git-hooks-nix.flakeModule

			./nix/check/sanity.nix
			./nix/dev
			./nix/pkg
		];
	};
}
