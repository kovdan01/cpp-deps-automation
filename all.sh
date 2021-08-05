#!/bin/bash

python init.py

python tools/cmake.py
python tools/ninja.py

python libs/yaml_cpp.py
python libs/cyrus_sasl.py
python libs/date.py
python libs/sqlpp11.py

# doesn't compile on some distributions due to horrible dependencies resolution
# wait for 0.30 release where this problem should be solved
# python libs/sqlpp11_mysql.py

python libs/catch2.py
python libs/boost.py

# doesn't compile with gcc 11 because of the bug: https://bugreports.qt.io/browse/QTBUG-90395
# python libs/qt5base.py
