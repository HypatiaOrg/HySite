from roman import fromRoman, InvalidRomanNumeralError


def legacy_float(x) -> float | None:
    try:
        return float(x)
    except ValueError:
        return None


def legacy_spectype(s: str) -> float:
    typechar = []
    digits = []
    roman_numerals = []
    curr_digit = ""
    curr_roman_numeral = ""
    for char in s + " ":
        if char == "F":
            typechar.append(10)
        elif char == "G":
            typechar.append(20)
        elif char == "K":
            typechar.append(30)
        elif char == "M":
            typechar.append(40)
        if char in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."}:
            curr_digit += char
        elif len(curr_digit) > 0:
            try:
                test_num = float(curr_digit)
            except ValueError:
                pass
            else:
                digits.append(test_num)
            curr_digit = ""

        if char in {"I", "V", "X"}:
            curr_roman_numeral += char
        elif len(curr_roman_numeral) > 0:
            try:
                numeral = fromRoman(curr_roman_numeral)
            except InvalidRomanNumeralError:
                pass
            else:
                roman_numerals.append(numeral)
            curr_roman_numeral = ""
    first_type = 0
    if len(typechar) > 0:
        first_type = typechar[0]
    first_digit = 0
    if len(digits) > 0:
        first_digit = digits[0]
    first_roman_numeral = 0
    if len(roman_numerals) > 0:
        first_roman_numeral = float(roman_numerals[0])
    return float(first_type + first_digit + (first_roman_numeral / 100))
