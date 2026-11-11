# taky-gate

TAKY 2.0 guide-type hooks for Claude Code. The plugin steers risky commands onto a safe path instead of stopping work: it rewrites a dirty `git reset --hard` to stash first, moves `rm -r` targets into `~/.taky/trash` (also when the `rm` is one step of a chained command; heredoc bodies are file content and are ignored), fixes `netlify deploy` to the site in `~/.taky/routes.json`, and tells Claude the right route for merge, main push, deploy and paid calls. It never opens an approval prompt. The USER approves a whole work unit with one line such as `승인 push,deploy 2h`.

## Modes

- observe (default): records what it would have done to `~/.taky/delta/YYYYMMDD.jsonl` and changes nothing.
- guide: create the empty file `~/.taky/guide-mode`.

## Windows

`python3` is often the Microsoft Store stub on Windows. Replace `python3` with `python` (or `py -3`) in `hooks/hooks.json` before installing. Keep `-X utf8` so Korean text is read and written as UTF-8.

## Install

```
python -X utf8 tests/test_hooks.py   # expect 47/47 PASS
claude plugin marketplace add "<absolute path to this folder>"
claude plugin install taky-gate@taky-local --scope user
```
