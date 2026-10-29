"""Keep repeated source builds free of obsolete hashed panel assets."""

from pathlib import Path
from shutil import rmtree

from setuptools import setup
from setuptools.command.build_py import build_py


class CurrentPanelBuild(build_py):
    def run(self):
        if not self.dry_run and not self.editable_mode:
            panel = Path(self.build_lib) / "canovatwin" / "web"
            if panel.is_symlink():
                panel.unlink()
            elif panel.exists():
                rmtree(panel)
        super().run()


setup(cmdclass={"build_py": CurrentPanelBuild})
