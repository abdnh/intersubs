# InterSubs

_This project is work in progress and may not be in a usable state yet._

Interactive subtitles for mpv based on [oltodosel/interSubs](https://github.com/oltodosel/interSubs/),
[alexgtd/interSubs](https://github.com/alexgtd/interSubs),
and [fxmarty/rikai-mpv](https://github.com/fxmarty/rikai-mpv).

This is not a user script like the aforementioned projects; It's a standalone program that launches and controls mpv using the [JSON IPC](https://mpv.io/manual/master/#json-ipc).

Currently planned changes are the following:

- [x] Support for Windows (provided by [mpv.py](./src/mpv.py), which is copied from [Anki](https://github.com/ankitects/anki/blob/main/qt/aqt/mpv.py)).
- [x] Make the program pluggable into other programs, with support for custom click and hover actions. See an example of how this is used in my fork of the [Create subs2srs cards with mpv](https://github.com/abdnh/create-subs2srs-cards-with-mpv-video-player/tree/intersubs) add-on.
- [ ] Support a number of dictionaries by default. Contributions welcome!
