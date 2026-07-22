import hashlib
import os
import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ("test.yml", "lint.yml", "build.yml", "acceptance.yml", "release.yml")


class RepositoryContractTest(unittest.TestCase):
    def test_python_and_uv_versions_are_exact_and_aligned(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())

        python_version = (ROOT / ".python-version").read_text().strip()
        uv_version = (ROOT / ".uv-version").read_text().strip()
        self.assertEqual(f"=={python_version}", project["project"]["requires-python"])
        self.assertEqual(
            [f"uv_build=={uv_version}"], project["build-system"]["requires"]
        )
        self.assertEqual(["waitress==3.0.2"], project["project"]["dependencies"])
        self.assertEqual(
            ["coverage==7.15.2", "ruff==0.15.22"], project["dependency-groups"]["dev"]
        )
        self.assertEqual("0.0.0", project["project"]["version"])
        bootstrap_lock = (ROOT / "vendor" / "bootstrap-tools.lock.txt").read_text()
        self.assertIn("pip==25.2", bootstrap_lock)

    def test_release_version_and_container_are_immutable(self):
        self.assertRegex((ROOT / "VERSION").read_text().strip(), r"^v\d+\.\d+\.\d+$")
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn(
            "FROM python:3.14.0-slim@sha256:5af4c7f950774a1abf3fd4e8e3fc95f4d0fe684c7fdc1eb10777fc5a017371c7",
            dockerfile,
        )
        from_lines = [
            line for line in dockerfile.splitlines() if line.startswith("FROM ")
        ]
        self.assertEqual(1, len(from_lines))
        self.assertRegex(from_lines[0], r"^FROM [^@\s]+@sha256:[0-9a-f]{64}$")

    def test_workflows_use_immutable_actions_and_safe_checkout(self):
        action_ref = re.compile(r"uses:\s+[^\s@]+@([^\s#]+)")
        for workflow_name in WORKFLOWS:
            text = (ROOT / ".github" / "workflows" / workflow_name).read_text()
            refs = action_ref.findall(text)
            self.assertTrue(refs, workflow_name)
            self.assertTrue(
                all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in refs), workflow_name
            )
            self.assertNotIn("runs-on: ubuntu-latest", text)
            self.assertIn("runs-on: ubuntu-24.04", text)
            self.assertIn('PIP_DISABLE_PIP_VERSION_CHECK: "1"', text)
            self.assertIn(
                "PIP_FIND_LINKS: ${{ github.workspace }}/vendor/cache/python/linux-x86_64",
                text,
            )
            self.assertIn('PIP_NO_INDEX: "1"', text)
            self.assertEqual(
                text.count("actions/checkout@"),
                text.count("persist-credentials: false"),
                workflow_name,
            )

    def test_fence_is_the_first_step_in_every_job(self):
        for workflow_name in WORKFLOWS:
            lines = (
                (ROOT / ".github" / "workflows" / workflow_name)
                .read_text()
                .splitlines()
            )
            for index, line in enumerate(lines):
                if line.strip() == "steps:":
                    next_line = next(
                        candidate.strip()
                        for candidate in lines[index + 1 :]
                        if candidate.strip()
                    )
                    self.assertTrue(
                        next_line.startswith("- uses: openai/fence@"),
                        f"{workflow_name}: {next_line}",
                    )

    def test_vendored_wheels_are_binary_and_hash_locked(self):
        lock_text = "\n".join(
            (ROOT / "vendor" / name).read_text()
            for name in (
                "requirements.lock.txt",
                "runtime-requirements.lock.txt",
                "bootstrap-tools.lock.txt",
            )
        )
        platform_packages = []
        for platform in ("macos-arm64", "linux-x86_64"):
            files = sorted((ROOT / "vendor" / "cache" / "python" / platform).iterdir())
            self.assertTrue(files, platform)
            self.assertTrue(all(path.suffix == ".whl" for path in files), platform)
            packages = set()
            for path in files:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertIn(f"sha256:{digest}", lock_text, path.name)
                packages.add(path.name.split("-")[0].replace("_", "-").lower())
            platform_packages.append(packages)
        self.assertEqual(platform_packages[0], platform_packages[1])

    def test_repository_scripts_are_executable_and_hidden_from_linguist(self):
        scripts = [path for path in (ROOT / "script").iterdir() if path.is_file()]
        self.assertTrue(scripts)
        self.assertTrue(all(os.access(path, os.X_OK) for path in scripts))
        attributes = (ROOT / ".gitattributes").read_text()
        self.assertIn("script/** -linguist-detectable", attributes)
        self.assertIn("vendor/** linguist-vendored", attributes)


if __name__ == "__main__":
    unittest.main()
