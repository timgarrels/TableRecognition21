import os

improvements = [
    "NoImprovement",
    "EdgeMutationProbability",
    "EdgeMutationProbabilityExtreme",
    "AvgDegreeCut",
]

datasets = [
    "FusTe",
    "Deco"
]

seeds = [
    1,
    2,
    3,
]

noise_options = [
    "--noise",
    "",
]

command = " ".join([
    "python3",
    "src/run_cross_validation.py",
    "--dataset {dataset}",
    "{noise}",
    "--seed {seed}",
    "--improvement {improvement}",
    "2> {log_file} &",
])

try:
    os.mkdir("logfiles")
except FileExistsError:
    print("logfiles dir already exists")
    print("Is other computation still running?")
    print("Remove old logfiles dir if no other computation is running and you want to restart")
    exit(-1)

for improvement in improvements:
    for dataset in datasets:
        for seed in seeds:
            for noise in noise_options:
                noise_str = "noise" if "noise" in noise else "noNoise"
                log_file = f"logfiles/{dataset}_{improvement}_{seed}_{noise_str}"

                run_ready_command = command.format(
                    dataset=dataset,
                    noise=noise,
                    seed=seed,
                    improvement=improvement,
                    log_file=log_file,
                )
                os.system(
                    run_ready_command
                )
