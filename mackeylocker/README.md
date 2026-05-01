# MacKeylocker

A small macOS utility that locks your keyboard (and Touch Bar, if you have one). Originally built for cleaning your keys without firing off random inputs, but useful for anything where you want to keep your Mac awake and active without accidentally triggering shortcuts — presentations, reading, monitoring a process, etc. Quick weekend script, works on most Mac configs.

## Install

Requires Python 3.9+ and the system Tkinter. Install the one dependency:

```
pip install pyobjc-framework-Quartz
```

Or install the whole thing:

```
make install
```

You also need to grant **Accessibility** permissions to your terminal:
System Settings > Privacy & Security > Accessibility.

## Usage

```
sudo python3 mackeylocker.py
```

Or just `make run`.

Root is needed to kill the Touch Bar processes. If you don't have a Touch Bar (or don't care about locking it), skip sudo:

```
python3 mackeylocker.py --no-touchbar
```

Auto-unlock after a set time:

```
sudo python3 mackeylocker.py --timeout 120
```

## Unlocking

Three ways to unlock:

- Click the **Unlock** button in the overlay window
- Hold all four modifier keys at once (Cmd + Opt + Ctrl + Shift)
- Triple-click the mouse

## License

MIT
