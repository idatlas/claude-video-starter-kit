# Art prompts: "How the pipeline works" (paper-cutout explainer)

Made by Claude from `script.txt`. Paste the **style block** at the start of every prompt so the
images match. Save each image as the file name given, into `projects/<name>/art/`.

## Style block (goes at the start of every prompt)

> Flat paper-cutout illustration, like shapes cut from colored card stock and layered. Each piece
> has a thin white paper edge and a slightly rough cut. Subtle paper texture on each piece. Bold,
> simple shapes, no fine detail, no outlines in black. Palette only: navy #1F2430, orange #FF7A45,
> teal #2FA4A0, blue #4D7CFF, yellow #FFC94D, pink #F28CA0, cream #EADBC0. One object only,
> centered, filling about 70% of the frame, seen straight on. Plain solid light gray background
> (#D9D9D9) with nothing else on it, no shadow on the background. No text, no letters, no logos.

## Images

| # | File name | Prompt (after the style block) |
|---|---|---|
| 1 | `laptop.png` | An open laptop seen from the front. On its cream screen, a simple four-pointed orange star. |
| 2 | `bubble.png` | A rounded blue speech bubble with a tail at the lower left, with three short white lines inside, like text. |
| 3 | `plan.png` | A brown clipboard holding a cream sheet with four orange check marks, each followed by a short navy line. |
| 4 | `mic.png` | A studio microphone with a yellow rounded head and a navy stand. |
| 5 | `film.png` | A movie clapperboard, navy with white diagonal stripes on the clapper, slightly open. |
| 6 | `palette.png` | An artist's cream paint palette with orange, blue, teal and pink paint dots and one paintbrush. |
| 7 | `frames.png` | Three picture frames stacked and offset, teal at the back, blue, then orange at the front, each with a tiny mountain and sun. |
| 8 | `preview.png` | A navy computer monitor showing a grid of six colored squares, with an orange magnifying glass over one corner. |
| 9 | `gear.png` | A single teal gear with eight square teeth and a cream hole in the middle. |
| 10 | `video.png` | A rounded orange rectangle with a white play triangle and a thin progress bar along the bottom. |

## After generating

1. Look at all ten together (ask Claude for a sheet). Regenerate any that don't match the others.
2. Remove the backgrounds: `scripts/cutout.py projects/<name>/art`. This writes `<name>-cut.png`.
3. If an image has a small logo or sparkle in a corner, crop it out before step 2.
4. Point the project's layers at the `-cut.png` files.
