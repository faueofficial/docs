# Image detector

**Stage:** MVP · **Owner:** backend · **Relates to:** [`pii-handling.md`](../../10-architecture/pii-handling.md), [ADR 0013](../../80-adr/0013-server-authoritative-image-pii-pipeline.md)

The detector is what lets the PII pipeline run outside `local`. It is built to
be small, because the API image carries it and every upload pays for it.

## What it is

`app/modules/media/light_detector.py`, on `onnxruntime`, with three models and no
other dependencies beyond numpy and Pillow.

| Piece | Size | Role |
|---|---|---|
| `onnxruntime` (CPU) | 24 MB wheel | Runs both models |
| YuNet `face_detection_yunet_2023mar.onnx` | 0.23 MB | Faces, boxes grown by 12% then filled |
| PP-OCRv4 `text_detection_ppocrv4.onnx` | 4.7 MB | Where text is (detection only, no reading) |
| `image-safety-classifier-xs` (fp16) | 7.1 MB | Refuses NSFW and graphic content |

About **36 MB** added to the image, against roughly 150 MB of OpenCV and a
Tesseract binary plus 350 MB for the `open_clip` safety model in the earlier plan.
Models are fetched at build time by `scripts/fetch_media_models.py` and checked
against pinned SHA-256 digests; a changed file fails the build.

Text is **detected, not read**. Redaction needs to know where text is, so only
the detection half of OCR runs. It over-redacts: lettering on a garment is
blanked along with an address label. That is the safe direction.

## What it costs

Measured on the golden set (82 images, 400 to 2,400 px) as CPU seconds on one
thread, so a busy machine does not distort it:

| Stage | Median | 95th percentile |
|---|---|---|
| Face detection | 0.25 s | 0.46 s |
| Text detection, longest side 960 (default) | 1.84 s | 2.52 s |
| Safety classification | 0.33 s | 0.44 s |
| **Per image** | **about 2.4 s** | about 3.4 s |

Text detection is the cost. At 736 px it is 1.27 s but misses small signs
(see below); at 1280 px it is 2.3 s with a 7 s tail and gains nothing over 960.
`MEDIA_TEXT_MAX_SIDE` is the knob, and like the safety threshold it can be changed from the console
(Settings) without a deploy.

Peak resident memory for a process with all three models loaded was about
220 MB.

## Safety classification

`OwenElliott/image-safety-classifier-xs`: a SwiftFormer-XS fine-tune, **MIT**,
3.0 M parameters, classes `NSFL` (graphic), `NSFW`, `SFW`, published accuracy
97.8%. The published ONNX is 13.1 MB; the build converts it to fp16 (7.1 MB,
largest output difference from fp32 0.0007 on the sample set). Dynamic int8
quantisation was tried and the published graph does not survive it, so fp16 is
the smallest form that works.

| | |
|---|---|
| CPU time | about 0.4 s per image, one thread, including resizing |
| Input | the whole frame resized to 224 x 224 (not centre-cropped: a crop can be walked around by framing) |
| Rule | refuse when `NSFW` or `NSFL` probability is at or above `MEDIA_SAFETY_THRESHOLD` (default 0.7) |
| Result | `rejected`, reason `unsafe_content`, nothing stored |

See "Measured" below for how it behaves on real fashion images and what could
not be measured.

Not covered, and not claimed:

- **Minors** are not detected. That is a separate and harder problem and needs
  its own decision.
- **Non-apparel** images (`not_apparel` in the contract) are not rejected.
- Anything the model was not trained on.

`MEDIA_SAFETY_REQUIRED=true` makes the service refuse to start without the
model; without it, a missing model means uploads are accepted and recorded as
`safety_verdict = 'unchecked'`, never `safe`.

## Measured

The golden set is `tests/golden/pii_images`: 82 images from Wikimedia Commons
(CC BY, CC BY-SA, CC0, public domain), chosen to look like what FAUE receives:
Nigerian and West African fashion with faces, flat fabric, scenes with printed
text, crowds, and swimwear as a hard negative. `scripts/build_golden_set.py`
downloads them; `manifest.json` holds the labels (visual review) and the licence
and author of every image. `scripts/eval_detector.py` measures, and
`tests/golden/test_pii_golden.py` holds the floors.

Labels are counts and presence, not boxes, so recall is count-based.

| Measure | Result | Target in `pii-handling.md` |
|---|---|---|
| Large, clearly visible faces found | **74 of 76 (97.4%)**; 41 of 42 images with a face had at least one found | recall >= 0.98 |
| Small faces in crowds found | about 80% of those labelled | not set |
| Printed text, clearly legible (20 images), at 960 px | **20 of 20** | OCR redaction >= 0.95 |
| Printed text at 736 px | 18 of 20 (the two misses are distant signs) | |
| Faint or incidental text (watermarks, small labels) | 73% found at 960 px | not set |
| Share of a picture covered by boxes | median 4.8%, 90th percentile 17% | |
| Pictures with no text that still got a text box | 24 of 43, largest cover 12% | |
| Fabric images covered by a text box over 5% | none | |
| Legitimate fashion refused at 0.7 | **0 of 78** (72 other, 6 swimwear) | |
| Legitimate fashion refused at 0.6 | 1 of 78 (a runway one-piece scored exactly 0.60) | |

What the misses and false alarms were:

- **Faces missed:** a person turned away at a loom and one of a couple posed
  at an angle. Both are the case a front-facing detector is weakest at.
- **False face alarms:** a mannequin, a leaf pattern and a child seen from
  behind. Harmless: the area is filled.
- **Printed faces:** commemorative cloth with five printed portraits had three
  filled. The pipeline cannot tell a printed face from a person, so this fabric
  will be defaced. Rare, and the safe direction, but it is real.
- **Text misses at 736 px:** signs on buildings at a distance.
- **Over-redaction:** text boxes land on busy patterns and flowers. They are
  small, and no fabric sample was covered.

What could **not** be measured, and is therefore unknown:

- **How many explicit images the safety check refuses.** None were downloaded,
  and none should be. The 97.8% accuracy is the model author's own figure on
  their data. The set measures only the cost to legitimate fashion: false
  alarms.
- **Minors**, not detected at all.
- **Non-apparel** images, not rejected.
- Anything outside the set's 82 images. Six swimwear images is a small sample;
  one more borderline picture would change the false-alarm rate noticeably.

The honest summary: faces are at the target within noise, text is at the target
at 960 px, and the safety check is tuned so that fashion is not refused but its
recall on harmful content is taken on trust.

## Deployment

- `MEDIA_DETECTOR=auto` (default): the light detector when models are present;
  outside `local` the service **refuses to start** without them.
- `MEDIA_MODELS_DIR` (default `models/media`; `/opt/models/media` in the image).
- `NullDetector` is only honoured in `local`.
- The API image installs the `media` extra (`pip install ".[media]"`). A service
  that never decodes an image does not need it.
- `MEDIA_SAFETY_THRESHOLD` (default 0.7) and `MEDIA_SAFETY_REQUIRED` (default off;
  turn on once the image carries the model).
