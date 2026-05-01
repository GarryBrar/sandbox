# MacKeylocker

A small macOS utility that locks your keyboard (and optionally the Touch Bar) so you can clean your laptop without triggering random inputs. This is a quick weekend throwaway script that is expected to work on most Mac configs. Note that documentation was initially created by
GenAI. 

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
