def normalize_name(text: str) -> str:
    return ' '.join(word.capitalize() for word in text.strip().split())


async def get_info_by_tests(tests_list, test_info):
    text = ""
    for test in tests_list:
        text += f"{test_info[test]}\n\n"
    return text


async def get_list_and_price(list_tests,tests_price ):
    text = ""
    price = 0
    for test in list_tests:
        text += f"{test} - {tests_price[test]}\n"
        price += tests_price[test]

    return text, price