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
        # backends and sanitizers
        "enable_vulkan":     [True, False, None],
        "enable_d3d12":      [True, False, None],
        "enable_metal":      [True, False, None],
        "enable_d3d11":      [True, False, None],
        "enable_null":       [True, False, None],
        "enable_desktop_gl": [True, False, None],
        "enable_opengles":   [True, False, None],
        "enable_asan":       [True, False, None],
        "enable_tsan":       [True, False, None],
        "enable_msan":       [True, False, None],
        "enable_ubsan":      [True, False, None],
        # windowing flags
        "use_wayland":       [True, False, None],
        "use_x11":           [True, False, None],
        "use_glfw":          [True, False, None],
    }

    default_options = {
        # leave everything unset so Dawn’s own CMake defaults apply
        "enable_vulkan":     None,
        "enable_d3d12":      None,
        "enable_metal":      None,
        "enable_d3d11":      None,
        "enable_null":       None,
        "enable_desktop_gl": None,
        "enable_opengles":   None,
        "enable_asan":       None,
        "enable_tsan":       None,
        "enable_msan":       None,
        "enable_ubsan":      None,
        "use_wayland":       None,
        "use_x11":           None,
        "use_glfw":          None,
    }

    options_description = {
        "enable_vulkan":     "Force-enable the Vulkan backend",
        "enable_d3d12":      "Force-enable the D3D12 backend",
        "enable_metal":      "Force-enable the Metal backend",
        "enable_d3d11":      "Force-enable the D3D11 backend",
        "enable_null":       "Force-enable the Null backend",
        "enable_desktop_gl": "Force-enable the Desktop OpenGL backend",
        "enable_opengles":   "Force-enable the OpenGLES backend",
        "use_wayland":       "Force-enable Wayland support",
        "use_x11":           "Force-enable X11 support",
        "use_glfw":          "Force-enable GLFW in samples",
    }

    def config_options(self):
        # If you want to preserve Dawn’s macOS defaults even when unset:
        if self.settings.os == "Macos":
            if self.options.enable_vulkan is None:
                self.options.enable_vulkan = False
            if self.options.enable_metal is None:
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

        # Always-on build flags
        tc.variables["DAWN_ENABLE_INSTALL"]     = "ON"
        tc.variables["DAWN_FETCH_DEPENDENCIES"] = "ON"

        # Only inject a CMake cache var if the user set an option
        def maybe(var_name, opt):
            if opt is not None:
                tc.variables[var_name] = "ON" if opt else "OFF"

        # backends
        maybe("DAWN_ENABLE_VULKAN",     self.options.enable_vulkan)
        maybe("DAWN_ENABLE_D3D12",      self.options.enable_d3d12)
        maybe("DAWN_ENABLE_METAL",      self.options.enable_metal)
        maybe("DAWN_ENABLE_D3D11",      self.options.enable_d3d11)
        maybe("DAWN_ENABLE_NULL",       self.options.enable_null)
        maybe("DAWN_ENABLE_DESKTOP_GL", self.options.enable_desktop_gl)
        maybe("DAWN_ENABLE_OPENGLES",   self.options.enable_opengles)

        # sanitizers
        maybe("DAWN_ENABLE_ASAN", self.options.enable_asan)
        maybe("DAWN_ENABLE_TSAN", self.options.enable_tsan)
        maybe("DAWN_ENABLE_MSAN", self.options.enable_msan)
        maybe("DAWN_ENABLE_UBSAN",self.options.enable_ubsan)

        # windowing
        maybe("USE_WAYLAND", self.options.use_wayland)
        maybe("USE_X11",     self.options.use_x11)
        maybe("DAWN_USE_GLFW", self.options.use_glfw)

        # samples / tests / tint
        tc.variables["TINT_BUILD_SPV_READER"]  = "OFF"
        tc.variables["TINT_BUILD_CMD_TOOLS"]   = "OFF"
        tc.variables["TINT_BUILD_TESTS"]       = "OFF"
        tc.variables["TINT_BUILD_IR_BINARY"]   = "OFF"
        tc.variables["DAWN_BUILD_SAMPLES"]     = "OFF"

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cfg = {}
        if self.settings.os == "Windows":
            cfg["variables"] = {"CMAKE_CXX_FLAGS": "/utf-8"}
        cmake.configure(**cfg)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "dawn::webgpu_dawn")
        self.cpp_info.libs = ["webgpu_dawn"]

