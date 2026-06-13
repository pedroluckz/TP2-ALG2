import random
import os

class InstanceGenerator:

    def __init__(self, seed=None):
        self.seed=seed
        self.rng = random.Random(seed)

    def generate_random(self,
                        m,
                        n,
                        density
                        ):

        costs = [
            1
            for _ in range(n)
        ]

        sets_masks = [0] * n

        for s in range(n):
            for e in range(m):

                if self.rng.random() < density:
                    sets_masks[s] |= (1 << e)


        for e in range(m):

            covered = False

            for s in range(n):

                if sets_masks[s] & (1 << e):
                    covered = True
                    break

            if not covered:

                s = self.rng.randrange(n)
                sets_masks[s] |= (1 << e)

        return {
            "type": "random",
            "density": density,
            "m": m,
            "n": n,
            "costs": costs,
            "sets_masks": sets_masks
        }
    
    def generate_adversarial(self, m):

        if (m // 2) % 2 == 0:
            raise ValueError(
                "n deve ser escolhido de forma que n/2 seja ímpar."
            )

        A = set(range(0, m, 2))
        B = set(range(1, m, 2))

        costs = []
        sets_masks = []

        #
        # adiciona A
        #
        mask_A = 0
        for e in A:
            mask_A |= (1 << e)

        sets_masks.append(mask_A)
        costs.append(1)

        #
        # adiciona B
        #
        mask_B = 0
        for e in B:
            mask_B |= (1 << e)

        sets_masks.append(mask_B)
        costs.append(1)

        covered = set()

        while len(covered) < m:

            uncovered_A = len(A - covered)
            uncovered_B = len(B - covered)

            size = max(uncovered_A, uncovered_B) + 1

            remaining = sorted(set(range(m)) - covered)

            chosen = remaining[:min(size, len(remaining))]

            mask = 0

            for e in chosen:
                mask |= (1 << e)

            sets_masks.append(mask)
            costs.append(1)

            covered.update(chosen)

        return {
            "type": "adversarial",
            "m": m,
            "n": len(sets_masks),
            "costs": costs,
            "sets_masks": sets_masks
        }
    
    def save_to_file(self, instance, directory):

        def write_numbers(f, numbers, per_line=12):

            for i, num in enumerate(numbers):

                f.write(f"{num} ")

                if (i + 1) % per_line == 0:
                    f.write("\n")

            if len(numbers) % per_line != 0:
                f.write("\n")

        os.makedirs(directory, exist_ok=True)

        if instance["type"] == "random":

            filename = (
                f"rand_d{instance['density']}_"
                f"m{instance['m']}_"
                f"n{instance['n']}_"
                f"s{self.seed}.txt"
            )

        else:

            filename = (
                f"adv_m{instance['m']}_"
                f"n{instance['n']}.txt"
            )

        filepath = os.path.join(directory, filename)

        m = instance["m"]
        n = instance["n"]

        costs = instance["costs"]
        sets_masks = instance["sets_masks"]

        with open(filepath, "w") as f:

            f.write(f"{m} {n}\n")

            write_numbers(f, costs)

            for element in range(m):

                covering_sets = []

                for s in range(n):

                    if sets_masks[s] & (1 << element):
                        covering_sets.append(s + 1)

                f.write(f"{len(covering_sets)}\n")

                write_numbers(f, covering_sets)

if __name__ == "__main__":

    densities = [0.1, 0.3, 0.5]

    NUM_INSTANCES = 20

    #
    # Variando m
    #
    fixed_n = 75

    m_values = [
        25,
        50,
        75,
        100,
        125
    ]

    #
    # Variando n
    #
    fixed_m = 75

    n_values = [
        25,
        50,
        100,
        125
    ]

    instance_id = 0

    # --------------------
    # m variável
    # --------------------

    for density in densities:

        for m in m_values:

            for rep in range(NUM_INSTANCES):

                generator = InstanceGenerator(
                    seed=instance_id
                )

                instance = generator.generate_random(
                    m=m,
                    n=fixed_n,
                    density=density
                )

                directory = (
                    f"generatedinstances/"
                    f"d{density}/"
                    f"m{m}_n{fixed_n}"
                )

                generator.save_to_file(
                    instance,
                    directory
)

                instance_id += 1

    # --------------------
    # n variável
    # --------------------

    for density in densities:

        for n in n_values:

            for rep in range(NUM_INSTANCES):

                generator = InstanceGenerator(
                    seed=instance_id
                )

                instance = generator.generate_random(
                    m=fixed_m,
                    n=n,
                    density=density
                )

                directory = (
                    f"generatedinstances/"
                    f"d{density}/"
                    f"m{fixed_m}_n{n}"
                )

                generator.save_to_file(
                    instance,
                    directory
                )

                instance_id += 1

    # --------------------
    # adversariais
    # --------------------

    #for m in [26, 46, 66, 86, 106]:

        #for rep in range(NUM_INSTANCES):

            #instance = generator.generate_adversarial(m)

            #generator.save_to_file(instance)

    print("Instâncias geradas com sucesso.")