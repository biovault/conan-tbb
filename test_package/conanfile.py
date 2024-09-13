import os
from conans import ConanFile, tools
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps
from pathlib import Path
import subprocess


class TbbTestConan(ConanFile):
    name = "TBBTest"
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps"
    requires = ("tbb/2021.13.0")
    exports = "CMakeLists.txt", "example.cpp"

    def generate(self):
        print("Generating toolchain")
        tc = CMakeToolchain(self)
        # Use the packaged cmake files in the test
        tc.variables["TBB_ROOT"] = Path(
            self.deps_cpp_info["tbb"].rootpath, "lib", "cmake", "TBB"
        ).as_posix()

        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure() # cli_args=["--trace-expand", "--trace-format=human"])
        cmake.build() # cli_args=["--verbose"])

    # Get package libraries into the executable directory
    def imports(self):
        self.copy("*.dll", dst=".", src="bin")
        self.copy("*.dylib*", dst=".", src="lib")
        self.copy('*.so*', dst='.', src='lib')

    def test(self):
        if not tools.cross_building(self.settings):
            if self.settings.os == "Windows":
                self.run(str(Path(Path.cwd(), "Release", "example.exe")))
            else:
                self.run(str(Path(Path.cwd(), "example")))
