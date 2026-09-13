{ self, ... }: {
	perSystem = { pkgs, config, ... }: {
		packages.seriousdb_docker_image = pkgs.dockerTools.streamLayeredImage {
			name = "seriousdb";
			tag = "latest";

			contents = [
				pkgs.cacert

				config.packages.seriousdb
			];

			config.Env = ["PYTHONUNBUFFERED=1"];
			config.Cmd = [
				"${config.packages.seriousdb}/bin/seriousdb"
			];

			config.ExposedPorts."8000/tcp" = {};
		};

		packages.default = config.packages.seriousdb;

		packages.seriousdb = pkgs.python314Packages.buildPythonApplication {
			pname = "seriousdb";
			version = "0.1.0";
			format = "pyproject";
			src = self;

			nativeBuildInputs = [
				pkgs.python314Packages.setuptools
				pkgs.python314Packages.wheel
			];

			propagatedBuildInputs = [
				pkgs.python314Packages.fastapi
				pkgs.python314Packages.uvicorn
			];

			doCheck = false;
			dontCheckRuntimeDeps = true;
		};
	};
}
