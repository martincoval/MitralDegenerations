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

## Stav

- **Funkční a beze změny chování:** `models/patient_name.py`, `models/calibration.py`,
  `utils/image_utils.py`, `controllers/conversion_controller.py`, `scripts/run_conversion.py`
  (pokrývá UC-01, kroky 1-2 a 6 - nahrání, extrakce metadat, export anonymizovaného snímku).
- **Kostry k doplnění (byly prázdné i v původní struktuře):** `models/patient.py`
  (vyhledávání pacienta a historie - UC-01 krok 3-5, UC-03), `models/measurement.py`
  a `models/acvim_classification.py` (UC-02 kroky 3-5), `controllers/diagnostic_controller.py`
  (napojení na AI model - UC-02 krok 1-2), `views/*` (GUI - framework zatím není
  v `requirements.txt`).

## Spuštění dávkové konverze

```bash
python scripts/run_conversion.py
```
