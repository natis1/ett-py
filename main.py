# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import src
import website
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    src.database.init_db()
    src.database.add_player("Pine", "SelfAdded", 2, 0)
    src.database.add_player("SuperPIne", "lol", 0, 5.02)
    src.database.add_character("Pine", "SelfAdded", "Autumn", "Leshy", "Back-Alley Doctor", "Druid",
                               "Leaf Leshy", 'https://meme.com/memes', 0, 'Absalom', 0)
    src.database.add_xp_to_player("Pine", 42)

    app = website.create_app()
    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
