import json
import os
import re

OUT_BASE = "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/samus_dataset/Echocardiography-DogPLAX"
MAIN_PATIENT = "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/samus_dataset/MainPatient"
SUBTASK = "Echocardiography-DogPLAX"

TEST_EXAM_IDS = {"003", "009", "015", "021"}
VAL_EXAM_IDS = {"002", "013"}  # uprav, pokud chceš jiná vyšetření na validaci

with open(os.path.join(OUT_BASE, "manifest.json")) as f:
    manifest = json.load(f)

def extract_exam_id(source_json: str) -> str:
    match = re.match(r"(\d+)", source_json.strip())
    if not match:
        raise ValueError(f"Nelze najít číslo vyšetření v: {source_json}")
    return match.group(1).zfill(3)

train_names, val_names, test_names = [], [], []

for entry in manifest:
    exam_id = extract_exam_id(entry["source_json"])
    name = entry["name"]
    if exam_id in TEST_EXAM_IDS:
        test_names.append(name)
    elif exam_id in VAL_EXAM_IDS:
        val_names.append(name)
    else:
        train_names.append(name)

print(f"Trénink: {len(train_names)} snímků -> {train_names}")
print(f"Validace: {len(val_names)} snímků -> {val_names}")
print(f"Test: {len(test_names)} snímků -> {test_names}")

def write_train_val(filename, names):
    with open(os.path.join(MAIN_PATIENT, filename), "w") as f:
        for name in names:
            f.write(f"1/{SUBTASK}/{name}\n")  # jen jedna třída (LVIDd -> class_id 1)

def write_test(filename, names):
    with open(os.path.join(MAIN_PATIENT, filename), "w") as f:
        for name in names:
            f.write(f"{SUBTASK}/{name}\n")

write_train_val("train-DogPLAX.txt", train_names)
write_train_val("val-DogPLAX.txt", val_names)
write_test("test-DogPLAX.txt", test_names)

print("\nHotovo")