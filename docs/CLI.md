# ClipShelf command line

`clipshelf` is both a Windows tray app and a headless command line. Every
command below works on Windows, macOS and Linux, reading and writing the same
files the tray app uses. The global option `--config PATH` points the command
at a specific `config.json` (useful for scripts and tests).

```
clipshelf [--config PATH] COMMAND [ARGS]
```

## list

Print the stored history, newest first. Pinned entries are marked with `*`.

```
clipshelf list [--limit N]
```

`--limit 0` (the default) prints everything.

## search

Search history. The default mode is fuzzy subsequence matching with bonuses
for word starts, consecutive matches, recency, pinning and copy counts. With
`--regex` the query is a regular expression (case insensitive, multiline) and
results are ordered by recency.

```
clipshelf search QUERY [--regex] [--pinned] [--limit N]
```

```bash
clipshelf search "git reb"
clipshelf search "SELECT .* FROM" --regex
clipshelf search invoice --pinned
```

## add

Record a clip without touching the clipboard. Reads stdin when `TEXT` is
omitted, which makes piping easy:

```
clipshelf add [TEXT]
```

```bash
clipshelf add "ssh deploy@example.com"
echo "$(git rev-parse HEAD)" | clipshelf add
```

## export

Export history as `json` (lossless), `markdown` (readable) or `csv`
(spreadsheet-friendly). Without `--output` the result goes to stdout.

```
clipshelf export {json,markdown,csv} [--output FILE] [--pinned-only]
```

## import

Merge a JSON or CSV export into history. Entries keep their ids, so importing
the same file twice adds nothing the second time. `--replace` discards the
current history first.

```
clipshelf import FILE [--replace]
```

The format is taken from the file extension (`.json` or `.csv`).

## stats

```
clipshelf stats
```

Prints clip and pinned counts, total copies, characters, UTF-8 bytes, the
oldest and newest clip timestamps, and the most-copied clips.

## snippets

Reusable named text with `{date}`, `{time}` and `{datetime}` placeholders.

```
clipshelf snippets list
clipshelf snippets add NAME [TEXT] [--force]
clipshelf snippets show NAME
clipshelf snippets render NAME
clipshelf snippets remove NAME
```

* `add` reads stdin when `TEXT` is omitted and refuses to overwrite an
  existing name unless `--force` is given.
* `render` fills the placeholders with the current local date/time and counts
  a use.
* Names are case insensitive, up to 64 characters of letters, digits, dots,
  dashes and underscores.

## doctor

```
clipshelf doctor
```

Prints version, Python and platform, whether the tray app is available, and
the state of the config, history and snippets files.

## once

```
clipshelf once
```

Loads and re-saves the history file, applying the configured size limit and
cleaning up malformed entries. Handy after manual edits of `history.json`.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success |
| 1 | Usage error found at runtime (missing file, bad regex, duplicate snippet) |
| 2 | Invalid command line (argparse) |