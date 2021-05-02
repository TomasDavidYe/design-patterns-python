
def permutations(x):
    permutations_with_prefix(prefix="",
                             remaining=x)


def permutations_with_prefix(prefix, remaining):
    if len(remaining) == 0:
        print(prefix)
    else:
        for index, char in enumerate(remaining):
            permutations_with_prefix(prefix + char, remaining[:index] + remaining[index + 1:])

