# Every Scoreboard

A tool to generate all the scoreboard objectives available in Minecraft. 
All of them, for ~~any~~ most versions.

It works by generating a datapack which will create the scoreboards for you.

# How to use

You can find 'pre-made' datapacks over [here](https://github.com/samipourquoi/every-scoreboard/tags).
If you don't find what you need, read the following section; you can skip it otherwise.

## 'Compiling'

First of all, clone the repository: 
```shell script
$ git clone https://github.com/Chezloc/every-scoreboard.git
$ cd every-scoreboard
```

Install the dependencies with this command; 
make sure you have [pip](https://pip.pypa.io/en/stable/installing/) installed. 
```shell script
$ pip install -r requirements.txt
```

To 'compile' the datapacks, run the following:
```shell script
# For 26.2
$ python3 scripts/create.py --mcversion="26.2" -c
```

The `-c` flag will add the [custom objectives](https://minecraft.wiki/w/Statistics#List_of_custom_statistic_names)
to the datapack. Be careful however! It is made for the latest version(s) of the game only.
You will probably need to modify the resulting `mcfunction` files at the end if you
do it for an older version of Minecraft.

For versions 1.20 and up, block/item/entity data is fetched automatically at runtime from
[PrismarineJS/minecraft-data](https://github.com/PrismarineJS/minecraft-data) and cached locally
under `scripts/mcdata/<version>/`, so you don't need to update anything by hand when a new
Minecraft version comes out — just run `create.py` with the new `--mcversion`. If PrismarineJS
doesn't have the exact version yet, the closest older version it does have is used instead,
with any gap filled in from a hand-written patch in `scripts/mcdata/patches/<version>.json` (only
needed for very recent releases PrismarineJS hasn't caught up to). Versions below 1.20 still use
the `minecraft_data` pip package.

The resulting files will end up at `datapacks/every-scoreboard-<version>` and `dictionaries/dictionary-<version>.json`.
We will come back to the second file later on.

## Running the datapack

Once you have the datapack ready, move it over your world's datapacks folder. Log on to your world and enter the following commands:
```
/reload
/function every-scoreboard:create
```

And here you're all set! If you wish to get rid of all of these objectives, run:
```
/function every-scoreboard:delete
```

See the naming convention over in the next section. 

Note that the scoreboard names won't change between versions of the game.
That means you can have your world in 1.15.2 with that datapack, then updates your world to 1.16.2, run the datapack
for that version again, and you will keep your scoreboards from 1.15.2, with the new ones. 

## Naming convention

The scoreboards are name accordingly:
- `m-<block>` Mined blocks
- `u-<item>` Used items
- `c-<item>` Crafted items
- `b-<item>` Broken tools
- `p-<item>` Picked up items
- `d-<item>` Dropped items
- `k-<mob>` Killed mobs
- `kb-<mob>` Killed by mob
- `z-<stats>` Custom (find all the possible `stats` over [here](https://minecraft.wiki/w/Statistics#List_of_custom_statistic_names))

### ⚠️ Important note ⚠️

Scoreboards name can't be longer than 16 characters! To solve that issue, the program truncates the names which are too
long, and replace their end with a series of number. 

If you wish to create your own tool solving that issue, you can find
a JSON of key-value's (fullname to truncated name) in the generated `dictionaries/dictionary-<version>.json` file.

# 'Recover' your old stats

What if you have already started your world without all of these fancy scoreboards? No problem!
You can actually take the statistics from your world and convert them to commands, which will update the
objectives to their actual value.

To do so, run the `update.py` script like so:
```shell script
$ python3 scripts/update.py -D="./dictionaries/dictionary-26.2.json" -S="path/to/stats"
```

- the `-D` flag will set the path of the dictionary (needed to convert full name scoreboards to their truncated form).
- the `-S` flag will set the path of the stats folder. It's usually found at `.minecraft/saves/<world>/stats`, or
`<server>/world/players/stats`. It should contain plenty of JSON files.

There are 5 __optional__ flags:
- `--usercache="<path>"` (or `-u`) points at your server's `usercache.json` (found at the root of
  the server, alongside the `world` folder) to resolve player UUIDs to usernames locally, without
  calling Mojang's API. Recommended: it's instant and works for every player already in the cache.
  Any UUID not found there falls back to a live lookup against Mojang's session server.
- `--dig="<name>"` sets the name of the general dig scoreboard (counts all blocks mined)
- `--picks="<name>"` sets the name of all type pick uses (netherite, diamond, iron...)
- `--shovels="<name>"` sets the name of all type shovel uses 
- `--axes="<name>"` sets the name of all type axe uses

The program will generate a datapack at `datapacks/every-scoreboard-<version>`. Make sure you have a backup of your
world *just in case* something goes wrong. Drag it to your world's datapacks folder,
and enter these commands:
```
/reload
/function #every-scoreboard:update
```

# Credits
Contact me on Discord `chezloc`.

Feel free to contact me if you need any help 😀