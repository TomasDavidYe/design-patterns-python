def f_score(precision, recall, beta):
    return (1 + beta ** 2) * precision * recall / (beta ** 2 * precision + recall)



print(f_score(precision=0.94,
              recall=0.96,
              beta=.1))
