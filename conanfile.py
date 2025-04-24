import os
from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.scm import Git
from conan.tools.files import get, rmdir

class DawnConan(ConanFile):
    name        = "dawn"
    version     = "7069"
    license     = "Apache-2.0"
    url         = "https://dawn.googlesource.com/dawn"
    description = "Dawn is an open-source and cross-platform implementation of the WebGPU standard."
    topics      = ("conan", "dawn", "webgpu", "graphics", "gpu")

    settings = "os", "compiler", "build_type", "arch"

    options = {
        # backends
        "force_vulkan":     [True, False, None],
        "force_d3d12":      [True, False, None],
        "force_metal":      [True, False, None],
        "force_d3d11":      [True, False, None],
        "force_null":       [True, False, None],
        "force_desktop_gl": [True, False, None],
        "force_opengles":   [True, False, None],
        # sanitizers
        "force_asan":       [True, False, None],
        "force_tsan":       [True, False, None],
        "force_msan":       [True, False, None],
        "force_ubsan":      [True, False, None],
        # windowing
        "force_wayland":    [True, False, None],
        "force_x11":        [True, False, None],
        "force_glfw":       [True, False, None],
    }

    # All unset by default—lets Dawn’s CMakeLists pick its own defaults
    default_options = {
        "force_vulkan":     None,
        "force_d3d12":      None,
        "force_metal":      None,
        "force_d3d11":      None,
        "force_null":       None,
        "force_desktop_gl": None,
        "force_opengles":   None,
        "force_asan":       None,
        "force_tsan":       None,
        "force_msan":       None,
        "force_ubsan":      None,
        "force_wayland":    None,
        "force_x11":        None,
        "force_glfw":       None,
    }

    def config_options(self):
        if self.settings.os == "Macos":
            if self.options.force_vulkan is None:
                self.options.force_vulkan = False
            if self.options.force_metal is None:
                self.options.force_metal = True

    def layout(self):
        cmake_layout(self)

    def source(self):
        git = Git(self)
        git.clone(
            url="https://dawn.googlesource.com/dawn",
            args=[
                "--branch", f"chromium/{self.version}",
                "--single-branch",
                "--filter=blob:none",
                "--sparse",
                "--no-checkout",
                "--depth=1",
            ],
            target="."
        )
        self.run("git sparse-checkout init --no-cone")
        self.run("git sparse-checkout set '/*' '!/test'")
        self.run(f"git checkout chromium/{self.version}")
        rmdir(self, ".git")
        rmdir(self, "test")

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")

        tc.cache_variables["DAWN_ENABLE_INSTALL"]     = "ON"
        tc.cache_variables["DAWN_FETCH_DEPENDENCIES"] = "ON"

        # Map any forced options into DAWN_ENABLE_*/USE_* cache vars
        def _force(opt_name, cmake_var):
            val = getattr(self.options, opt_name)
            if val is True:
                tc.cache_variables[cmake_var] = "ON"
            elif val is False:
                tc.cache_variables[cmake_var] = "OFF"

        # Backends
        _force("force_vulkan",     "DAWN_ENABLE_VULKAN")
        _force("force_d3d12",      "DAWN_ENABLE_D3D12")
        _force("force_metal",      "DAWN_ENABLE_METAL")
        _force("force_d3d11",      "DAWN_ENABLE_D3D11")
        _force("force_null",       "DAWN_ENABLE_NULL")
        _force("force_desktop_gl", "DAWN_ENABLE_DESKTOP_GL")
        _force("force_opengles",   "DAWN_ENABLE_OPENGLES")

        # Sanitizers
        _force("force_asan",  "DAWN_ENABLE_ASAN")
        _force("force_tsan",  "DAWN_ENABLE_TSAN")
        _force("force_msan",  "DAWN_ENABLE_MSAN")
        _force("force_ubsan", "DAWN_ENABLE_UBSAN")

        # Windowing
        _force("force_wayland", "DAWN_USE_WAYLAND")
        _force("force_x11",     "DAWN_USE_X11")
        _force("force_glfw",    "DAWN_USE_GLFW")

        # Always-off for package
        for f in (
            "TINT_BUILD_SPV_READER",
            "TINT_BUILD_CMD_TOOLS",
            "TINT_BUILD_TESTS",
            "TINT_BUILD_IR_BINARY",
            "DAWN_BUILD_SAMPLES",
            "DAWN_BUILD_TESTS",
        ):
            tc.cache_variables[f] = "OFF"

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        CMake(self).install()

    def package_info(self):
        self.cpp_info.set_property("cmake_target_name", "dawn::webgpu_dawn")
        self.cpp_info.libs = ["webgpu_dawn"]

