# a simple e2e sanity check to ensure the database is working
#
# WILL
# 	- reach the binary at `/docs`
# 	- place a value in the database at `/db`
# 	- check the value is present

{
	perSystem = { pkgs, config, ... }: {
		checks.launch = pkgs.testers.runNixOSTest {
			name = "launch";

			nodes.main.environment.systemPackages = [
				config.packages.seriousdb
			];

			nodes.main.networking.firewall.allowedTCPPorts = [8000];

			testScript = ''
main.wait_for_unit("multi-user.target")
main.execute("seriousdb >&2 &")
main.wait_for_open_port(8000)
main.succeed("curl -sSf http://127.0.0.1:8000/docs")
main.succeed("curl -sSf -X PUT 'http://127.0.0.1:8000/db?key=hello_world_key&value=hello_world'")

response = main.succeed("curl -sSf 'http://127.0.0.1:8000/db?key=hello_world_key'")

assert "hello_world" in response


			'';
		};
	};
}
