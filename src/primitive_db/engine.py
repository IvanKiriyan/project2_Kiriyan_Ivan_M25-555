import prompt

HELP_TEXT = "<command> exit - выйти из программы\n<command> help - справочная информация"


def welcome() -> None:
    print("Первая попытка запустить проект!\n")
    print("***")
    print(HELP_TEXT)

    while True:
        command = prompt.string("Введите команду: ").strip()

        if command == "exit":
            return

        if command == "help":
            print()
            print(HELP_TEXT)
            continue

        print()
        print("Неизвестная команда. Введите help для справки.")