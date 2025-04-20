import os
from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.scm import Git

class DawnConan(ConanFile):
    name        = "dawn"
    version     = "7069"
    license     = "Apache-2.0"
    author      = "Dawn Authors"
    url         = "https://dawn.googlesource.com/dawn"
    description = "Dawn is an open-source and cross-platform implementation of the WebGPU standard."
    topics      = ("conan", "dawn", "webgpu", "graphics", "gpu")

    settings = "os", "compiler", "build_type", "arch"

    options = {
        "enable_vulkan":  [True, False],
        "enable_d3d12":   [True, False],
        "enable_metal":   [True, False],
        "enable_d3d11":   [True, False],
        "enable_null":    [True, False],
        "enable_desktop_gl": [True, False],
        "enable_opengles":   [True, False],
    }

    default_options = {
        "enable_vulkan":     True,
        "enable_d3d12":      False,
        "enable_metal":      False,
        "enable_d3d11":      False,
        "enable_null":       False,
        "enable_desktop_gl": False,
        "enable_opengles":   False,
    }

    options_description = {
        "enable_vulkan":     "Build the Vulkan backend",
        "enable_d3d12":      "Build the D3D12 backend",
        "enable_metal":      "Build the Metal backend",
        "enable_d3d11":      "Build the D3D11 backend",
        "enable_null":       "Build the Null (reference) backend",
        "enable_desktop_gl": "Build the Desktop OpenGL backend",
        "enable_opengles":   "Build the OpenGLES backend",
    }

    def config_options(self):
        # On macOS, default to Metal and disable Vulkan
        if self.settings.os == "Macos":
            self.options.enable_vulkan = False
            self.options.enable_metal = True

    def layout(self):
        cmake_layout(self)

    def source(self):
        git = Git(self)
        git.clone(
            url="https://dawn.googlesource.com/dawn",
            args=["--branch", f"chromium/{self.version}"],
            target="."
        )

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")
        # core options
        tc.variables["DAWN_ENABLE_INSTALL"]     = "ON"
        tc.variables["DAWN_FETCH_DEPENDENCIES"] = "ON"
        # disable all backends by default, then enable per-option
        tc.variables["DAWN_ENABLE_D3D11"]      = "ON" if self.options.enable_d3d11      else "OFF"
        tc.variables["DAWN_ENABLE_D3D12"]      = "ON" if self.options.enable_d3d12      else "OFF"
        tc.variables["DAWN_ENABLE_NULL"]       = "ON" if self.options.enable_null       else "OFF"
        tc.variables["DAWN_ENABLE_DESKTOP_GL"] = "ON" if self.options.enable_desktop_gl else "OFF"
        tc.variables["DAWN_ENABLE_OPENGLES"]   = "ON" if self.options.enable_opengles   else "OFF"
        tc.variables["DAWN_ENABLE_VULKAN"]     = "ON" if self.options.enable_vulkan     else "OFF"
        tc.variables["DAWN_ENABLE_METAL"]      = "ON" if self.options.enable_metal      else "OFF"
        # Tint and samples
        tc.variables["TINT_BUILD_SPV_READER"]  = "OFF"
        tc.variables["TINT_BUILD_CMD_TOOLS"]   = "OFF"
        tc.variables["TINT_BUILD_TESTS"]       = "OFF"
        tc.variables["TINT_BUILD_IR_BINARY"]   = "OFF"
        tc.variables["DAWN_BUILD_SAMPLES"]     = "OFF"
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cfg_args = {}
        if self.settings.os == "Windows":
            cfg_args["variables"] = {"CMAKE_CXX_FLAGS": "/utf-8"}
        cmake.configure(**cfg_args)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "dawn::webgpu_dawn")
        self.cpp_info.libs = ["webgpu_dawn"]

