# AUSSCHUSS – animierter Kurzfilm (Blender 4.2, prozedural)

Story und Shotliste: [STORY.md](STORY.md). Alles im Film (Modelle, Materialien, Rigs, Animation,
Kameras, Licht) entsteht per Python. Die `.blend` ist ein reines Build-Produkt.

## Aufbau

```
build.py          baut den ganzen Film → ausschuss.blend (+ sound/events.json)
lib/core.py       Primitive, prozedurale Materialien, Helfer
lib/rig.py        Puppet-Rigs (Armature + bone-parented Teile)
lib/anim.py       Keying, Walk-Cycles, Attach/Detach (Child-Of), Kamera, Sound-Events
lib/characters.py Hedda, Funke, der Erfasser, Bello, Dorfbewohner, Hühner, Drohnen-Tauben, Katze
lib/props.py      Schrott-Bibliothek, Haufen, Strommasten, Stadt, Laster, Rauch
lib/sets.py       Render-/World-Setup, Nebel, Schrottfeld + Hütte
lib/sets2.py      Werkstatt, Dorfplatz, Depot + Halle
lib/life.py       Lebendigkeit nach der Animation: Atmen/Kopfdrift (Noise-Modifier), Auto-Blinzeln,
                  Antennen-/Einrad-Wackeln, Staubpartikel, Vögel über dem Sonnenaufgang
seq/seq1..6.py    die sechs Sequenzen (Animation + Kameras + Licht pro Szene)
sound/            make_sound.py (Score als MIDI → fluidsynth, Foley synthetisch, Mix, Mastering)
tools/            Vorschau-Render, Stills, Kontaktbögen
```

Szenen `S1_…` bis `S6_…` teilen sich eine globale Zeitleiste (absolute Framenummern).
Kamerawechsel laufen über Timeline-Marker. Die Szene **FILM** reiht alle sechs im Sequencer
aneinander und legt `sound/soundtrack.wav` darunter.

## Bauen

```bash
blender -b -P build.py
```

```bash
python3 sound/make_sound.py
```

`build.py --final` stellt die Szenen direkt auf finale Qualität: 100 % Auflösung, 64 Samples,
volle Shadow-Maps und Raytracing.

## Hochwertig rendern

Ohne `--final` stehen alle Szenen auf Vorschau-Werten (25 % von 1920×1080, 1 Sample, grobe
Schatten). Für den finalen Render pro Szene `Render > Resolution %` auf 100 setzen,
EEVEE-Samples erhöhen (64–128), Shadow Resolution Scale auf 1.0 und Raytracing einschalten.
Oder einfach `blender -b -P build.py -- --final`.

Danach entweder die Szene `FILM` rendern (Sequencer, mit Ton) oder jede `S*`-Szene einzeln
als Bildsequenz nach `render/S*/` und anschließend zusammenschneiden. Der Look hängt am
Volumen-Nebel (Fog-Boxen pro Szene), an der Glare im Compositor und an AgX (Medium High
Contrast).

## Vorschau

```bash
tools/render_preview.sh
```

```bash
tools/assemble_preview.sh
```

Jedes 2. Frame wird gerendert (12 fps); `assemble_preview.sh` legt den Soundtrack darunter
→ `preview/ausschuss_preview.mp4`.

## Prüfwerkzeuge

```bash
blender -b ausschuss.blend -S S4_Chase -P tools/collide.py -- 8 preview/coll/S4.json
```

`tools/collide.py` prüft jedes 8. Frame einer Szene auf Durchdringungen. Bewegte Objekte bzw.
Gruppen (Rig samt angehängter Teile) werden per BVH gegen alles andere getestet; ausgegeben wird
die Eindringtiefe je Paar und Framebereich. Gewollte Kontakte (Figur im Fass, Netz, Käfig)
tauchen dort auch auf und müssen von Hand bewertet werden.

```bash
blender -b ausschuss.blend -P tools/shotframes.py -- preview/shotframes.txt
```

```bash
tools/shots.sh
```

Rendert je Kameraeinstellung drei Stichproben-Frames und legt Kontaktbögen nach `preview/shots/`.
