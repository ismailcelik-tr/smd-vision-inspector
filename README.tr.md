# SMD Vision Inspector

[English](README.md)

SMD/SMT dizgi hattı için bilgisayarlı görü tabanlı kalite denetimi. Dizgi makinesinin
çıkışındaki sabit kamera, her PCB'yi fırından önce denetler. Bir bileşen eksik, kaymış,
dönmüş, ters ya da beklenmedik bir yerdeyse operatörü uyarır. IC'ler en sıkı kontrollerden
geçer.

**Durum:** erken geliştirme aşaması. Denetim akışı henüz yok.

## Yaklaşım

- Önce deterministik bilgisayarlı görü: fiducial ile kart hizalama, golden referansla
  karşılaştırma, template matching, ROI bazlı kontroller.
- AI yalnızca klasik yönteme göre ölçülmüş bir avantaj sağladığı yerde kullanılır.
- Yanlış negatif, yanlış pozitif ve gecikme birincil metriklerdir.
- Aşamalar ayrı bileşenlerdir: capture → acquisition → registration → inspection →
  decision → alerting. Kaydedilen denetimler çevrimdışı olarak değerlendirilir.

Kapsam için [PROJECT_BRIEF.md](PROJECT_BRIEF.md) dosyasına bakın (İngilizce).

## Geliştirme

[uv](https://docs.astral.sh/uv/) gerekir.

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Üretim görüntüleri ve ürün recipe'leri firmaya özeldir ve bu repoda bulunmaz. Testler
sentetik görüntüler kullanır.

## Lisans

[PolyForm Noncommercial 1.0.0](LICENSE). Ticari olmayan kullanım serbesttir. Ticari
kullanım için telif hakkı sahibinden ayrıca lisans alınması gerekir; bir issue açın ya da
[@ismailcelik-tr](https://github.com/ismailcelik-tr) ile iletişime geçin. Bağlayıcı olan
İngilizce lisans metnidir.
