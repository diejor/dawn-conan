import os
from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.scm import Git
from conan.tools.files import copy, rm, rmdir

class DawnConan(ConanFile):
    name         = "dawn"
    version      = "7069"
    license      = "Apache-2.0"
    url          = "https://dawn.googlesource.com/dawn"
    description  = "Dawn is an open-source and cross-platform implementation of the WebGPU standard."
    topics       = ("conan", "dawn", "webgpu", "graphics", "gpu")

    settings     = "os", "compiler", "build_type", "arch"
    options      = {
        "shared":            [True, False],
        "fPIC":              [True, False],
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
    default_options = {
        "shared":            False,
        "fPIC":              True,
        "force_vulkan":      None,
        "force_d3d12":       None,
        "force_metal":       None,
        "force_d3d11":       None,
        "force_null":        None,
        "force_desktop_gl":  None,
        "force_opengles":    None,
        "force_asan":        None,
        "force_tsan":        None,
        "force_msan":        None,
        "force_ubsan":       None,
        "force_wayland":     None,
        "force_x11":         None,
        "force_glfw":        None,
    }

    generators = "CMakeDeps"

    def config_options(self):
        if self.settings.os == "Macos":
            if self.options.force_vulkan is None:
                self.options.force_vulkan = False
            if self.options.force_metal is None:
                self.options.force_metal = True

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def layout(self):
        cmake_layout(self)

    def source(self):
        git = Git(self)
        git.clone(
            url=self.url,
            args=[
                "--branch", f"chromium/{self.version}",
                "--single-branch", "--filter=blob:none",
                "--sparse", "--no-checkout", "--depth=1"
            ],
            target="."
        )
        self.run("git sparse-checkout init --no-cone")
        self.run("git sparse-checkout set '/*' '!/test'")
        self.run(f"git checkout chromium/{self.version}")
        rmdir(self, ".git")
        rmdir(self, "test")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CMAKE_POSITION_INDEPENDENT_CODE"]    = "ON"
        tc.cache_variables["BUILD_SHARED_LIBS"]                 = "OFF"
        tc.cache_variables["DAWN_BUILD_MONOLITHIC_LIBRARY"]     = "ON"
        tc.cache_variables["DAWN_ENABLE_INSTALL"]               = "ON"
        tc.cache_variables["DAWN_FETCH_DEPENDENCIES"]           = "ON"

        def _map(opt, var):
            val = getattr(self.options, opt)
            if val is True:
                tc.cache_variables[var] = "ON"
            elif val is False:
                tc.cache_variables[var] = "OFF"

        # backends
        for opt, var in [
            ("force_vulkan",     "DAWN_ENABLE_VULKAN"),
            ("force_d3d12",      "DAWN_ENABLE_D3D12"),
            ("force_metal",      "DAWN_ENABLE_METAL"),
            ("force_d3d11",      "DAWN_ENABLE_D3D11"),
            ("force_null",       "DAWN_ENABLE_NULL"),
            ("force_desktop_gl", "DAWN_ENABLE_DESKTOP_GL"),
            ("force_opengles",   "DAWN_ENABLE_OPENGLES"),
        ]:
            _map(opt, var)

        # sanitizers
        for opt, var in [
            ("force_asan",  "DAWN_ENABLE_ASAN"),
            ("force_tsan",  "DAWN_ENABLE_TSAN"),
            ("force_msan",  "DAWN_ENABLE_MSAN"),
            ("force_ubsan", "DAWN_ENABLE_UBSAN"),
        ]:
            _map(opt, var)

        # windowing
        for opt, var in [
            ("force_wayland", "DAWN_USE_WAYLAND"),
            ("force_x11",     "DAWN_USE_X11"),
            ("force_glfw",    "DAWN_USE_GLFW"),
        ]:
            _map(opt, var)

        # disable tests/tools/samples
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
        cmake = CMake(self)
        cmake.install()

        cfg = str(self.settings.build_type)
        src_dir = os.path.join(self.build_folder, "build", cfg, "src", "dawn")
        copy(self, "libdawn_*.a", src_dir, os.path.join(self.package_folder, "lib"), keep_path=False)

        # remove the shared plugin
        rm(self, "*.so*", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        # overall package name and alias
        self.cpp_info.set_property("cmake_file_name", "Dawn")
        self.cpp_info.set_property("cmake_target_name", "dawn::dawncpp")

        # define individual components
        components = {
            "dawn_common":     [],
            "dawn_native":     ["dawn_common"],
            "dawn_wgpu_utils": ["dawn_native"],
            "dawn_proc":       ["dawn_wgpu_utils"],
            "dawn_wire":       ["dawn_common"],
            "dawn_platform":   ["dawn_common"],
            "dawn_glfw":       ["dawn_platform"],
        }

        for name, requires in components.items():
            comp = self.cpp_info.components[name]
            comp.libs = [name]
            comp.set_property("cmake_target_name", f"dawn::{name}")
            comp.requires = [f"dawn::{r}" for r in requires]

        # alias pulling them all in
        alias = self.cpp_info.components["dawncpp"]
        alias.set_property("cmake_target_name", "dawn::dawncpp")
        alias.requires = [f"dawn::{n}" for n in components]

