def template_method(action):
    # For example pulling data from DB and preparing model features...
    print('Setting up...')

    # Running custom part
    result = action()

    # For example closing connection to DB  calculating model predictions
    print('Tearing down...')

    # Returning custom result after all boilerplate has been executed
    return result


def action_a():
    # For example predicting via KNN
    print('Running action A')
    return 'A'


def action_b():
    # For example predicting via Logistics Regression
    print('Running action B')
    return 'B'


# Example usage
print()
print(f'Result of action_a = {template_method(action_a)}')

print()
print(f'Result of action_b = {template_method(action_b)}')
