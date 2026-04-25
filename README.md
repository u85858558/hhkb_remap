# hhkb_remap

Remap keys on an HHKB Hybrid Type-S on Linux. Built on `python3-evdev`: grabs the
keyboard, drops or rewrites events per a table at the top of the file, forwards
the rest through `uinput`. Originally to suppress **Fn+Esc → Power**.

## Install & run

```sh
sudo apt install python3-evdev
sudo python3 hhkb_remap.py
```

Stop with `Ctrl+C`.

## Configure

Edit `REMAP` in `hhkb_remap.py`:

```python
REMAP = {
    ecodes.KEY_POWER:    None,                  # drop
    ecodes.KEY_CAPSLOCK: ecodes.KEY_LEFTCTRL,   # rewrite
}
```

