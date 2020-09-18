def action_a():
    # For example pulling data from DB and preparing model features...
    print('Setting up...')

    # For example predicting via KNN
    print('Running action A')

    # For example closing connection to DB  calculating model predictions
    print('Tearing down...')

    return 'A'


def action_b():
    # For example pulling data from DB and preparing model features...
    print('Setting up...')

    # For example predicting via Logistics Regression
    print('Running action B')

    # For example closing connection to DB  calculating model predictions
    print('Tearing down...')

    return 'B'


# Example usage
print()
print(f'Result of action_a = {action_a()}')

print()
print(f'Result of action_b = {action_b()}')
