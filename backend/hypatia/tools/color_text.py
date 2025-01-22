# https://stackabuse.com/how-to-print-colored-text-in-python/
style_to_number = {'normal': 0, 'bold': 1, 'dark': 2, 'light': 3, 'underline': 4, 'blink': 5}
text_color_to_number = {'black': 30, 'red': 31, 'green': 32, 'yellow': 33, 'blue': 34, 'purple': 35,
                        'cyan': 36, 'white': 37}
background_color_to_number = {'black': 40, 'red': 41, 'green': 42, 'yellow': 43, 'blue': 44, 'purple': 45,
                              'cyan': 46, 'white': 47}
text_color_matplotlib = {'black': 'white', 'red': 'black', 'green': 'white', 'yellow': 'black', 'blue': 'white',
                         'purple': 'white', 'cyan': 'black', 'white': 'black'}

def colorize_text(text: str, style_text: str = 'normal', color_text: str = 'white', color_background: str = 'black'):
    if style_text not in style_to_number.keys():
        raise ValueError(f"Style '{style_text}' not found, options are {style_to_number.keys()}")
    if color_text not in text_color_to_number.keys():
        raise ValueError(f"Color '{color_text}' not found, options are {text_color_to_number.keys()}")
    if color_background not in background_color_to_number.keys():
        raise ValueError(f"Color '{color_background}' not found, options are {background_color_to_number.keys()}")
    style_number = style_to_number[style_text]
    text_color_number = text_color_to_number[color_text]
    background_color_number = background_color_to_number[color_background]
    return f"\033[{style_number};{text_color_number};{background_color_number}m{text}\033[0;0m"

def catalog_name_text(text: str):
    return colorize_text(text, style_text='bold', color_text='black', color_background='purple')

def file_name_text(text: str):
    return colorize_text(text, style_text='bold', color_text='black', color_background='green')

def warning_yellow_text(text: str):
    return colorize_text(text, style_text='bold', color_text='black', color_background='yellow')

def simbad_error_text(text: str):
    return colorize_text(text, style_text='normal', color_text='black', color_background='yellow')