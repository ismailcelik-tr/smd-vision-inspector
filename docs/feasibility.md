# Feasibility (P2)

> Status: draft. Camera sizing only. Tracking, quality gate and registration
> spikes follow once a stable close-up video is available.

Scope: Karvox 4.3" panel only. Other products are checked against the
result later.

## Inputs

| Input | Value | Source |
|---|---|---|
| Panel size | 151 × 87.706 mm (long side along travel) | user |
| Board speed | ≈210 mm/s, constant (211 and 207 mm/s in two runs) | phone video, template tracking |
| Conveyor | edge-rail, open above, cluttered see-through background | photo |
| Smallest parts | 1206 passives; 0.5 mm pitch: LQFP48, MSOP-10, 40-pin FPC | BOM |

Speed was measured on hand-held 4K/30 fps phone video at ≈0.2 mm/px after
removing camera drift. Accuracy is about ±5 %.

## Requirements

| Item | Value | Why |
|---|---|---|
| Resolution | ≤ 0.05 mm/px | offset and pin-1 on 0.5 mm pitch parts |
| Design speed | 250 mm/s | measured speed + 20 % |
| Full-board frames per pass | ≥ 3 | best-frame selection without a trigger |
| FOV margin | 5 mm per edge, ±5 mm lateral play | board segmentation, rail clearance |
| Motion blur | ≤ 1 px | sub-pixel offset measurement |

## Sizing

```
travel/frame  d     = v / fps
FOV along     Fx    = L + 3·d + 2·edge
resolution    r     = Fx / sensor_px_x
exposure      t_max = r / v                 (1 px blur)
magnification m     = sensor_width / Fx
working dist  WD    ≈ f · (1 + 1/m)
```

| Sensor | Shutter | fps | Fx (mm) | mm/px | Fy (mm, need 108) | t_max | Lens → WD |
|---|---|---|---|---|---|---|---|
| IMX304 12 MP, 3.45 µm, 1.1" | global | 23 | 194 | 0.047 | 142 | 189 µs | 25 mm → 368 mm |
| IMX545 12 MP, 2.74 µm, 1/1.1" | global | 30 | 186 | 0.045 | 136 | 182 µs | 16 mm → 281 mm |
| IMX183 20 MP, 2.4 µm, 1" | rolling | 14 | 215 | 0.039 | 143 | 157 µs | 16 mm → 277 mm |
| IMX226 12 MP, 1.85 µm, 1/1.7" | rolling | 32 | 184 | 0.046 | 139 | 183 µs | 12 mm → 309 mm |

Findings:

- **Exposure must be ≈ 150–190 µs.** Continuous light cannot reach this
  through a polarizer. A strobed LED, synced to the camera's exposure
  output, is required for every option.
- **Plain rolling shutter is not usable.** Readout skew equals the travel per
  frame: 8–18 mm, i.e. 170–460 px of shear. Rolling-shutter sensors only work
  in global-reset-release (GRR) mode with a strobe. In GRR, lower rows keep
  integrating until readout (up to 1/fps), so ambient light causes a
  top-to-bottom brightness gradient. A light-tight shroud is then mandatory.
- **A global shutter tolerates ambient leaks.** In a 190 µs exposure ambient
  light is negligible against the strobe. The shroud still helps against
  glare but its fit is not critical.
- **Small pixels are diffraction-limited.** At f/5.6 the Airy disk is
  7.5 µm: 2.2 px on 3.45 µm, 3.1 px on 2.4 µm, 4.1 px on 1.85 µm. Effective
  resolution of the IMX226 drops to about 0.08–0.09 mm/px, which is enough
  for presence but marginal for offset and pin-1.
- **Depth of field is not a constraint.** At f/5.6 it is 15–26 mm,
  more than board warp plus the tallest SMD part.
- **USB3 bandwidth fits.** 12 MP at 23 fps is 283 MB/s. GigE IMX304 models
  run at ≈9 fps, which forces Fx ≈ 244 mm and 0.06 mm/px, so USB3 is
  preferred. Passive USB3 cables limit the PC distance to a few metres.

## Options

Prices are indicative public listings in USD, excluding VAT, customs and
shipping to Turkey. Get local distributor quotes before buying.

### 1. Global shutter 12 MP (recommended)

| Part | Candidate | Price |
|---|---|---|
| Camera | Hikrobot MV-CH120-10UC (IMX304, marked EoL; ask for successor) | ≈ $1,750 |
| | Daheng MARS-1230-23U3C (IMX304) | quote |
| | Basler a2A4096-30ucPRO (IMX545) | $1,559 / €1,339 |
| Lens | Hikrobot MVL-KF2528M-12MPE, 25 mm 1.1" | $210–280 |
| | Computar V2528-MPY, 25 mm 1.1" | $460–620 |

Camera + lens: ≈ $1,770–2,370.

### 2. Rolling shutter 20 MP in GRR (budget)

| Part | Candidate | Price |
|---|---|---|
| Camera | Hikrobot MV-CE200-10UC (IMX183) | $380–490 |
| Lens | 16 mm, 1", 20 MP rated | quote |

Camera + lens: ≈ $600–800 (estimate). Depends on a light-tight shroud;
14 fps leaves the smallest frame margin.

### 3. Rolling shutter 12 MP in GRR (prototype only)

| Part | Candidate | Price |
|---|---|---|
| Camera | Daheng MER2-1220-32U3C (IMX226) | $296–€369 |
| Lens | 12 mm, 1/1.7", 12 MP rated | quote |

Camera + lens: ≈ $450–600 (estimate). Diffraction limits offset and pin-1
checks.

### Lighting and shroud (all options)

| Part | Candidate | Price |
|---|---|---|
| 2 × strobe bar light, white, ≥ 250 mm | CCS LDL2 or similar overdrive bar | from $414 each |
| Strobe controller (if not built in) | Leimac ISC-24, VA Imaging strobe controller | $149–349 |
| Diffuser + polarizer plates, lens polarizer | CCS plates | from $17 / $41 |
| Shroud | aluminium profile + black panels, local fabrication | quote |

Lighting: ≈ $900–1,500 (estimate).

| Option | Estimated total (excl. shroud) |
|---|---|
| 1. Global shutter 12 MP | ≈ $2,700–3,900 |
| 2. Rolling 20 MP GRR | ≈ $1,500–2,300 |
| 3. Rolling 12 MP GRR | ≈ $1,350–2,100 |

## Open questions

- Largest board in the product range. Current FOV fits boards up to
  ≈ 115 mm across and ≈ 160 mm along travel at 3 frames per pass.
- Is the conveyor speed fixed? Lower speed scales exposure and light power
  down linearly.
- PC location relative to the camera (USB3 cable length).
- Can the existing photoelectric sensor on the conveyor serve as a hardware
  trigger later?

## Next steps

1. Close-up stable video (board ≈ 80 % of frame width, ≈ 0.045 mm/px,
   1/2000 s shutter) to test tracking, quality gate and fiducial
   registration at production-like resolution.
2. Local quotes for option 1 and the lighting set.

## Sources

- [Hikrobot MV-CH120-10UC listing](https://light186.com/product/hikrobot-12mp-23-1fps-usb-3-0-camera-with-an-imx304-sensor/)
- [Daheng MARS-1230-23U3C press release](https://en.daheng-imaging.com/show-43-340-1.html)
- [Basler a2A4096-30ucPRO (Graftek)](https://graftek.com/product/a2a4096-30ucpro/),
  [Basler shop](https://www.baslerweb.com/en/shop/a2a4096-30ucpro/)
- [Hikrobot MV-CE200-10UC datasheet](https://www.maxxvision.com/downloads/Cameras/USB30/Hikrobot/Hikrobot_MV-CE200-10UMUC.pdf),
  [listing](https://light186.com/product/hikrobot-20mp-19-2fps-usb-3-0-camera-with-an-imx183-sensor-2/)
- [Daheng MER2-1220-32U3C](https://en.daheng-imaging.com/show-106-1997-1.html),
  [listing](https://va-imaging.com/products/usb3-0-camera-12-2mp-color-sony-imx226-mer2-1220-32u3c)
- [Hikrobot MVL-KF2528M-12MPE](https://light186.com/product/hikrobot-1-1-25mm-f2-8-12mp-c-mount-lens/)
- [Computar V2528-MPY (B&H)](https://www.bhphotovideo.com/c/product/1337068-REG/computar_v2528_mpy_1_1_25mm_f2_8_12_0.html)
- [CCS lights](https://fjwoptical.com/collections/ccs),
  [VA Imaging strobe controller](https://va-imaging.com/en-us/products/industrial-strobe-controller-led-light-trigger-va-strb-d1-v1),
  [Leimac controllers](https://machinevisionstore.com/catalog/bycategory?category=1017&group=57)
- [Basler sensor shutter modes (GRR)](https://docs.baslerweb.com/sensor-shutter-mode),
  [XIMEA shutter modes](https://ximea.com/support/wiki/allprod/Sensor_Shutter_Modes)
