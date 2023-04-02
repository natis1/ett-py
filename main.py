#!/usr/bin/python
from werkzeug.middleware.proxy_fix import ProxyFix

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import src
import website
import os
import sys


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    src.database.init_db()
    app = website.create_app()
    if len(sys.argv) > 1:
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )
        app.run(debug=False, port=int(sys.argv[1]))
    else:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
