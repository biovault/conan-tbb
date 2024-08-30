from conans import ConanFile, tools
from conan.tools.cmake import CMakeDeps, CMake, CMakeToolchain
from conans.tools import os_info, SystemPackageTool, get_env
import os
import shutil
from pathlib import Path, PurePosixPath
import subprocess

required_conan_version = ">=1.51.0"


class FaissConan(ConanFile):
    name = "faiss"
    version = "1.7.3"
    license = "MIT"
    author = "B. van Lew b.van_lew@lumc.nl"
    url = "https://github.com/biovault/conan-faiss"
    description = """Faiss is a library for efficient 
    similarity search and clustering of dense vectors."""
    topics = ("clustering", "similarity")
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "testing": [True, False]}
    default_options = {"shared": True, "testing": False}
    generators = "CMakeDeps"
    exports = "cmake/*"
    # provide BLAS_ROOT - 
    # On Windows side load this dependency with nuget 
    # e.g. D:/temp/testopenblas/OpenBLAS.0.2.14.1/lib/native
    # with sub dirs bin libb include
    BLAS_ROOT = Path(os.environ.get("BLAS_ROOT", ""))

    def source(self):
        self.run("git clone https://github.com/facebookresearch/faiss.git")
        os.chdir("./faiss")
        self.run(f"git checkout tags/v{self.version}")
        os.chdir("..")

    def _get_tc(self):
        """Generate the CMake configuration using
        multi-config generators on all platforms, as follows:

        Windows - defaults to Visual Studio
        Macos - XCode
        Linux - Ninja Multi-Config

        CMake needs to be at least 3.17 for Ninja Multi-Config

        Returns:
            CMakeToolchain: a configured toolchain object
        """
        generator = None
        if self.settings.os == "Macos":
            generator = "Xcode"

        if self.settings.os == "Linux":
            generator = "Ninja Multi-Config"

        tc = CMakeToolchain(self, generator=generator)
        tc.variables["FAISS_ENABLE_PYTHON "] = "OFF"
        tc.variables["FAISS_ENABLE_GPU "] = "OFF"
        tc.variables["BUILD_TESTING"] = "ON" if self.options.testing else "OFF"
        tc.variables["BUILD_SHARED_LIBS"] = "ON" if self.options.shared else "OFF"

        if self.settings.os == "Windows":
            # tc.variables["MKL_ROOT_DIR"] = "D:/intelmkl"
            tc.variables["BLA_STATIC"] = "ON"
            tc.variables["BLAS_LIBRARY:FILEPATH"] = PurePosixPath(self.BLAS_ROOT / "lib/x64/libopenblas.dll.a")
            tc.variables["BLAS_LIBRARIES"] = PurePosixPath(self.BLAS_ROOT /  "lib/x64/libopenblas.dll.a")
            tc.variables["LAPACK_LIBRARY:FILEPATH"] = PurePosixPath(self.BLAS_ROOT / "lib/x64/libopenblas.dll.a")
            tc.variables["LAPACK_LIBRARIES"] = PurePosixPath(self.BLAS_ROOT / "lib/x64/libopenblas.dll.a")

            #tc.variables["BLAS_DIR"] = "D:/temp/testopenblasOpenBLAS.0.2.14.1/lib/native"
            #tc.variables["BLAS_LIBRARY"] = "D:/temp/testopenblasOpenBLAS.0.2.14.1/lib/native/lib/x64/libopenblas.dll.a"
            #tc.variables["LAPACK_LIBRARY"] = "D:/temp/testopenblasOpenBLAS.0.2.14.1/lib/native/lib/x64/libopenblas.dll.a"

        if self.settings.os == "Linux":
            tc.variables["CMAKE_CONFIGURATION_TYPES"] = "Debug;Release;RelWithDebInfo"

        if self.settings.os == "Macos":
            proc = subprocess.run(
                "brew --prefix libomp", shell=True, capture_output=True
            )
            prefix_path = f"{proc.stdout.decode('UTF-8').strip()}"
            tc.variables["OpenMP_ROOT"] = prefix_path

        tc.variables["CMAKE_CXX_STANDARD"] = "17"

        return tc

    def layout(self):
        # Cause the libs and bin to be output to separate subdirs
        # based on build configuration.
        self.cpp.package.libdirs = ["lib/$<CONFIG>"]
        self.cpp.package.bindirs = ["bin/$<CONFIG>"]

    def system_requirements(self):
        if self.settings.os == "Macos":
            installer = SystemPackageTool()
            installer.install("libomp")
            # Make the brew OpenMP findable with a symlink
            proc = subprocess.run("brew --prefix libomp",  shell=True, capture_output=True)
            subprocess.run(f"ln {proc.stdout.decode('UTF-8').strip()}/lib/libomp.dylib /usr/local/lib/libomp.dylib", shell=True)

    def generate(self):
        print("In generate")
        tc = self._get_tc()
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="faiss")
        cmake.verbose = True
        return cmake

    def build(self):
        # list(TRANSFORM CMAKE_MODULE_PATH PREPEND ${{CMAKE_CURRENT_SOURCE_DIR}}/../cmake)
#         if self.settings.os == "Windows":         
#             line_to_replace = 'set(MKL_LIBRARIES)'
#             tools.replace_in_file("faiss/cmake/FindMKL.cmake", line_to_replace,
#                               '''{}
# set(ENV{{MKLROOT}} "D:/intelmkl/intelmkl.devel.win-x64.2023.2.0.49496" ) 
# message(STATUS "**************In faiss ${{CMAKE_CURRENT_LIST_FILE}} *************")
# '''.format(line_to_replace))
            
#             line_to_replace = 'if(NOT ${_LIBRARIES})'
#             tools.replace_in_file("faiss/cmake/FindMKL.cmake", line_to_replace,
#                               '''message(STATUS "**************MKL In libs search ${{IT}} == ${{BLAS_mkl_MKLROOT}} == ${{BLAS_mkl_LIB_PATH_SUFFIXES}}*************")
#                               {}
# '''.format(line_to_replace))
        
        # Build both release and debug for dual packaging
        cmake_debug = self._configure_cmake()
        cmake_debug.build(build_type="Debug")
        cmake_debug.install(build_type="Debug")

        cmake_release = self._configure_cmake()
        cmake_release.build(build_type="Release")
        cmake_release.install(build_type="Release")

        cmake_relwdeb = self._configure_cmake()
        cmake_relwdeb.build(build_type="RelWithDebInfo")
        cmake_relwdeb.install(build_type="RelWithDebInfo")

    # Package has no build type marking
    def package_id(self):
        del self.info.settings.build_type
        if self.settings.compiler == "Visual Studio":
            del self.info.settings.compiler.runtime

    # Package contains its own cmake config file
    def package_info(self):
        self.cpp_info.set_property("skip_deps_file", True)
        self.cpp_info.set_property("cmake_config_file", True)

    def _pkg_bin(self, build_type):
        src_dir = f"{self.build_folder}/lib/{build_type}"
        dst_lib = f"lib/{build_type}"
        dst_bin = f"bin/{build_type}"

        self.copy("*.dll", src=src_dir, dst=dst_bin, keep_path=False)
        self.copy("*.so", src=src_dir, dst=dst_lib, keep_path=False)
        self.copy("*.dylib", src=src_dir, dst=dst_lib, keep_path=False)
        self.copy("*.a", src=src_dir, dst=dst_lib, keep_path=False)
        if ((build_type == "Debug") or (build_type == "RelWithDebInfo")) and (
            self.settings.compiler == "Visual Studio"
        ):
            # the debug info
            self.copy("*.pdb", src=src_dir, dst=dst_lib, keep_path=False)

        if self.settings.compiler == "Visual Studio":
            # the blas dll to the package
            blas_dir = PurePosixPath(self.BLAS_ROOT / "bin/x64/")
            self.copy("*.dll", src=blas_dir, dst=dst_bin, keep_path=False)


    def package(self):
        # cleanup excess installs - this is a kludge TODO fix cmake
        print("cleanup")
        for child in Path(self.package_folder, "lib").iterdir():
            if child.is_file():
                child.unlink()
        print("end cleanup")
        self.copy("*.h", src="faiss/src/cpp", dst="include", keep_path=True)
        self.copy("*.hpp", src="faiss/src/cpp", dst="include", keep_path=True)

        # Debug
        self._pkg_bin("Debug")
        # Release
        self._pkg_bin("Release")
        # RelWithDebInfo
        self._pkg_bin("RelWithDebInfo")
