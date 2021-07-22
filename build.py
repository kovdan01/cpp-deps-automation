import os
import requests
import subprocess

#root = os.environ['ROOT_PATH']
#repo = os.environ['REPO_PATH']
#ninja_tool_path = os.environ['NINJA_TOOL_PATH']
#cmake_tool_binary_path = os.environ['CMAKE_TOOL_BINARY_PATH']
#cmake_binary = os.path.join(cmake_tool_binary_path, "cmake")
#ninja_binary = os.path.join(root, ninja_tool_path, "ninja")

cmake_binary="/usr/bin/cmake"
ninja_binary="/usr/bin/ninja"

try:
    c_compiler = os.environ["CC"]
except KeyError as e:
    c_compiler = "gcc"
try:
    cxx_compiler = os.environ["CXX"]
except KeyError as e:
    cxx_compiler = "g++"

def execute_command(cmd):
    ret = subprocess.call(cmd, shell=True)
    if ret != 0:
        raise RuntimeError('Exit code {} while executing "{}"'.format(ret, cmd))

def build_cmake(source_dir, cmake_params=None, prefix_dir=None,
                build_dir=None, build_type="Release"):    

    if prefix_dir is None:
        prefix_dir = os.path.join(os.path.abspath(source_dir), "prefix")
    if os.path.isdir(prefix_dir):
        raise RuntimeError("Prefix directory {} already exists".format(prefix_dir))
    os.mkdir(prefix_dir)
    
    if build_dir is None:
        build_dir = os.path.join(os.path.abspath(source_dir), "build")
    if os.path.isdir(build_dir):
        raise RuntimeError("Build directory {} already exists".format(build_dir))
    os.mkdir(build_dir)

    if cmake_params is None:
        cmake_params = ""

    execute_command("{} ".format(cmake_binary) +
                    "-S {} ".format(source_dir) +
                    "-B {} ".format(build_dir) +
                    "-G Ninja " +
                    "-D CMAKE_MAKE_PROGRAM={} ".format(ninja_binary) +
                    "-D CMAKE_INSTALL_PREFIX={} ".format(prefix_dir) +
                    "-D CMAKE_BUILD_TYPE={} ".format(build_type) +
                    "-D CMAKE_C_COMPILER={} ".format(c_compiler) +
                    "-D CMAKE_CXX_COMPILER={} ".format(cxx_compiler) +
                    "{} ".format(cmake_params))

    execute_command("{} --build {} --target install".format(cmake_binary, build_dir))
    
    return prefix_dir


def download_and_extract_library_sources(url, library_name="temp"):
    if url.endswith(".tar.gz"):
        archive_format = ".tar.gz"
    elif url.endswith(".tar.bz2"):
        archive_format = ".tar.bz2"
    elif url.endswith(".zip"):
        archive_format = ".zip"
    else:
        raise RuntimeError("Unknown archive type on URL {}".format(url))

    archive_name = library_name + archive_format
    print("Downloading {} from {}...".format(library_name, url))
    open(archive_name, "wb").write(requests.get(url, allow_redirects=True).content)
    print("Done!")

    if archive_format == ".zip":
        execute_command("7z x {}".format(archive_name))
    elif archive_format == ".tar.gz" or archive_format == ".tar.bz2":
        execute_command("tar -xf {}".format(archive_name))
    else:
        assert False


def build_yaml_cpp(version="0.6.3", prefix_dir=None):
    url = "https://github.com/jbeder/yaml-cpp/archive/yaml-cpp-{}.tar.gz".format(version)
    download_and_extract_library_sources(url=url, library_name="yaml")
    
    source_dir = "yaml-cpp-yaml-cpp-{}".format(version)
    return build_cmake(source_dir=source_dir,
                       cmake_params="-D YAML_BUILD_SHARED_LIBS=ON "
                                    "-D YAML_CPP_BUILD_TESTS=OFF ",
                       prefix_dir=prefix_dir)

def build_sqlpp11_base(version="0.60", prefix_dir=None):
    url = "https://github.com/rbock/sqlpp11/archive/{}.tar.gz".format(version)
    download_and_extract_library_sources(url=url, library_name="sqlpp11_base")
    
    source_dir = "sqlpp11-{}".format(version)
    return build_cmake(source_dir=source_dir,
                       cmake_params="-D BUILD_TESTING=OFF",
                       prefix_dir=prefix_dir)

def build_chrono_date(version="3.0.0", prefix_dir=None):
    url = "https://github.com/HowardHinnant/date/archive/v{}.tar.gz".format(version)
    download_and_extract_library_sources(url=url, library_name="chrono_date")
    
    source_dir = "date-{}".format(version)
    return build_cmake(source_dir=source_dir,
                       prefix_dir=prefix_dir)

def build_sqlpp11_connector_mysql(version="0.29", prefix_dir=None,
                                  sqlpp11_base_prefix="/usr", chrono_date_prefix="/usr"):
    url = "https://github.com/rbock/sqlpp11-connector-mysql/archive/{}.tar.gz".format(version)
    download_and_extract_library_sources(url=url, library_name="sqlpp11_connector_mysql")

    source_dir = "sqlpp11-connector-mysql-{}".format(version)
    return build_cmake(source_dir=source_dir,
                       cmake_params="-D ENABLE_TESTS=OFF " +
                                    "-D USE_MARIADB=TRUE " +
                                    "-D SQLPP11_INCLUDE_DIR={}/include ".format(sqlpp11_base_prefix) +
                                    "-D DATE_INCLUDE_DIR={}/include ".format(chrono_date_prefix) +
                                    "-D CMAKE_PREFIX_PATH={};{} ".format(sqlpp11_base_prefix, chrono_date_prefix),
                       prefix_dir=prefix_dir)

def build_catch2(version="2.13.4", prefix_dir=None):
    url = "https://github.com/catchorg/Catch2/archive/v{}.tar.gz".format(version)
    download_and_extract_library_sources(url=url, library_name="yaml")
    
    source_dir = "Catch2-{}".format(version)
    return build_cmake(source_dir=source_dir,
                       cmake_params="-D BUILD_TESTING=OFF ",
                       prefix_dir=prefix_dir)

def build_boost(version="1.76.0", prefix_dir=None):
    current_dir = os.getcwd()
    
    version_major, version_minor, version_patch = version.split(".")
    url = "https://boostorg.jfrog.io/artifactory/main/release/{}.{}.{}/source/boost_{}_{}_{}.tar.bz2".format(version_major, version_minor, version_patch,
                                                                                                             version_major, version_minor, version_patch)
    download_and_extract_library_sources(url=url, library_name="boost")
    
    source_dir = "boost_{}_{}_{}".format(version_major, version_minor, version_patch)
    
    if prefix_dir is None:
        prefix_dir = os.path.join(os.path.abspath(source_dir), "prefix")
    if os.path.isdir(prefix_dir):
        raise RuntimeError("Prefix directory {} already exists".format(prefix_dir))
    os.mkdir(prefix_dir)
    
    os.chdir(source_dir)

    execute_command("chmod +x ./bootstrap.sh")
    execute_command("chmod +x ./tools/build/src/engine/build.sh")

    toolset = os.path.basename(c_compiler)
    execute_command('echo "using {} : : {} : ;" > user-config.jam'.format(toolset, cxx_compiler))
    
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
    return prefix_dir

yaml_cpp_prefix = build_yaml_cpp()
sqlpp11_base_prefix = build_sqlpp11_base()
chrono_date_prefix = build_chrono_date()

# comment due to horrible dependencies resolution
# sqlpp11_connector_mysql_prefix = build_sqlpp11_connector_mysql(sqlpp11_base_prefix=sqlpp11_base_prefix,
#                                                                chrono_date_prefix=chrono_date_prefix)

catch2_prefix = build_catch2()

boost_prefix = build_boost()
