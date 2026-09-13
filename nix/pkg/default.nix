{ self, ... }: {
	perSystem = { pkgs, ... }: {
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
			];

			doCheck = false;
		};
	};
}
