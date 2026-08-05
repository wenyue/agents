import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / 'scripts' / 'sync_plugin_version.py'


def write_json(root: Path, relative_path: str, value: dict) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def load_json(root: Path, relative_path: str) -> dict:
    return json.loads((root / relative_path).read_text(encoding='utf-8'))


def create_repository_fixture(root: Path, stored_version: str = '0.0.0') -> None:
    root.joinpath('VERSION').write_text(
        '2.3.4-beta.1+build.5\n', encoding='utf-8'
    )
    for relative_path in (
        '.codex-plugin/plugin.json',
        '.cursor-plugin/plugin.json',
        'plugin.json',
    ):
        write_json(
            root,
            relative_path,
            {'name': 'smartkit', 'version': stored_version},
        )
    for relative_path in (
        '.cursor-plugin/marketplace.json',
        '.github/plugin/marketplace.json',
    ):
        write_json(
            root,
            relative_path,
            {
                'metadata': {'version': stored_version},
                'plugins': [
                    {'name': 'unrelated', 'version': '9.9.9'},
                    {'name': 'smartkit', 'version': stored_version},
                ],
            },
        )
    write_json(
        root,
        'setup-assets/catalog/assets.json',
        {'plugin': {'id': 'smartkit', 'version': stored_version}},
    )


class SyncPluginVersionTest(unittest.TestCase):
    def test_syncs_every_plugin_version_from_version_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_repository_fixture(root)

            result = subprocess.run(
                [sys.executable, str(SCRIPT), '--root', str(root)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('2.3.4-beta.1+build.5', result.stdout)
            for relative_path in (
                '.codex-plugin/plugin.json',
                '.cursor-plugin/plugin.json',
                'plugin.json',
            ):
                self.assertEqual(
                    load_json(root, relative_path)['version'],
                    '2.3.4-beta.1+build.5',
                )
            for relative_path in (
                '.cursor-plugin/marketplace.json',
                '.github/plugin/marketplace.json',
            ):
                marketplace = load_json(root, relative_path)
                self.assertEqual(
                    marketplace['metadata']['version'],
                    '2.3.4-beta.1+build.5',
                )
                self.assertEqual(
                    marketplace['plugins'][1]['version'],
                    '2.3.4-beta.1+build.5',
                )
                self.assertEqual(
                    marketplace['plugins'][0]['version'],
                    '9.9.9',
                )
            self.assertEqual(
                load_json(root, 'setup-assets/catalog/assets.json')['plugin'][
                    'version'
                ],
                '2.3.4-beta.1+build.5',
            )

    def test_check_reports_drift_without_modifying_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            create_repository_fixture(root, stored_version='2.3.4-beta.1+build.5')

            current = subprocess.run(
                [sys.executable, str(SCRIPT), '--root', str(root), '--check'],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(current.returncode, 0, current.stderr)
            self.assertIn('up to date', current.stdout.lower())

            manifest_path = root / '.codex-plugin/plugin.json'
            manifest = load_json(root, '.codex-plugin/plugin.json')
            manifest['version'] = '0.0.0'
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + '\n', encoding='utf-8'
            )

            stale = subprocess.run(
                [sys.executable, str(SCRIPT), '--root', str(root), '--check'],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(stale.returncode, 1)
            self.assertIn('.codex-plugin/plugin.json', stale.stderr)
            self.assertEqual(
                load_json(root, '.codex-plugin/plugin.json')['version'],
                '0.0.0',
            )


if __name__ == '__main__':
    unittest.main()
