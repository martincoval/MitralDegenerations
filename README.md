# Projekt - MVC struktura

Diagnostická aplikace pro echokardiografické vyšetření (UC-01, UC-02, UC-03).

## Struktura

```
project/
├── data/
│   ├── raw_dicom/        # vstupní .dcm soubory
│   └── anonymized/       # výstup konverze (images/ + calibrations.json)
├── models/                # Model - data a doménová logika
│   ├── patient_name.py    # extrakce jména pacienta z DICOM tagu
│   ├── calibration.py      # extrakce měřítka (mm/pixel) z DICOM tagu
│   ├── patient.py          # Patient/Examination entity + repozitář (DB) - TODO
│   ├── measurement.py      # výpočet LA/Ao a LVIDdN - TODO
│   └── acvim_classification.py  # klasifikace dle ACVIM tabulky - TODO
├── controllers/            # Controller - orchestrace use case flow
│   ├── conversion_controller.py   # UC-01: načtení, anonymizace, export .jpg
│   └── diagnostic_controller.py   # UC-02: AI model → měření → klasifikace → uložení - TODO
├── views/                   # View - GUI (framework zatím nezvolen)
│   ├── main_window.py
│   ├── patient_card.py
│   └── image_viewer.py
├── utils/
│   └── image_utils.py      # resize/normalizace obrazu (bez domain logiky)
├── scripts/
│   └── run_conversion.py   # CLI vstupní bod pro dávkovou konverzi
├── tests/
│   └── test_staging.py
└── requirements.txt
```


## Aktuální stav projektu

- **Anonymizace a příprava dat (UC-01):** Plně funkční skripty pro lokální zpracování souborů DICOM. Zajišťují bezpečné odstranění citlivých údajů pacientů, pixelovou kalibraci a export dat připravených pro cloudové zpracování v prostředí Google Colab.
- **AI segmentace a klasifikace (UC-02 / UC-03):** Implementované modely pro parasternální krátkou (DogPSAX) a dlouhou osu (DogPLAX) založené na adaptované architektuře SAMUS. Kód a trénovací skripty jsou optimalizovány pro běh v cloudu a propojeny s vyhodnocovací logikou ACVIM.

## Spuštění lokální dávkové konverze

Pro spuštění konverze a anonymizace surových DICOM souborů z adresáře `data/raw_dicom/` spusťte:

```bash
python scripts/run_conversion.py

## Spuštění dávkové konverze

```bash
python scripts/run_conversion.py
```
