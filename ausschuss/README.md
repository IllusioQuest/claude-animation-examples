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
lib/humanparts.py modellierte Köpfe, Augen mit Iris/Lid, Hände, Stiefel, Mantel-Details, Schal, Skinning
lib/junk.py       detaillierte Schrott-Vorlagen (Fässer, Reifen, Kisten, Fernseher, Waschmaschine …)
lib/dressing.py   Set-Dressing: Hüttenverkleidung, Details, Pfützen, Gras, Steine, Wracks, animierte Details
lib/relief.py     unebener Boden außerhalb der gemessenen Laufwege
lib/pov.py        Scanner-Sicht des Erfassers (Kamera, roter Look, HUD)
lib/cloth.py      Stoff-Simulation von Heddas Mantel (mit Fallback rund um Schnitte)
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

Heddas Mantel ist eine echte Stoff-Simulation (`lib/cloth.py`). Der Build backt sie über den ganzen
Film in `blendcache_ausschuss/` neben der .blend (nicht im Repo). Wer nur die .blend kopiert, muss den
Ordner mitnehmen oder den Build einmal laufen lassen. Rund um Schnitte und beim Sitzen zeigt der Film
automatisch den mitverformten (geskinnten) Mantel, weil eine Simulation keine Teleports übersteht.

## Hochwertig rendern

Ohne `--final` stehen alle Szenen auf Vorschau-Werten (25 % von 1920×1080, 1 Sample, grobe
Schatten). Für den finalen Render pro Szene `Render > Resolution %` auf 100 setzen,
EEVEE-Samples erhöhen (64–128), Shadow Resolution Scale auf 1.0 und Raytracing einschalten.
Oder einfach `blender -b -P build.py -- --final`.

**Mantel-Simulation:** Heddas Stoffmantel liegt als Cache in `blendcache_ausschuss/` (gut 100 MB,
nicht im Repository). Nach dem Klonen bzw. Pullen einmal backen (ca. 6 Minuten), sonst rendert der
Mantel unsimuliert:

```
blender -b ausschuss.blend --python tools/bake_cloth.py
```

`build.py` macht das am Ende eines Builds selbst. Ob die Simulation sauber ist (der Stoff bleibt am
Körper), prüft:

```
blender -b ausschuss.blend --python tools/check_cloth.py
```

**Für eine Render-Farm:** eine in sich geschlossene Datei, die Mantel-Simulation steckt in der .blend
selbst (kein `blendcache_*`-Ordner nötig), alle externen Dateien sind eingepackt:

```
blender -b ausschuss.blend --python tools/pack_for_farm.py
```

Das schreibt `ausschuss_farm.blend` (die Originaldatei bleibt unverändert). Auf der Farm die Szene
`FILM` rendern, Bilder 1–6458, 24 fps.

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
