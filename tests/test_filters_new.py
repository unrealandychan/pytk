"""Tests for new filters: MakeFilter, TerraformFilter, PackageManagerFilter."""
import pytest
from pytk.filters.make import MakeFilter
from pytk.filters.terraform import TerraformFilter
from pytk.filters.package_manager import PackageManagerFilter


# --- MakeFilter ---

class TestMakeFilter:
    def setup_method(self):
        self.f = MakeFilter()

    def test_strips_entering_leaving_directory(self):
        output = (
            "make[1]: Entering directory '/home/user/project'\n"
            "gcc -o main main.c\n"
            "make[1]: Leaving directory '/home/user/project'"
        )
        result = self.f.filter(output, ["make"])
        assert "Entering directory" not in result
        assert "Leaving directory" not in result
        assert "gcc -o main main.c" in result

    def test_strips_tab_echo_lines(self):
        output = (
            "Building target...\n"
            "\tgcc -Wall -o foo foo.c\n"
            "\techo done\n"
            "Build finished."
        )
        result = self.f.filter(output, ["make"])
        assert "\tgcc" not in result
        assert "\techo" not in result
        assert "Building target..." in result
        assert "Build finished." in result

    def test_error_lines_preserved(self):
        output = (
            "make[1]: Entering directory '/src'\n"
            "make: *** [Makefile:10: foo] Error 1\n"
            "make[1]: Leaving directory '/src'"
        )
        result = self.f.filter(output, ["make"])
        assert "Error 1" in result
        assert "Entering directory" not in result

    def test_matches_make_command(self):
        assert self.f.matches(["make"])
        assert self.f.matches(["make", "all"])
        assert not self.f.matches(["cmake"])
        assert not self.f.matches([])


# --- TerraformFilter ---

class TestTerraformFilter:
    def setup_method(self):
        self.f = TerraformFilter()

    def test_strips_refreshing_state(self):
        output = (
            "aws_instance.web: Refreshing state... [id=i-12345]\n"
            "aws_s3_bucket.data: Refreshing state... [id=mybucket]\n"
            "Plan: 1 to add, 0 to change, 0 to destroy."
        )
        result = self.f.filter(output, ["terraform"])
        assert "Refreshing state" not in result
        assert "Plan: 1 to add" in result

    def test_keeps_error_and_warning_lines(self):
        output = (
            "aws_instance.web: Refreshing state... [id=i-12345]\n"
            "Error: Invalid resource configuration\n"
            "Warning: deprecated attribute used"
        )
        result = self.f.filter(output, ["terraform"])
        assert "Error: Invalid resource configuration" in result
        assert "Warning: deprecated attribute used" in result

    def test_keeps_apply_complete(self):
        output = (
            "aws_instance.web: Refreshing state... [id=i-12345]\n"
            "Apply complete! Resources: 2 added, 0 changed, 0 destroyed.\n"
            "Changes to Outputs:\n"
            "  + ip = \"1.2.3.4\""
        )
        result = self.f.filter(output, ["terraform"])
        assert "Apply complete!" in result
        assert "Changes to Outputs:" in result

    def test_matches_terraform_command(self):
        assert self.f.matches(["terraform"])
        assert self.f.matches(["terraform", "apply"])
        assert not self.f.matches(["terragrunt"])
        assert not self.f.matches([])


# --- PackageManagerFilter ---

class TestPackageManagerFilter:
    def setup_method(self):
        self.f = PackageManagerFilter()

    def test_strips_download_progress(self):
        output = (
            "Collecting requests\n"
            "  Downloading requests-2.28.0-py3-none-any.whl 100%\n"
            "Successfully installed requests-2.28.0"
        )
        result = self.f.filter(output, ["pip"])
        assert "Downloading requests" not in result
        assert "Successfully installed requests-2.28.0" in result

    def test_strips_wheel_build_noise(self):
        output = (
            "Collecting mypackage\n"
            "  Building wheel for mypackage (setup.py)\n"
            "  Created wheel for mypackage\n"
            "  Stored in directory: /tmp/pip-wheels\n"
            "Successfully installed mypackage-1.0"
        )
        result = self.f.filter(output, ["pip"])
        assert "Building wheel" not in result
        assert "Created wheel" not in result
        assert "Stored in directory" not in result
        assert "Successfully installed mypackage-1.0" in result

    def test_keeps_error_and_warning(self):
        output = (
            "Collecting badpackage\n"
            "  Downloading badpackage-1.0.whl 50%\n"
            "ERROR: Could not find a version that satisfies the requirement badpackage\n"
            "WARNING: pip is configured with locations that require TLS/SSL"
        )
        result = self.f.filter(output, ["pip"])
        assert "ERROR: Could not find" in result
        assert "WARNING: pip is configured" in result

    def test_strips_block_char_progress(self):
        line_with_block = "  " + chr(9601) * 20 + " 45%"
        output = "Collecting foo\n" + line_with_block + "\nSuccessfully installed foo-1.0"
        result = self.f.filter(output, ["uv"])
        assert chr(9601) not in result
        assert "Successfully installed foo-1.0" in result

    def test_matches_commands(self):
        assert self.f.matches(["pip"])
        assert self.f.matches(["pip3"])
        # uv is now handled by UvFilter, not PackageManagerFilter
        assert self.f.matches(["poetry"])
        assert not self.f.matches(["npm"])
        assert not self.f.matches([])
