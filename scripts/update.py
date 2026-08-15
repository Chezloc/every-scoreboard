description = """
Converts statistics to objective values.
by samipourquoi & Chezloc
"""

pack_legacy = """{
    "pack": {
        "description": "Every scoreboard, for Minecraft %s!",
        "pack_format": %d
    }
}
"""

pack_modern = """{
    "pack": {
        "description": "Every scoreboard, for Minecraft %s!",
        "min_format": [%d, %d],
        "max_format": [%d, %d]
    }
}
"""

# Data pack format numbers (major, minor), covering every release from 1.16
# through 26.2. Keep in sync with create.py - see that file for sourcing notes.
pack_formats = {
	"1.16": (5, 0),
	"1.16.1": (5, 0),
	"1.16.2": (6, 0),
	"1.16.3": (6, 0),
	"1.16.4": (6, 0),
	"1.16.5": (6, 0),
	"1.17": (7, 0),
	"1.17.1": (7, 0),
	"1.18": (8, 0),
	"1.18.1": (8, 0),
	"1.18.2": (9, 0),
	"1.19": (10, 0),
	"1.19.1": (10, 0),
	"1.19.2": (10, 0),
	"1.19.3": (10, 0),
	"1.19.4": (12, 0),
	"1.20": (15, 0),
	"1.20.1": (15, 0),
	"1.20.2": (18, 0),
	"1.20.3": (26, 0),
	"1.20.4": (26, 0),
	"1.20.5": (41, 0),
	"1.20.6": (41, 0),
	"1.21": (48, 0),
	"1.21.1": (48, 0),
	"1.21.2": (57, 0),
	"1.21.3": (57, 0),
	"1.21.4": (61, 0),
	"1.21.5": (71, 0),
	"1.21.6": (80, 0),
	"1.21.7": (81, 0),
	"1.21.8": (81, 0),
	"1.21.9": (88, 0),
	"1.21.10": (88, 0),
	"1.21.11": (94, 1),
	"26.1": (101, 1),
	"26.2": (107, 1),
}

tag_text = """{
	"values": [
		%s
	]
}"""

import argparse
import requests
import json
import os
import sys
import time

# Arguments
parser = argparse.ArgumentParser(description=description)
parser.add_argument("-S", "--statslocation", help="set the path from where the program will get the statistics")
parser.add_argument("-D", "--dictionary", help="set the path from where the program will get the objectives dictionary")
parser.add_argument("-d", "--dig", required=False, help="(optional) set the name of the total dig objective")
parser.add_argument("-p", "--picks", required=False, help="(optional) set the name of the total pick uses objective")
parser.add_argument("-s", "--shovels", required=False,
                    help="(optional) set the name of the total shovel uses objective")
parser.add_argument("-a", "--axes", required=False, help="(optional) set the name of the axe uses objective")
parser.add_argument("-u", "--usercache", required=False,
                    help="(optional) path to the server's usercache.json, used to resolve UUIDs to usernames "
                         "locally instead of querying Mojang's API")
args = parser.parse_args()


def main():
	minecraft_version = args.dictionary.split("/")[-1][11:-5]

	# Create required files/folders
	os.makedirs("./datapacks/every-scoreboard-" + minecraft_version + "/data/every-scoreboard/functions/",
	            exist_ok=True)
	os.makedirs("./datapacks/every-scoreboard-" + minecraft_version + "/data/every-scoreboard/tags/functions",
	            exist_ok=True)
	# Creates the pack.mcmeta file
	if minecraft_version not in pack_formats:
		raise ValueError("No pack_format known for version '%s'. Add it to pack_formats." % minecraft_version)
	pack_major, pack_minor = pack_formats[minecraft_version]
	pack_mcmeta = open("./datapacks/every-scoreboard-" + minecraft_version + "/pack.mcmeta", "w+")
	if pack_major >= 82:  # 25w31a+ uses min_format/max_format instead of a single pack_format
		pack_mcmeta.write(pack_modern % (minecraft_version, pack_major, pack_minor, 999, 0))
	else:
		pack_mcmeta.write(pack_legacy % (minecraft_version, pack_major))
	pack_mcmeta.close()

	# Reads dictionary
	dictionary_file = open(args.dictionary, "r")
	dictionary = json.load(dictionary_file)
	dictionary_file.close()

	# Reads usercache.json for local UUID->username lookups, if provided
	usercache = {}
	if args.usercache:
		usercache_file = open(args.usercache, "r")
		for entry in json.load(usercache_file):
			usercache[entry["uuid"].replace("-", "")] = entry["name"]
		usercache_file.close()

	location = args.statslocation
	files = os.listdir(location)

	done = 0
	commands = ""
	for uuid in files:
		done += 1

		# If ever there is a random OS file
		if uuid[36:] != ".json":
			continue

		file = open(location + "/" + uuid, "r")
		try:
			stats = json.load(file)["stats"]
		except:
			continue

		file.close()

		mined = stats_to_commands(stats["minecraft:mined"] if "minecraft:mined" in stats else {}, "m-", dictionary)
		used = stats_to_commands(stats["minecraft:used"] if "minecraft:used" in stats else {}, "u-", dictionary)
		crafted = stats_to_commands(stats["minecraft:crafted"] if "minecraft:crafted" in stats else {}, "c-",
		                            dictionary)
		broken = stats_to_commands(stats["minecraft:broken"] if "minecraft:broken" in stats else {}, "b-", dictionary)
		picked_up = stats_to_commands(stats["minecraft:picked_up"] if "minecraft:picked_up" in stats else {}, "p-",
		                              dictionary)
		dropped = stats_to_commands(stats["minecraft:dropped"] if "minecraft:dropped" in stats else {}, "d-",
		                            dictionary)
		killed = stats_to_commands(stats["minecraft:killed"] if "minecraft:killed" in stats else {}, "k-", dictionary)
		killed_by = stats_to_commands(stats["minecraft:killed_by"] if "minecraft:killed_by" in stats else {}, "kb-",
		                              dictionary)
		custom = stats_to_commands(stats["minecraft:custom"] if "minecraft:custom" in stats else {}, "z-", dictionary)

		# Random check to see if it's a fake player or not
		if len(mined) < 10:
			continue

		username = get_username(uuid[:36], usercache)
		commands += str.join("\n",mined + used + crafted + broken + picked_up + dropped + killed + killed_by + custom).replace("%s", username) + "\n"

		# Prints a progress bar that updates in place
		bar_width = 30
		filled = int(bar_width * done / len(files))
		bar = "#" * filled + "-" * (bar_width - filled)
		sys.stdout.write("\r[" + bar + "] " + str(done) + "/" + str(len(files)) + " - " + username + " " * 20)
		sys.stdout.flush()

	sys.stdout.write("\n")

	# It's messy code but it works ig
	i = 0
	commands = commands.split("\n")
	function_names = []
	has_ran_once = True
	max_length = 60000
	while has_ran_once or len(commands) > 0:
		update_mcfunction = open(
			"./datapacks/every-scoreboard-" + minecraft_version + "/data/every-scoreboard/functions/update" + str(i) + ".mcfunction",
			"w+")
		update_mcfunction.write(str.join("\n", commands[:max_length]))
		update_mcfunction.close()
		function_names.append("\"every-scoreboard:update" + str(i) + "\"")
		i += 1
		commands = commands[max_length:]

		if has_ran_once:
			has_ran_once = False

	# Creates the tag to run all of these function files
	tag = open(
			"./datapacks/every-scoreboard-" + minecraft_version + "/data/every-scoreboard/tags/functions/update.json",
			"w+")
	tag.write(tag_text % str.join(",\n\t\t", function_names))
	tag.close()




def stats_to_commands(stats, prefix, dictionary):
	commands = []
	dig = 0
	picks = 0
	shovels = 0
	axes = 0
	for i in stats:
		try:
			# Custom dig scoreboards
			if prefix == "m-":
				dig += stats[i]
			if prefix == "u-":
				if "pickaxe" in i[10:]:
					picks += stats[i]
				if "shovel" in i[10:]:
					shovels += stats[i]
				if "_axe" in i[10:]:
					axes += stats[i]

			commands.append("scoreboard players set %s " + dictionary[prefix + i[10:]] + " " + str(stats[i]))
		except:
			()

	# Custom dig scoreboards
	if prefix == "m-" and args.dig != None:
		commands.append("scoreboard players set %s " + args.dig + " " + str(dig))
	if prefix == "u-" and args.picks != None:
		commands.append("scoreboard players set %s " + args.picks + " " + str(picks))
	if prefix == "u-" and args.shovels != None:
		commands.append("scoreboard players set %s " + args.shovels + " " + str(shovels))
	if prefix == "u-" and args.axes != None:
		commands.append("scoreboard players set %s " + args.axes + " " + str(axes))

	return commands


def get_username(uuid, usercache=None, retries_left=5):
	# Removes the '-'
	uuid = uuid.replace("-", "")

	# Check the local usercache first, if one was provided - avoids hitting
	# Mojang's API (and its rate limit) entirely for players already cached
	if usercache and uuid in usercache:
		return usercache[uuid]

	# Requests the player's current profile from Mojang's session server.
	# (api.mojang.com/user/profiles/<uuid>/names was deprecated and removed
	# by Mojang in September 2022 - this replaces it.)
	response = requests.get("https://sessionserver.mojang.com/session/minecraft/profile/" + uuid)

	if response.status_code == 200:
		try:
			return response.json()["name"]
		except (KeyError, ValueError):
			pass  # unexpected shape - fall through to retry/give-up handling below

	if response.status_code == 404:
		# no such profile (e.g. an offline-mode/fake UUID) - not going to
		# start working on retry, so don't loop forever
		return uuid

	if retries_left <= 0:
		# sessionserver is rate-limited to one request/minute per profile;
		# after several attempts, assume something's genuinely wrong rather
		# than retrying indefinitely
		return uuid

	time.sleep(10)
	return get_username(uuid, usercache, retries_left - 1)


if __name__ == "__main__":
	main()