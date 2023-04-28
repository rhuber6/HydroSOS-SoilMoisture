

import os

path = "/Users/rachel1/Downloads/DR_maps"

for filename in os.listdir(path):
    if filename.endswith(".png"):
        if "DR_" in filename and "soilMoist" in filename and "_" not in filename.split("_")[1]:
            old_name = os.path.join(path, filename)
            new_name = os.path.join(path, "DR_" + filename.split("_")[2] + "_" + filename.split("_")[1] + "_" + "soilMoist.png")
            os.rename(old_name, new_name)
            print(f"{old_name} renamed to {new_name}")