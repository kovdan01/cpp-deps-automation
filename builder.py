#!/bin/python

import os
import pickle
import requests
import subprocess
import sys


def get_platform():
    platforms = {
        'linux'  : 'Linux',
        'linux1' : 'Linux',
        'linux2' : 'Linux',
        'darwin' : 'macOS',
        'win32'  : 'Windows'
    }
    if sys.platform not in platforms:
        raise RuntimeError("Unknown platform {}".format(sys.platform))

    return platforms[sys.platform]


def execute_command(cmd):
    ret = subprocess.call(cmd, shell=True)
    if ret != 0:
        raise RuntimeError('Exit code {} while executing "{}"'.format(ret, cmd))


def check_prefix_dif(prefix_dir, source_dir):
    if prefix_dir is None:
        prefix_dir = os.path.join(os.path.abspath(source_dir), "prefix")
    if os.path.isdir(prefix_dir):
        raise RuntimeError("Prefix directory {} already exists".format(prefix_dir))
    os.mkdir(prefix_dir)
    return prefix_dir


def check_build_dir(build_dir, source_dir):
    if build_dir is None:
        build_dir = os.path.join(os.path.abspath(source_dir), "build")
    if os.path.isdir(build_dir):
        raise RuntimeError("Build directory {} already exists".format(build_dir))
    os.mkdir(build_dir)
    return build_dir


def download_and_extract_archive(url, label="temp"):
    if url.endswith(".tar.gz"):
        archive_format = ".tar.gz"
    elif url.endswith(".tar.bz2"):
        archive_format = ".tar.bz2"
    elif url.endswith(".tar.xz"):
        archive_format = ".tar.bz2"
    elif url.endswith(".zip"):
        archive_format = ".zip"
    else:
        raise RuntimeError("Unknown archive type on URL {}".format(url))

    archive_name = label + archive_format
    print("Downloading {} from {}...".format(label, url))
    open(archive_name, "wb").write(requests.get(url, allow_redirects=True).content)
    print("Done!")

    print("Extracting {}...".format(archive_name))
    if archive_format == ".zip":
        execute_command("7z x {}".format(archive_name))
    elif archive_format == ".tar.gz" or archive_format == ".tar.bz2" or archive_format == ".tar.xz":
        execute_command("tar -xf {}".format(archive_name))
    else:
        assert False
    print("Done!")


class Builder:
    """
    Class members:
    - cmake_binary;
    - ninja_binary;
    - c_compiler;
    - cxx_compiler;
    - prefixes: dict from str (library label) to str (library prefix).
    """

    def __init__(self, c_compiler=None, cxx_compiler=None, platform=None):
        self.platform = get_platform()
        self.prefixes = dict()

        if c_compiler is None:
            try:
                self.c_compiler = os.environ["CC"]
            except KeyError as e:
                self.c_compiler = "gcc"
        else:
            self.c_compiler = c_compiler

        if cxx_compiler is None:
            try:
                self.cxx_compiler = os.environ["CXX"]
            except KeyError as e:
                self.cxx_compiler = "g++"
        else:
            self.cxx_compiler = cxx_compiler


    """Configure, build and install project with CMake; return installation prefix."""
    def build_cmake(self, source_dir, cmake_params=None, prefix_dir=None,
                    build_dir=None, build_type="Release"):

        prefix_dir = check_prefix_dif(prefix_dir, source_dir)
        build_dir = check_build_dir(build_dir, source_dir)

        if cmake_params is None:
            cmake_params = ""

        execute_command("{} ".format(self.cmake_binary) +
                        "-S {} ".format(source_dir) +
                        "-B {} ".format(build_dir) +
                        "-G Ninja " +
                        "-D CMAKE_MAKE_PROGRAM={} ".format(self.ninja_binary) +
                        "-D CMAKE_INSTALL_PREFIX={} ".format(prefix_dir) +
                        "-D CMAKE_BUILD_TYPE={} ".format(build_type) +
                        "-D CMAKE_C_COMPILER={} ".format(self.c_compiler) +
                        "-D CMAKE_CXX_COMPILER={} ".format(self.cxx_compiler) +
                        "{} ".format(cmake_params))

        execute_command("{} --build {} --target all".format(self.cmake_binary, build_dir))
        execute_command("{} --build {} --target install".format(self.cmake_binary, build_dir))

        return prefix_dir


    """Configure project with configure script, build and install with make; return installation prefix."""
    def build_make(self, source_dir, configure_params=None,
                   prefix_dir=None, prefix_arg="--prefix=", build_dir=None):

        current_dir = os.getcwd()
        prefix_dir = check_prefix_dif(prefix_dir, source_dir)
        build_dir = check_build_dir(build_dir, source_dir)

        if configure_params is None:
            configure_params = ""

        configure_script = os.path.join(os.path.abspath(source_dir), "configure")
        os.chdir(build_dir)
        execute_command("{} ".format(configure_script) +
                        "{}{} ".format(prefix_arg, prefix_dir) +
                        "{} ".format(configure_params))
        execute_command("make")
        execute_command("make install")
        os.chdir(current_dir)

        return prefix_dir


    """Download CMake and store cmake executable path as cmake_binary class member."""
    def download_cmake(self, version="3.21.1"):
        if self.platform == "Linux":
            suffix = "Linux-x86_64.tar.gz"
            dirname = "cmake-{}-linux-x86_64".format(version)
            self.cmake_binary = os.path.join(dirname, "bin", "cmake")
        elif self.platform == "macOS":
            suffix = "Darwin-x86_64.tar.gz"
            dirname = "cmake-{}-Darwin-x86_64".format(version)
            self.cmake_binary = os.path.join(dirname, "CMake.app", "Contents", "bin", "cmake")
        elif self.platform == "Windows":
            suffix = "win64-x64.zip"
            dirname = "cmake-{}-win64-x64".format(version)
            self.cmake_binary = os.path.join(dirname, "bin", "cmake.exe")
        else:
            raise RuntimeError("Unknown platform {}".format(self.platform))

        url = "https://github.com/Kitware/CMake/releases/download/v{}/cmake-{}-{}".format(version, version, suffix)
        download_and_extract_archive(url=url, label="cmake")
        self.cmake_binary = os.path.abspath(self.cmake_binary)


    """Download Ninja build tools and store ninja executable path as ninja_binary class member."""
    def download_ninja(self, version="1.10.2"):
        if self.platform == "Linux":
            suffix = "linux.zip"
            self.ninja_binary = "ninja"
        elif self.platform == "macOS":
            suffix = "mac.zip"
            self.ninja_binary = "ninja"
        elif self.platform == "Windows":
            suffix = "win.zip"
            self.ninja_binary = "ninja.exe"
        else:
            raise RuntimeError("Unknown platform {}".format(self.platform))

        url = "https://github.com/ninja-build/ninja/releases/download/v{}/ninja-{}".format(version, suffix)
        download_and_extract_archive(url=url, label="ninja")
        self.ninja_binary = os.path.abspath(self.ninja_binary)


    def get_prefix(key):
        try:
            return self.prefixes[key]
        except KeyError:
            return ""


    def build_yaml_cpp(self, version="0.6.3", prefix_dir=None):
        url = "https://github.com/jbeder/yaml-cpp/archive/yaml-cpp-{}.tar.gz".format(version)
        download_and_extract_archive(url=url, label="yaml_cpp")

        source_dir = "yaml-cpp-yaml-cpp-{}".format(version)
        self.prefixes['yaml-cpp'] = self.build_cmake(source_dir=source_dir,
                                                     cmake_params="-D YAML_BUILD_SHARED_LIBS=ON "
                                                                  "-D YAML_CPP_BUILD_TESTS=OFF ",
                                                     prefix_dir=prefix_dir)


    def build_sqlpp11(self, version="0.60", prefix_dir=None):
        url = "https://github.com/rbock/sqlpp11/archive/{}.tar.gz".format(version)
        download_and_extract_archive(url=url, label="sqlpp11")

        source_dir = "sqlpp11-{}".format(version)
        self.prefixes['sqlpp11'] = self.build_cmake(source_dir=source_dir,
                                                    cmake_params="-D BUILD_TESTING=OFF",
                                                    prefix_dir=prefix_dir)


    def build_date(self, version="3.0.0", prefix_dir=None):
        url = "https://github.com/HowardHinnant/date/archive/v{}.tar.gz".format(version)
        download_and_extract_archive(url=url, label="date")

        source_dir = "date-{}".format(version)
        self.prefixes['date'] = self.build_cmake(source_dir=source_dir,
                                                 prefix_dir=prefix_dir)


    def build_sqlpp11_connector_mysql(self, version="0.29", prefix_dir=None):
        url = "https://github.com/rbock/sqlpp11-connector-mysql/archive/{}.tar.gz".format(version)
        download_and_extract_archive(url=url, label="sqlpp11_connector_mysql")

        sqlpp11_prefix = get_prefix("sqlpp11")
        date_prefix = get_prefix("date")

        source_dir = "sqlpp11-connector-mysql-{}".format(version)
        self.prefixes['sqlpp11-mysql'] = self.build_cmake(source_dir=source_dir,
                                                          cmake_params="-D ENABLE_TESTS=OFF " +
                                                                       "-D USE_MARIADB=TRUE " +
                                                                       "-D SQLPP11_INCLUDE_DIR={}/include ".format(sqlpp11_prefix) +
                                                                       "-D DATE_INCLUDE_DIR={}/include ".format(date_prefix) +
                                                                       "-D CMAKE_PREFIX_PATH=\"{};{}\" ".format(sqlpp11_prefix, date_prefix),
                                                          prefix_dir=prefix_dir)


    def build_catch2(self, version="2.13.4", prefix_dir=None):
        url = "https://github.com/catchorg/Catch2/archive/v{}.tar.gz".format(version)
        download_and_extract_archive(url=url, label="yaml")

        source_dir = "Catch2-{}".format(version)
        self.prefixes['catch2'] = self.build_cmake(source_dir=source_dir,
                                                   cmake_params="-D BUILD_TESTING=OFF ",
                                                   prefix_dir=prefix_dir)


    def build_boost(self, version="1.76.0", prefix_dir=None):
        current_dir = os.getcwd()

        version_major, version_minor, version_patch = version.split(".")
        url = "https://boostorg.jfrog.io/artifactory/main/release/{}.{}.{}/source/boost_{}_{}_{}.tar.bz2".format(version_major, version_minor, version_patch,
                                                                                                                 version_major, version_minor, version_patch)
        download_and_extract_archive(url=url, label="boost")

        source_dir = "boost_{}_{}_{}".format(version_major, version_minor, version_patch)
        prefix_dir = check_prefix_dif(prefix_dir, source_dir)

        os.chdir(source_dir)

        execute_command("chmod +x ./bootstrap.sh")
        execute_command("chmod +x ./tools/build/src/engine/build.sh")

        toolset = os.path.basename(self.c_compiler)
        execute_command('echo "using {} : : {} : ;" > user-config.jam'.format(toolset, self.cxx_compiler))

        execute_command("./bootstrap.sh " +
                        "--with-toolset={} ".format(toolset) +
                        "--without-libraries=python")

        execute_command('./b2 ' +
                        '--ignore-site-config ' +
                        '--user-config=./user-config.jam ' +
                        '--prefix={} '.format(prefix_dir) +
                        'toolset={} '.format(toolset) +
                        'variant=release ' +
                        'link=shared ' +
                        'threading=multi ' +
                        'install')

        os.chdir(current_dir)
        self.prefixes['boost'] = prefix_dir


    def build_cyrus_sasl(self, version="2.1.27", prefix_dir=None):
        url = "https://github.com/cyrusimap/cyrus-sasl/releases/download/cyrus-sasl-{}/cyrus-sasl-{}.tar.gz".format(version, version)
        download_and_extract_archive(url=url, label="cyrus_sasl")

        source_dir = "cyrus-sasl-{}".format(version)
        self.prefixes['cyrus-sasl'] = self.build_make(source_dir=source_dir,
                                                      configure_params="--disable-otp " +
                                                                       "--with-dblib=gdbm ",
                                                      prefix_dir=prefix_dir)


    def build_qt5base(self, version="5.15.2", prefix_dir=None):
        version_major, version_minor, version_patch = version.split(".")
        version_short = "{}.{}".format(version_major, version_minor)
        url = "http://download.qt.io/official_releases/qt/{}/{}/submodules/qtbase-everywhere-src-{}.tar.xz".format(version_short, version, version)
        download_and_extract_archive(url=url, label="qt5base")

        source_dir = "qtbase-everywhere-src-{}".format(version)
        self.prefixes['qt5base'] = self.build_make(source_dir=source_dir,
                                                   configure_params="-platform linux-g++ " +
                                                                    "-c++std c++17 "
                                                                    "-opensource " +
                                                                    "-confirm-license " +
                                                                    "-no-opengl " +
                                                                    "-nomake examples " +
                                                                    "-nomake tests ",
                                                   prefix_dir=prefix_dir,
                                                   prefix_arg="-prefix ")


def load_builder(filename="builder.pkl"):
    with open(filename, "rb") as picklefile:
        return pickle.load(picklefile)


def save_builder(builder, filename="builder.pkl"):
    with open(filename, 'wb') as picklefile:
        pickle.dump(builder, picklefile)
