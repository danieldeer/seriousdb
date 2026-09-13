{
	perSystem = { pkgs, config, ... }: {
		devShells.default = pkgs.mkShell {
			inputsFrom = [
				config.pre-commit.devShell
			];

			nativeBuildInputs = [
				pkgs.nixd
				pkgs.nixpkgs-fmt
				pkgs.pre-commit
				pkgs.cocogitto
				pkgs.uv
				pkgs.ruff
				pkgs.fastapi-cli
				(pkgs.python314.withPackages (ps: [
					ps.fastapi
				]))
			];

			shellHook = ''
				export PYTHONPATH="${toString ./.}/src''${PYTHONPATH:+:$PYTHONPATH}"

				${config.pre-commit.installationScript}
			'';
		};

		pre-commit.check.enable = true;

		pre-commit.settings.hooks.check-merge-conflicts.enable = true;
		pre-commit.settings.hooks.check-symlinks.enable = true;
		pre-commit.settings.hooks.check-added-large-files.enable = true;
		pre-commit.settings.hooks.check-added-large-files.args = [
			"--maxkb=100"
			"--enforce-all"
		];

		pre-commit.settings.hooks.cog.enable = true;
		pre-commit.settings.hooks.cog.entry = "${pkgs.cocogitto}/bin/cog verify --file";
		pre-commit.settings.hooks.cog.stages = [
			"commit-msg"
		];

		pre-commit.settings.hooks.ripsecrets.enable = true;

		pre-commit.settings.hooks.check-yaml.enable = true;
		pre-commit.settings.hooks.check-json.enable = true;
		pre-commit.settings.hooks.check-toml.enable = true;
	};
}
