import os, random

OUT_BASE = "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/samus_dataset/Echocardiography-DogPSAX"
MAIN_PATIENT = "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/samus_dataset/MainPatient"
os.makedirs(MAIN_PATIENT, exist_ok=True)

SUBTASK = "Echocardiography-DogPSAX"

names = sorted([f.replace(".png", "") for f in os.listdir(os.path.join(OUT_BASE, "img"))])
random.seed(42)
random.shuffle(names)

val_names = names[:1]
train_names = names[1:]

print("Validace:", val_names)
print("Trénink:", train_names)

def write_split(filename, name_list):
    with open(os.path.join(MAIN_PATIENT, filename), "w") as f:
        for name in name_list:
            f.write(f"1/{SUBTASK}/{name}\n")  # class_id=1 -> aorta
            f.write(f"2/{SUBTASK}/{name}\n")  # class_id=2 -> LA

write_split("train-DogPSAX.txt", train_names)
write_split("val-DogPSAX.txt", val_names)

print(f"\nHotovo: {len(train_names)*2} tréninkových řádků, {len(val_names)*2} validačních řádků")