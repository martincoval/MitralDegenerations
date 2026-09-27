from dataclasses import dataclass
from typing import Optional


LVIDD_ALLOMETRIC_EXPONENT = 0.294
LVIDDN_THRESHOLD_B2 = 1.7
LA_AO_THRESHOLD_B2 = 1.6


@dataclass
class MeasurementResult:
    lvidd_mm: Optional[float]
    la_mm: Optional[float]
    ao_mm: Optional[float]
    weight_kg: Optional[float]


@dataclass
class DiagnosisResult:
    lvidd_n: Optional[float]
    la_ao_ratio: Optional[float]
    stage: str  # "B1", "B2", nebo "NELZE VYHODNOTIT"
    reason: Optional[str] = None  # důvod, pokud NELZE VYHODNOTIT


def calculate_lvidd_n(lvidd_mm: float, weight_kg: float) -> float:
    lvidd_cm = lvidd_mm / 10
    return lvidd_cm / (weight_kg ** LVIDD_ALLOMETRIC_EXPONENT)


def calculate_la_ao_ratio(la_mm: float, ao_mm: float) -> float:
    return la_mm / ao_mm


def classify_stage(measurement: MeasurementResult) -> DiagnosisResult:
    m = measurement

    missing = []
    if m.lvidd_mm is None:
        missing.append("LVIDd")
    if m.la_mm is None:
        missing.append("LA")
    if m.ao_mm is None:
        missing.append("Ao")
    if m.weight_kg is None:
        missing.append("hmotnost")

    if missing:
        return DiagnosisResult(
            lvidd_n=None,
            la_ao_ratio=None,
            stage="NELZE VYHODNOTIT",
            reason=f"Chybí hodnoty: {', '.join(missing)}",
        )

    lvidd_n = calculate_lvidd_n(m.lvidd_mm, m.weight_kg)
    la_ao = calculate_la_ao_ratio(m.la_mm, m.ao_mm)

    is_b2 = (lvidd_n >= LVIDDN_THRESHOLD_B2) and (la_ao >= LA_AO_THRESHOLD_B2)
    stage = "B2" if is_b2 else "B1"

    return DiagnosisResult(
        lvidd_n=round(lvidd_n, 3),
        la_ao_ratio=round(la_ao, 3),
        stage=stage,
    )


if __name__ == "__main__":
    test_case = MeasurementResult(
        lvidd_mm=32.9,
        la_mm=22.1,
        ao_mm=15.1,
        weight_kg=9.6,
    )
    result = classify_stage(test_case)
    print(f"LVIDDn: {result.lvidd_n}")
    print(f"LA/Ao: {result.la_ao_ratio}")
    print(f"Stádium: {result.stage}")