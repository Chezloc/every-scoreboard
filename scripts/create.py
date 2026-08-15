description = """
Creates a datapack which will add every scoreboard in the game.
By samipourquoi & Chezloc
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
# through 26.2. Sourced from Nixinova/pack-format (github.com/Nixinova/pack-format,
# an actively maintained table cross-referenced against Mojang's own
# version.json files) for everything through 26.1, and from minecraft.wiki's
# 26.2 infobox for 26.2 specifically (not yet in pack-format's shipped data
# as of this writing). NOTE: these are DATA pack formats, not resource pack
# formats - the two diverge for the same version (e.g. 1.21.11 is resource
# format 75 but data format 94.1), so don't substitute one for the other.
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

custom_version = "1.16+"

# Minecraft 1.21 (data pack format 48) renamed data/<namespace>/functions/ to
# data/<namespace>/function/ (singular), along with several other folders.
# This only affects the folder name, not the .mcfunction file contents/names.
FUNCTION_FOLDER_RENAME_FORMAT = 48


def function_folder_name(pack_major):
	return "function" if pack_major >= FUNCTION_FOLDER_RENAME_FORMAT else "functions"

import argparse
import json
import os
import requests

# Arguments
parser = argparse.ArgumentParser(description=description)
parser.add_argument("-mc", "--mcversion", help="set the Minecraft version the scoreboards will be for")
parser.add_argument("-c", "--custom", help="add the 'custom' objectives, from the latest version of the game",
                    action="store_true")
args = parser.parse_args()


def main():
	if args.custom:
		print(
			"\033[91mWARNING! The --custom flag is made for the %s version(s).\nIt will not work without modifying the generated mcfunction files!\033[0m" % custom_version)

	minecraft_version = args.mcversion
	blocks, items, entities = load_registries(minecraft_version)
	custom_stats = json.loads(open("./scripts/assets/custom_stats.json", "r").read()) if args.custom else {}

	# Creates the objective names from the registries
	mined = make(blocks, "m", "minecraft.mined", "%s Mined")
	used = make(items, "u", "minecraft.used", "%s Used")
	crafted = make(items, "c", "minecraft.crafted", "%s Crafted")
	broken = make(items, "b", "minecraft.broken", "%s Broken")
	dropped = make(items, "d", "minecraft.dropped", "%s Dropped")
	picked_up = make(items, "p", "minecraft.picked_up", "%s Picked up")
	killed = make(entities, "k", "minecraft.killed", "%s Killed")
	killed_by = make(entities, "kb", "minecraft.killed_by", "Killed by %s")
	custom = make(custom_stats, "z", "minecraft.custom", "%s")

	# Data pack format and folder-naming convention for this version
	if minecraft_version not in pack_formats:
		raise ValueError("No pack_format known for version '%s'. Add it to pack_formats." % minecraft_version)
	pack_major, pack_minor = pack_formats[minecraft_version]
	function_dir = function_folder_name(pack_major)

	# Creates the required folders
	os.makedirs("./dictionaries/", exist_ok=True)
	os.makedirs("./datapacks/every-scoreboard-" + minecraft_version + "/data/every-scoreboard/" + function_dir + "/",
	            exist_ok=True)

	# Creates the pack.mcmeta file
	pack_mcmeta = open("./datapacks/every-scoreboard-" + minecraft_version + "/pack.mcmeta", "w+")
	if pack_major >= 82:  # 25w31a+ uses min_format/max_format instead of a single pack_format
		# max_format uses a generous forward-compatible ceiling, same convention
		# widely used by other datapacks (see e.g. min_format: [84, 0], max_format: [999, 0])
		pack_mcmeta.write(pack_modern % (minecraft_version, pack_major, pack_minor, 999, 0))
	else:
		pack_mcmeta.write(pack_legacy % (minecraft_version, pack_major))
	pack_mcmeta.close()

	# Creates the json file
	dictionary = open("./dictionaries/dictionary-" + minecraft_version + ".json", "w+")
	dictionary.write(json.dumps({**mined["dictionary"], **used["dictionary"], **crafted["dictionary"],
	                             **broken["dictionary"], **dropped["dictionary"], **picked_up["dictionary"],
	                             **killed["dictionary"], **killed_by["dictionary"], **custom["dictionary"]}))
	dictionary.close()
	print("Wrote the dictionary file")

	# Creates the commands, which will register the objectives
	fin_create_commands = create_commands(mined) + create_commands(used) + create_commands(crafted) + create_commands(
		broken) + create_commands(dropped) + create_commands(picked_up) + create_commands(killed) + create_commands(
		killed_by) + create_commands(custom)
	fin_delete_commands = delete_commands(mined) + delete_commands(used) + delete_commands(crafted) + delete_commands(
		broken) + delete_commands(dropped) + delete_commands(picked_up) + delete_commands(killed) + delete_commands(
		killed_by) + delete_commands(custom)

	# Writes to a file
	create_mcfunction = open(
		"./datapacks/every-scoreboard-" + minecraft_version + "/data/every-scoreboard/" + function_dir + "/create.mcfunction",
		"w+")
	create_mcfunction.write("\n".join(fin_create_commands))
	create_mcfunction.close()
	print("Wrote the create.mcfunction file")

	# Writes the remove commands
	delete_mcfunction = open(
		"./datapacks/every-scoreboard-" + minecraft_version + "/data/every-scoreboard/" + function_dir + "/delete.mcfunction",
		"w+")
	delete_mcfunction.write("\n".join(fin_delete_commands))
	delete_mcfunction.close()
	print("Wrote the delete.mcfunction file")

	print("Wrote the datapack")


# Minecraft versions >= 1.20 aren't supported by the abandoned minecraft_data
# PyPI package, so for those we fetch blocks.json/items.json/entities.json
# straight from PrismarineJS/minecraft-data at runtime (falling back to
# minecraft_data for older versions it still knows). Fetched data is cached
# under scripts/mcdata/<version>/ so repeat runs don't re-download.
#
# If PrismarineJS doesn't have the exact requested version yet (e.g. a
# brand-new release), we fall back to its newest tracked version and layer
# on a hand-written patch (scripts/mcdata/patches/<version>.json) with the
# specific new registry entries added since then, sourced from
# minecraft.wiki's version changelog. Delete the patch and rerun once
# PrismarineJS catches up - it'll fetch the real data instead.
MCDATA_MIN_VERSION = (1, 20)  # below this, use the minecraft_data pip package instead
MCDATA_RAW_URL = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data/pc/"


def version_tuple(version_string):
	# "1.21.11" -> (1, 21, 11), "26.1" -> (26, 1)
	return tuple(int(part) for part in version_string.split("."))


def uses_mcdata(minecraft_version):
	try:
		return version_tuple(minecraft_version) >= MCDATA_MIN_VERSION
	except ValueError:
		return False  # snapshot names etc. - not handled here, fall through to minecraft_data


def fetch_json(url):
	response = requests.get(url)
	if response.status_code == 404:
		return None
	response.raise_for_status()
	return response.json()


def mcdata_versions_list():
	# PC versions in ascending (chronological) order
	return fetch_json(MCDATA_RAW_URL + "common/versions.json")


def nearest_available_version(minecraft_version, versions):
	# PrismarineJS's manifest can list a version whose folder is an
	# incomplete diff (e.g. 1.20.4 only has blocks.json, reusing 1.20.3's
	# items/entities) - load_mcdata_registries returns None for those.
	# Walk backward through the version list to the closest version with
	# a complete blocks/items/entities set. If the requested version isn't
	# in the list at all (e.g. it's newer than anything tracked), start
	# from the newest tracked version instead.
	try:
		start_index = versions.index(minecraft_version)
	except ValueError:
		start_index = len(versions) - 1

	for i in range(start_index, -1, -1):
		if load_mcdata_registries(versions[i]) is not None:
			return versions[i]

	return None


def load_mcdata_registries(minecraft_version):
	cache_dir = "./scripts/mcdata/" + minecraft_version + "/"
	cached = all(os.path.exists(cache_dir + f) for f in ("blocks.json", "items.json", "entities.json"))

	if cached:
		blocks = json.loads(open(cache_dir + "blocks.json").read())
		items = json.loads(open(cache_dir + "items.json").read())
		entities = json.loads(open(cache_dir + "entities.json").read())
		return blocks, items, entities

	blocks = fetch_json(MCDATA_RAW_URL + minecraft_version + "/blocks.json")
	items = fetch_json(MCDATA_RAW_URL + minecraft_version + "/items.json")
	entities = fetch_json(MCDATA_RAW_URL + minecraft_version + "/entities.json")
	if blocks is None or items is None or entities is None:
		return None  # PrismarineJS doesn't have complete data for this version - don't cache a failure

	os.makedirs(cache_dir, exist_ok=True)
	open(cache_dir + "blocks.json", "w+").write(json.dumps(blocks))
	open(cache_dir + "items.json", "w+").write(json.dumps(items))
	open(cache_dir + "entities.json", "w+").write(json.dumps(entities))

	return blocks, items, entities


def load_registries(minecraft_version):
	if not uses_mcdata(minecraft_version):
		# noinspection PyCallingNonCallable
		import minecraft_data
		data = minecraft_data(minecraft_version)
		return data.blocks, data.items, data.entities_name

	result = load_mcdata_registries(minecraft_version)
	patch_version = minecraft_version

	if result is None:
		versions = mcdata_versions_list()
		fallback_version = nearest_available_version(minecraft_version, versions)
		if fallback_version is None:
			raise ValueError("Could not find any usable PrismarineJS data at or before '%s'" % minecraft_version)
		print("PrismarineJS/minecraft-data has no complete data for '%s', falling back to '%s'"
		      % (minecraft_version, fallback_version))
		result = load_mcdata_registries(fallback_version)

	blocks, items, entities = (list_to_dict(r) for r in result)

	patch_path = "./scripts/mcdata/patches/" + patch_version + ".json"
	if os.path.exists(patch_path):
		patch = json.loads(open(patch_path).read())
		extend_registry(blocks, patch["blocks"])
		extend_registry(items, patch["items"])
		extend_registry(entities, patch["entities"])

	return blocks, items, entities


def extend_registry(registry, new_entries):
	next_id = max(registry.keys(), default=-1) + 1
	for entry in new_entries:
		registry[next_id] = entry
		next_id += 1


def list_to_dict(registry_list):
	return {i: entry for i, entry in enumerate(registry_list)}


def make(registry, prefix, criterion_namespace, lang):
	dictionary = {}
	criteria = {}
	display_names = {}
	for i in registry:
		full_name = prefix + "-" + registry[i]["name"]
		truncated_name = full_name
		if len(full_name) > 16:
			index = "+" + gen_id(full_name)
			truncated_name = full_name[:16 - len(index)] + index

		dictionary[full_name] = truncated_name
		criteria[full_name] = criterion_namespace + ":" + "minecraft." + registry[i]["name"]
		display_names[full_name] = lang % registry[i]["displayName"]

	return {
		"dictionary": dictionary,
		"criteria": criteria,
		"display_names": display_names
	}


def create_commands(data):
	commands = []
	for i in data["dictionary"]:
		commands.append("scoreboard objectives add " +
		                data["dictionary"][i] + " " +
		                data["criteria"][i] + " " +
		                "\"" + data["display_names"][i] + "\"")

	return commands


def delete_commands(data):
	commands = []
	for i in data["dictionary"]:
		commands.append("scoreboard objectives remove " + data["dictionary"][i])

	return commands


def gen_id(string):
	sum = 0
	for i in string:
		sum = (sum + (ord(i) & 0xF)) ^ (ord(i) * 5)
	return str(sum)


if __name__ == "__main__":
	main()