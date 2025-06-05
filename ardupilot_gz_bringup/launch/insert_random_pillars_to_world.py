import random
from pathlib import Path

WORLD_SDF_PATH = (Path(__file__).parent.parent / "../ardupilot_gz_gazebo/worlds/obstacle_map_surrounded.sdf").resolve()
PILLAR_MODEL_NAME = "pillar"
NUM_PILLARS = 8
X_MIN, X_MAX = -14.0, 14.0
Y_MIN, Y_MAX = -14.0, 14.0

def make_include_block(name, x, y, z):
    return f"""
    <include>
      <uri>model://{PILLAR_MODEL_NAME}</uri>
      <name>{name}</name>
      <pose>{x:.2f} {y:.2f} {z:.2f} 0 0 0</pose>
    </include>
    """

def main():
    with open(WORLD_SDF_PATH, "r") as f:
        lines = f.readlines()

    # find <world ...> line and its closing </world>
    world_start = next(i for i, l in enumerate(lines) if "<world" in l)
    world_end = next(i for i, l in enumerate(lines) if "</world>" in l)

    # remove old pillars (by name)
    new_lines = []
    for l in lines[:world_end]:
        if "<include>" in l and "pillar" in l:
            continue
        new_lines.append(l)
    # add random pillars before </world>
    for i in range(NUM_PILLARS):
        x = random.uniform(X_MIN, X_MAX)
        y = random.uniform(Y_MIN, Y_MAX)
        z = 0.5
        new_lines.append(make_include_block(f"pillar_{i}", x, y, z))
    new_lines += lines[world_end:]

    with open(WORLD_SDF_PATH, "w") as f:
        f.writelines(new_lines)

    print(f"Inserted {NUM_PILLARS} pillars into {WORLD_SDF_PATH}")

if __name__ == "__main__":
    main()