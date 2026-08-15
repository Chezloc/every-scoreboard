"""
Sends every line of a .mcfunction file to the server individually over RCON,
instead of running it as a datapack function. Useful for diagnosing cases
where /function silently fails with no server log output (e.g. a mod
intercepting command dispatch) - RCON bypasses that path entirely, since
each command is sent and executed directly, one at a time.

Requires: pip install mcrcon

Usage:
    python3 send_via_rcon.py -H <host> -P <port> -p <rcon_password> -f <path/to/file.mcfunction>

Options:
    -H, --host       RCON host (default: localhost)
    -P, --port       RCON port (default: 25575)
    -p, --password   RCON password (required)
    -f, --file       Path to the .mcfunction file to send
    -d, --delay      Delay in seconds between commands (default: 0)
    --start-line     Line number (1-indexed) to start from, for resuming (default: 1)
"""

import argparse
import sys
import time

from mcrcon import MCRcon

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-H", "--host", default="localhost", help="RCON host (default: localhost)")
parser.add_argument("-P", "--port", type=int, default=30080, help="RCON port (default: 25575)")
parser.add_argument("-p", "--password", required=True, help="RCON password")
parser.add_argument("-f", "--file", required=True, help="Path to the .mcfunction file to send")
parser.add_argument("-d", "--delay", type=float, default=0, help="Delay in seconds between commands (default: 0)")
parser.add_argument("--start-line", type=int, default=1, help="Line number (1-indexed) to start from")
args = parser.parse_args()


def main():
	with open(args.file, "r") as f:
		lines = [line.strip() for line in f if line.strip()]

	total = len(lines)
	start_index = args.start_line - 1
	if start_index < 0 or start_index >= total:
		print("--start-line %d is out of range (file has %d lines)" % (args.start_line, total))
		sys.exit(1)

	failures = []

	with MCRcon(args.host, args.password, port=args.port) as mcr:
		for i in range(start_index, total):
			command = lines[i]
			line_num = i + 1

			try:
				response = mcr.command(command)
			except Exception as e:
				failures.append((line_num, command, "connection error: %s" % e))
				print("\n[%d/%d] CONNECTION ERROR on line %d: %s" % (line_num, total, line_num, e))
				print("  command: %s" % command)
				print("  resume with: --start-line %d" % line_num)
				sys.exit(1)

			# Minecraft's command dispatcher returns an empty or non-error
			# response on success. Anything containing "error" or "Unknown"
			# (case-insensitive) is treated as a failed command.
			if response and ("error" in response.lower() or "unknown" in response.lower()
			                  or "unexpected" in response.lower()):
				failures.append((line_num, command, response))
				print("\n[%d/%d] FAILED line %d: %s" % (line_num, total, line_num, response))
				print("  command: %s" % command)

			if args.delay > 0:
				time.sleep(args.delay)

			# progress bar
			bar_width = 30
			filled = int(bar_width * (i + 1) / total)
			bar = "#" * filled + "-" * (bar_width - filled)
			sys.stdout.write("\r[" + bar + "] " + str(i + 1) + "/" + str(total) + " - line " + str(line_num) + " " * 10)
			sys.stdout.flush()

	sys.stdout.write("\n")

	sent = total - start_index
	if failures:
		print("\n%d of %d command(s) sent failed:" % (len(failures), sent))
		for line_num, command, response in failures:
			print("  line %d: %s" % (line_num, response))
			print("    -> %s" % command)
	else:
		print("\nAll %d commands executed with no error response." % sent)


if __name__ == "__main__":
	main()