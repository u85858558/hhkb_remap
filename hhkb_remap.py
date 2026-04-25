import selectors
import signal
import sys
import evdev
from evdev import ecodes, UInput

HHKB_NAME_PREFIX = "PFU Limited HHKB-Hybrid"

REMAP = {
    ecodes.KEY_POWER: None,
    # ecodes.KEY_CAPSLOCK:  ecodes.KEY_LEFTCTRL,
    # ecodes.KEY_RIGHTALT:  ecodes.KEY_RIGHTMETA,
    # ecodes.KEY_INSERT:    None,
}


def select_devices():
    sources = set(REMAP.keys())
    chosen = []
    for path in evdev.list_devices():
        d = evdev.InputDevice(path)
        if not d.name.startswith(HHKB_NAME_PREFIX):
            d.close()
            continue
        keys = set(d.capabilities().get(ecodes.EV_KEY, []))
        if keys & sources:
            chosen.append(d)
        else:
            d.close()
    if not chosen:
        sys.exit("no HHKB device exposes any of the keys in REMAP")
    return chosen


def mirror_caps(dev):
    caps = dev.capabilities()
    caps.pop(ecodes.EV_SYN, None)
    if ecodes.EV_KEY in caps:
        keys = set(caps[ecodes.EV_KEY])
        keys -= {src for src, tgt in REMAP.items() if tgt is None}
        keys |= {tgt for tgt in REMAP.values() if tgt is not None}
        caps[ecodes.EV_KEY] = sorted(keys)
    return caps


def main():
    devs = select_devices()
    mirrors = []

    def cleanup(*_):
        for d, ui in mirrors:
            try:
                d.ungrab()
            except Exception:
                pass
            ui.close()
            d.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    for d in devs:
        ui = UInput(mirror_caps(d), name=f"{d.name} (remapped)")
        d.grab()
        mirrors.append((d, ui))
        print(f"grabbing {d.path}  ({d.name!r})", flush=True)

    sel = selectors.DefaultSelector()
    for d, ui in mirrors:
        sel.register(d.fd, selectors.EVENT_READ, (d, ui))

    try:
        while True:
            for key, _ in sel.select():
                d, ui = key.data
                try:
                    events = list(d.read())
                except BlockingIOError:
                    continue
                for ev in events:
                    if ev.type == ecodes.EV_KEY and ev.code in REMAP:
                        tgt = REMAP[ev.code]
                        if tgt is None:
                            continue
                        ui.write(ecodes.EV_KEY, tgt, ev.value)
                    else:
                        ui.write_event(ev)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
