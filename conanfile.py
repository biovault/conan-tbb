from conans import ConanFile, tools
from conan.tools.cmake import CMakeDeps, CMake, CMakeToolchain
from conans import tools
import os
import shutil
from pathlib import Path, PurePosixPath
import subprocess

required_conan_version = ">=1.62.0"


class Lz4Conan(ConanFile):
    name = "lz4"
    version = "1.10.0"
    license = "MIT"
    author = "B. van Lew b.van_lew@lumc.nl"
    url = "https://github.com/biovault/conan-lz4"
    description = """LZ4 is lossless compression algorithm, providing 
        compression speed > 500 MB/s per core, scalable with multi-cores CPU."""
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
        self.run("git clone https://github.com/lz4/lz4.git")
        os.chdir("./lz4")
        self.run(f"git checkout tags/v{self.version}")
        os.chdir("build/cmake")
        # Prevent early resolution of CMAKE_INSTALL_LIBDIR in variable by prefix with \
        tools.replace_in_file("CMakeLists.txt", "set(LZ4_PKG_INSTALLDIR \"${CMAKE_INSTALL_LIBDIR}/cmake/lz4\")", "set(LZ4_PKG_INSTALLDIR \"\${CMAKE_INSTALL_LIBDIR}/cmake/lz4\")")
        # Allow linking against lz4::lz4 
        tools.replace_in_file("lz4Config.cmake.in", """
include( "${CMAKE_CURRENT_LIST_DIR}/lz4Targets.cmake" )""", """
include( "${CMAKE_CURRENT_LIST_DIR}/lz4Targets.cmake" )
if(NOT TARGET lz4::lz4)
    add_library(lz4::lz4 INTERFACE IMPORTED)
    if("@BUILD_SHARED_LIBS@")
        set_target_properties(lz4::lz4 PROPERTIES INTERFACE_LINK_LIBRARIES LZ4::lz4_shared)
    else()
        set_target_properties(lz4::lz4 PROPERTIES INTERFACE_LINK_LIBRARIES LZ4::lz4_static)
    endif()
endif()""")
        
    
    
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
        tc.variables["BUILD_STATIC_LIBS"] = "True"

        return tc

    def layout(self):
        # Cause the libs and bin to be output to separate subdirs
        # based on build configuration.
        self.cpp.package.libdirs = ["lib/$<CONFIG>"]
        self.cpp.package.bindirs = ["bin/$<CONFIG>"]


    def generate(self):
        print("In generate")
        tc = self._get_tc()
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder="lz4/build/cmake")
        cmake.verbose = True
        return cmake

    def build(self):
        # Build both release and debug for dual packaging
        cmake_debug = self._configure_cmake()
        cmake_debug.build(build_type="Debug")

        cmake_release = self._configure_cmake()
        cmake_release.build(build_type="Release")

        cmake_relwdeb = self._configure_cmake()
        cmake_relwdeb.build(build_type="RelWithDebInfo")

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
        if ((build_type == "Debug") or (build_type == "RelWithDebInfo")) and (
            self.settings.compiler == "Visual Studio"
        ):
            # the debug info
            self.copy("*.pdb", src=src_dir, dst=dst_lib, keep_path=False)

    def package(self):
        #self.copy("*.h", src="lz4/lib", dst="include", keep_path=True)
        print(f"********** package dir {self.package_folder}")
        # Debug
        self._pkg_bin("Debug")
        # Release
        self._pkg_bin("Release")
        # RelWithDebInfo
        self._pkg_bin("RelWithDebInfo")
        # In lz4Targets.cmake th variable _IMPORT_PATH assumes that the files 
        # are in lib/cmake/lz4 one level deeper than cmake/lz4
        # Move cmake dir under lib.
        shutil.move(Path(self.package_folder, "cmake"), Path(self.package_folder, "lib", "cmake"))

