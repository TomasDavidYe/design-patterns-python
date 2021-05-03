def f_score(precision, recall, beta):
    return (1 + beta ** 2) * precision * recall / (beta ** 2 * precision + recall)


print(f_score(precision=0.9,
              recall=0.7,
              beta=0.5))

# Dumb model predicting everything to class 0
total_num_observations = 100
num_positive = 2
num_negative = 98
true_positive = 0
false_positive = 0
false_negative = 2
true_negative = 98

accuracy = (true_positive + true_negative) / total_num_observations  # = (0 + 98 / 100) = 0.98
precision = true_positive / (true_positive + false_positive)  # = 0 / (0 + 0) = NaN
recall = true_positive / (true_positive + true_negative)  # = 0 / (0 + 98) = 0
f_score = (2 * precision * recall) / (precision + recall)  # NaN

# Smarter model which got some rare observations right
total_num_observations = 100
num_positive = 2
num_negative = 98
true_positive = 1
false_positive = 2
false_negative = 1
true_negative = 96

accuracy = (true_positive + true_negative) / total_num_observations  # = (1 + 96 / 100) = 0.97
precision = true_positive / (true_positive + false_positive)  # = 1 / (1 + 2) = 0.33
recall = true_positive / (true_positive + true_negative)  # = 1 / (1 + 96) = 0.0103
f_score = (2 * precision * recall) / (precision + recall)  # = ~0.02






# Dumb model which predicts everything into positive class
total_num_observations = 100
num_positive = 2
num_negative = 98
true_positive = 2
false_positive = 98
false_negative = 0
true_negative = 0

accuracy = (true_positive + true_negative) / total_num_observations  # = (2 / 100) = 0.02
precision = true_positive / (true_positive + false_positive)  # = 2 / (2 + 98) = 0.02
recall = true_positive / (true_positive + true_negative)  # = 2 / (2 + 0) = 1.0
f_score = (2 * precision * recall) / (precision + recall)  # = ~0.04
