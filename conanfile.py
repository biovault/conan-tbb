from conans import ConanFile, tools
from conan.tools.cmake import CMakeDeps, CMake, CMakeToolchain
from conans import tools
import os
import shutil
from pathlib import Path, PurePosixPath
import subprocess

required_conan_version = ">=1.62.0"


class tbbConan(ConanFile):
    name = "tbb"
    version = "2021.13.0"
    license = "MIT"
    author = "B. van Lew b.van_lew@lumc.nl"
    url = "https://github.com/biovault/conan-tbb"
    description = """oneTBB is a flexible C++ library that  
        simplifies the work of adding parallelism to complex applications."""
    topics = ("parallel", "multicore")
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "testing": [True, False]}
    default_options = {"shared": True, "testing": False}
    generators = "CMakeDeps"
    exports = "cmake/*"

    def source(self):
        self.run("git clone https://github.com/oneapi-src/oneTBB.git")
        os.chdir("./oneTBB")
        self.run(f"git checkout tags/v{self.version}")
        # tools.replace_in_file(Path(Path.cwd(), "./cmake", "utils.cmake"), "${CMAKE_INSTALL_LIBDIR}", "\${CMAKE_INSTALL_LIBDIR}")
         
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
        if self.settings.os == "Linux":
            tc.variables["CMAKE_CONFIGURATION_TYPES"] = "Debug;Release;RelWithDebInfo"

        tc.variables["CMAKE_CXX_STANDARD"] = "17"
        tc.variables["TBB_TEST"] = "OFF"
        tc.variables["TBB_STRICT"] = "OFF"

        return tc

    def layout(self):
        # Cause the libs and bin to be output to separate subdirs
        # based on build configuration.
        pass
        # self.cpp.package.libdirs = ["lib/$<CONFIG>"]
        # self.cpp.package.bindirs = ["bin/$<CONFIG>"]


    def generate(self):
        print("In generate")
        tc = self._get_tc()
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="oneTBB")
        cmake.verbose = True
        return cmake

    def build(self):
        # Build both release and debug for dual packaging
        cmake_debug = self._configure_cmake()
        cmake_debug.build(build_type="Debug")

        cmake_release = self._configure_cmake()
        cmake_release.build(build_type="Release")

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
        cmake = self._configure_cmake()
        cmake.install(build_type=build_type)

        src_dir = f"{build_type}"
        dst_lib = f"lib/{build_type}"
        #dst_bin = f"bin/{build_type}"

        #self.copy("*.lib", dst=dst_lib, keep_path=False)
        #self.copy("*.a", dst=dst_lib, keep_path=False)
        #self.copy("*.exe", dst=dst_bin, keep_path=False)
        #self.copy("*.dll", dst=dst_bin, keep_path=False)
        if (build_type == "Debug") and (
            self.settings.compiler == "Visual Studio"
        ):
            # the debug info
            self.copy("*.pdb", src=src_dir, dst=dst_lib, keep_path=False)

    def package(self):
        print(f"********** package dir {self.package_folder}")
        # Debug
        self._pkg_bin("Debug")
        # Release
        self._pkg_bin("Release")


