import os
from conans import ConanFile, tools
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps
from pathlib import Path
import subprocess


class FaissTestConan(ConanFile):
    name = "FaissTest"
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps"
    # requires = ("hdf5/1.12.1", "lz4/1.9.2")
    exports = "CMakeLists.txt", "example.cpp"

    def generate(self):
        print("Generating toolchain")
        tc = CMakeToolchain(self)
        tc.variables["faiss_ROOT"] = Path(
            self.deps_cpp_info["faiss"].rootpath
        ).as_posix()
        # if self.settings.os == "Macos":
        #     proc = subprocess.run(
        #         "brew --prefix libomp", shell=True, capture_output=True
        #     )
        #     tc.variables["OpenMP_ROOT"] = Path(
        #         proc.stdout.decode("UTF-8").strip()
        #     ).as_posix()
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not tools.cross_building(self.settings):
            if self.settings.os == "Windows":
                self.run(str(Path(Path.cwd(), "Release", "example.exe")))
            else:
                self.run(str(Path(Path.cwd(), "example")))
