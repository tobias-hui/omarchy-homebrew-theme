# Homebrew

An Omarchy 4 (Quattro) desktop port of luvus's **homebrew** theme: laser-lime
CRT phosphor on near-black. The palette is the authoritative set from luvus
`src/ui/theme.rs::homebrew()` — the same values jcode mirrors in
`~/.jcode/config.toml [display.colors]` — so luvus, jcode, the terminal, the
bar, and the wallpaper finally speak one green.

![Desktop preview](preview.png)

## Install

```sh
omarchy theme install https://github.com/tobias-hui/omarchy-homebrew-theme
```

Or *Install > Style > Theme* in the Omarchy menu (`Super + Space`) and paste
that URL. Backgrounds cycle with `Super + Ctrl + Space`.

## Palette

| Role | Hex | In the stream |
| --- | --- | --- |
| Background | `#081608` | The monitor's black with a green lift (luvus `base`) |
| Darker / crust | `#000000` | True void behind it (luvus `crust`) |
| Accent | `#00FF41` | The laser-lime head of the rain (luvus `accent`) |
| Foreground | `#3CFF3C` | Bright green body text (luvus `text`) |
| Muted | `#1E4C1E` | Dim trails, comments (luvus `overlay0`) |
| Selection | `#0A3A0A` | Highlighted code (luvus `sel_bg`) |
| Border | `#1A4E1A` | Window chrome (luvus `border`) |
| Red | `#FF6050` | Coral alert only — the one hot signal (luvus `coral`) |
| Yellow | `#C8FF3C` | Amber cue (luvus `amber`) |
| Cyan | `#5EFFB0` | Mint cursor/info (luvus `mint`) |
| Green | `#35E035` | Success (luvus `green`) |

Syntax stays in-world: the 16-color ANSI palette is all greens plus the
coral/amber accents. No blue nightclub, no magenta rain.

## Backgrounds

Two generated wallpapers of the same scene — "Ascension": a lone figure
stands at the base of a white-green beam of light inside an infinite field
of falling code, the rain dissolving into luminous mist over a mirror-wet
floor. Tuned per display:

- `1-ascension.jpg` (3440×1440, ultrawide) — full-height beam, silhouette
  and reflection preserved.
- `2-ascension-16x9.jpg` (1920×1080) — the same moment for a standard
  monitor.

## How the art is made

Two stages, because image models cannot set type:

1. **Plate** — the native ChatGPT image lane (Codex `imagegen` skill,
   subscription-billed) produces the atmosphere only: the black void, the pale
   green beam, the silhouette, and the reflective floor. The plates are kept in
   `tools/plates/`.
2. **Typography** — `tools/render_wallpaper.py` suppresses the plate's
   model-drawn "code" (which comes back as unreadable blobs) and renders every
   falling character deterministically with JetBrains Mono at the final
   resolution, in three depth layers with real binary and hexadecimal glyphs.

Re-render the assets with:

```sh
python tools/render_wallpaper.py \
  --plate tools/plates/ascension-ultrawide-plate.png \
  --out backgrounds/1-ascension.jpg --width 3440 --height 1440 --seed 33
python tools/render_wallpaper.py \
  --plate tools/plates/ascension-16x9-plate.png \
  --out backgrounds/2-ascension-16x9.jpg --width 1920 --height 1080 --seed 33
```

Needs `pillow` and `numpy`. The lock screen (`unlock.png`) reuses the 16:9
render.

## Applying a change to a running desktop

Editing the files is not enough. The shell keeps the decoded background in
memory keyed by path, so replacing an image in place changes nothing on screen.
Worse, `omarchy-shell` IPC fails silently when the calling shell has no session
environment: `omarchy theme bg set` then reports success while the old image
stays up.

Force the reload with the session environment set:

```sh
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export HYPRLAND_INSTANCE_SIGNATURE=$(basename "$(ls -d /run/user/$(id -u)/hypr/* | head -1)")
export WAYLAND_DISPLAY=wayland-1
omarchy theme set homebrew
omarchy theme bg set "$HOME/.config/omarchy/themes/homebrew/backgrounds/1-ascension.jpg"
```

Verify with a capture of an empty workspace rather than trusting the command's
exit code (`grim -o DP-3 out.png`); the wallpaper is hidden behind windows on
any occupied workspace.

## Credits

The color-role structure of `colors.toml` follows the layout conventions of
Omarchy's built-in themes; the wallpaper art in this repository is generated
and original to this theme.

## License

MIT — see LICENSE.
