import os
import pyperclip


def take_screenshot(file_path):
    os.system(f'screencapture -i {file_path}')


def is_file(file_path):
    return os.path.isfile(file_path)


def remove_file(file_path):
    if is_file(file_path):
        os.system(f'rm {file_path}')


def display_notification(text, title):
    osascript = f'''
            osascript <<EOF
            display notification "{text}" with title "{title}"
            EOF
        '''
    os.system(osascript)


def copy_to_clipboard(text):
    display_notification(text=f'Copied \'{text}\' to Clipboard', title=text)
    pyperclip.copy(text)
