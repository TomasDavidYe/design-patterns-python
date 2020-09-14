def template_method(action):
    # Opening connection to DB, for example...
    print('Setting up...')

    action()

    # Closing connection to DB, for example
    print('Tearing down...')


def action_a():
    print('Running action A')


def action_b():
    print('Running action B')



template_method(action_a)
template_method(action_b)
