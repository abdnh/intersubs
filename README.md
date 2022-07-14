# InterSubs

_This project is work in progress and not in a usable state yet._

Interactive subtitles for mpv based on [oltodosel/interSubs](https://github.com/oltodosel/interSubs/),
[alexgtd/interSubs](https://github.com/alexgtd/interSubs),
and [fxmarty/rikai-mpv](https://github.com/fxmarty/rikai-mpv).

This is not a user script like the aforementioned projects; It's a standalone program that launches and controls mpv using the [JSON IPC](https://mpv.io/manual/master/#json-ipc).

Currently planned changes are the following:

- [x] Support for Windows (provided by [mpv.py](./src/mpv.py), wich is copied from [Anki](https://github.com/ankitects/anki/blob/main/qt/aqt/mpv.py)).
- [ ] Make the program pluggable into other programs, with support for custom click and hover actions.
