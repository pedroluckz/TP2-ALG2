import os
import csv
from Structures import SetCoverInstance

INSTANCES_DIR = "generatedinstances/adversarial"

OUTPUT_DIR = "testresults"
OUTPUT_CSV = os.path.join(
    OUTPUT_DIR,
    "adversarial_results.csv"
)

# main - roda o algoritmo guloso nas instâncias adversariais
def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(
        f for f in os.listdir(INSTANCES_DIR)
        if f.endswith(".txt")
    )

    with open(OUTPUT_CSV, "w", newline="") as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow([
            "instance",
            "m",
            "n",
            "greedy_cost",
            "opt_cost",
            "approx_ratio",
            "sets_selected"
        ])

        for filename in files:

            filepath = os.path.join(
                INSTANCES_DIR,
                filename
            )

            instance = SetCoverInstance(0, 0)
            instance.load_from_file(filepath)

            greedy_cost, solution = (
                instance.calculate_greedy_upper_bound()
            )

            # Nas instâncias adversariais, a solução ótima é A + B
            opt_cost = 2

            approx_ratio = (
                greedy_cost / opt_cost
            )

            writer.writerow([
                filename,
                instance.num_elements,
                instance.num_sets,
                greedy_cost,
                opt_cost,
                approx_ratio,
                len(solution)
            ])

            print(
                f"{filename:<25} "
                f"m={instance.num_elements:<5} "
                f"n={instance.num_sets:<5} "
                f"greedy={greedy_cost:<5} "
                f"ratio={approx_ratio:.2f}"
            )

    print(f"\nResultados salvos em: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()