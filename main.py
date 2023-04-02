# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import src
import website
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    src.database.init_db()
    app = website.create_app()
    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
