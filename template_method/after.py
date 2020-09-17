def template_method(action):
    # For example pulling data from DB and preparing model features...
    print('Setting up...')

    result = action()

    # For example closing connection to DB  calculating model predictions
    print('Tearing down...')

    return result


def action_a():
    # For example predicting via KNN
    print('Running action A')


def action_b():
    # For example predicting via Logistics Regression
    print('Running action B')



result_a = template_method(action_a)
result_b = template_method(action_b)
