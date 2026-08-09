import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'update_external_skills.py'


def load_module():
    spec = importlib.util.spec_from_file_location('update_external_skills', SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError('cannot load update_external_skills')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_skill(root: Path, relative: str, name: str, marker: str) -> None:
    skill = root / relative
    skill.mkdir(parents=True)
    (skill / 'SKILL.md').write_text(
        f'---\nname: {name}\ndescription: Test fixture.\n---\n\n# {name}\n\n{marker}\n',
        encoding='utf-8',
    )


class ExternalSkillsUpdaterTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    @staticmethod
    def registry(sources):
        return {
            'version': 1,
            'custom': [{'id': 'smartkit/custom', 'path': 'custom'}],
            'external_sources': sources,
        }

    @staticmethod
    def source(source_id: str, skill_name: str) -> dict[str, object]:
        return {
            'id': source_id,
            'url': f'https://github.com/{source_id}',
            'license': {'spdx': 'MIT', 'path': 'LICENSE'},
            'skills': [{
                'id': f'{source_id.split("/", 1)[0]}/{skill_name}',
                'path': f'skills/{skill_name}',
            }],
        }

    def prepare_two_source_project(self):
        project = self.root / 'project'
        alpha = self.root / 'alpha-upstream'
        beta = self.root / 'beta-upstream'
        write_skill(project, 'skills/custom', 'custom', 'custom')
        for upstream, name in ((alpha, 'alpha'), (beta, 'beta')):
            write_skill(upstream, f'skills/{name}', name, 'version one')
            (upstream / 'LICENSE').write_text(
                'MIT License\n\nPermission is hereby granted, free of charge.\n',
                encoding='utf-8',
            )
        registry = self.registry([
            self.source('acme/alpha-source', 'alpha'),
            self.source('example/beta-source', 'beta'),
        ])
        (project / 'skills/registry.json').write_text(
            json.dumps(registry), encoding='utf-8'
        )
        checkouts = {
            'acme/alpha-source': self.module.ResolvedCheckout(alpha, 'main', '1' * 40),
            'example/beta-source': self.module.ResolvedCheckout(beta, 'main', '2' * 40),
        }
        self.assertEqual(
            self.module.main(
                ['--update', '--root', str(project)],
                resolver=lambda source: checkouts[source.id],
            ),
            0,
        )
        return project, alpha, beta, registry, checkouts

    def test_update_installs_selected_source_and_preserves_custom_skill(self):
        project = self.root / 'project'
        upstream = self.root / 'upstream'
        write_skill(project, 'skills/setup-project-agents', 'setup-project-agents', 'custom')
        write_skill(upstream, 'skills/alpha', 'alpha', 'external')
        (upstream / 'LICENSE').write_text(
            'MIT License\n\nPermission is hereby granted, free of charge, to any person '
            'obtaining a copy of this software.\n',
            encoding='utf-8',
        )
        registry = {
            'version': 1,
            'custom': [
                {'id': 'smartkit/setup-project-agents', 'path': 'setup-project-agents'}
            ],
            'external_sources': [
                {
                    'id': 'acme/skills',
                    'url': 'https://github.com/acme/skills',
                    'ref': 'main',
                    'license': {'spdx': 'MIT', 'path': 'LICENSE'},
                    'skills': [{'id': 'acme/alpha', 'path': 'skills/alpha'}],
                }
            ],
        }
        (project / 'skills').mkdir(exist_ok=True)
        (project / 'skills/registry.json').write_text(
            json.dumps(registry), encoding='utf-8'
        )

        checkout = self.module.ResolvedCheckout(
            root=upstream,
            resolved_ref='main',
            commit='a' * 40,
        )
        result = self.module.main(
            ['--update', '--root', str(project)],
            resolver=lambda source: checkout,
        )

        self.assertEqual(result, 0)
        self.assertIn(
            'custom',
            (project / 'skills/setup-project-agents/SKILL.md').read_text(encoding='utf-8'),
        )
        self.assertIn(
            'external',
            (project / 'skills/alpha/SKILL.md').read_text(encoding='utf-8'),
        )
        lock = json.loads(
            (project / 'vendor/external-skills.lock.json').read_text(encoding='utf-8')
        )
        self.assertEqual(lock['sources'][0]['id'], 'acme/skills')
        self.assertEqual(lock['sources'][0]['commit'], 'a' * 40)
        self.assertEqual(lock['sources'][0]['skills'][0]['id'], 'acme/alpha')
        self.assertTrue((project / 'licenses/acme-skills-LICENSE.txt').is_file())

        self.assertEqual(
            self.module.main(
                ['--check', '--root', str(project)],
                resolver=lambda source: checkout,
            ),
            0,
        )
        (project / 'skills/alpha/SKILL.md').write_text('drift\n', encoding='utf-8')
        self.assertEqual(
            self.module.main(
                ['--check', '--root', str(project)],
                resolver=lambda source: checkout,
            ),
            1,
        )

    def test_update_rolls_back_every_touched_path(self):
        project = self.root / 'project'
        upstream = self.root / 'upstream'
        write_skill(project, 'skills/custom', 'custom', 'custom')
        write_skill(upstream, 'skills/alpha', 'alpha', 'external')
        (upstream / 'LICENSE').write_text(
            'MIT License\n\nPermission is hereby granted, free of charge.\n',
            encoding='utf-8',
        )
        (project / 'skills/registry.json').write_text(
            json.dumps({
                'version': 1,
                'custom': [{'id': 'smartkit/custom', 'path': 'custom'}],
                'external_sources': [{
                    'id': 'acme/skills',
                    'url': 'https://github.com/acme/skills',
                    'license': {'spdx': 'MIT', 'path': 'LICENSE'},
                    'skills': [{'id': 'acme/alpha', 'path': 'skills/alpha'}],
                }],
            }),
            encoding='utf-8',
        )
        registry = self.module.load_registry(project)
        checkout = self.module.ResolvedCheckout(upstream, 'main', 'b' * 40)
        snapshots = {'acme/skills': self.module.load_source_snapshot(
            registry.external_sources[0], checkout
        )}
        desired_lock = self.module._desired_lock(
            registry, snapshots, None, selected_source=None
        )
        calls = 0

        def fail_second(staged, target):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('injected failure')
            self.module.replace_path(staged, target)

        with self.assertRaisesRegex(self.module.UpdateError, 'transaction failed'):
            self.module.update_repository(
                project,
                registry,
                snapshots,
                desired_lock,
                selected_source=None,
                replace=fail_second,
            )
        self.assertFalse((project / 'skills/alpha').exists())
        self.assertFalse((project / 'vendor/external-skills.lock.json').exists())
        self.assertIn(
            'custom',
            (project / 'skills/custom/SKILL.md').read_text(encoding='utf-8'),
        )

    def test_staging_failure_does_not_touch_installed_skills(self):
        project = self.root / 'project'
        upstream = self.root / 'upstream'
        write_skill(project, 'skills/custom', 'custom', 'custom')
        write_skill(upstream, 'skills/alpha', 'alpha', 'version one')
        write_skill(upstream, 'skills/beta', 'beta', 'version one')
        (upstream / 'LICENSE').write_text(
            'MIT License\n\nPermission is hereby granted, free of charge.\n',
            encoding='utf-8',
        )
        (project / 'skills/registry.json').write_text(
            json.dumps({
                'version': 1,
                'custom': [{'id': 'smartkit/custom', 'path': 'custom'}],
                'external_sources': [{
                    'id': 'acme/skills',
                    'url': 'https://github.com/acme/skills',
                    'license': {'spdx': 'MIT', 'path': 'LICENSE'},
                    'skills': [
                        {'id': 'acme/alpha', 'path': 'skills/alpha'},
                        {'id': 'acme/beta', 'path': 'skills/beta'},
                    ],
                }],
            }),
            encoding='utf-8',
        )
        registry = self.module.load_registry(project)
        checkout = self.module.ResolvedCheckout(upstream, 'main', 'd' * 40)
        initial_snapshots = {'acme/skills': self.module.load_source_snapshot(
            registry.external_sources[0], checkout
        )}
        initial_lock = self.module._desired_lock(
            registry, initial_snapshots, None, selected_source=None
        )
        self.module.update_repository(
            project,
            registry,
            initial_snapshots,
            initial_lock,
            selected_source=None,
        )

        for name in ('alpha', 'beta'):
            skill = upstream / 'skills' / name / 'SKILL.md'
            skill.write_text(
                skill.read_text(encoding='utf-8').replace('version one', 'version two'),
                encoding='utf-8',
            )
        updated_checkout = self.module.ResolvedCheckout(upstream, 'main', 'e' * 40)
        updated_snapshots = {'acme/skills': self.module.load_source_snapshot(
            registry.external_sources[0], updated_checkout
        )}
        updated_lock = self.module._desired_lock(
            registry, updated_snapshots, initial_lock, selected_source=None
        )
        copytree = self.module.shutil.copytree

        def fail_while_staging_beta(source, destination, *args, **kwargs):
            if Path(source).name == 'beta' and 'staging' in Path(destination).parts:
                raise OSError('injected staging failure')
            return copytree(source, destination, *args, **kwargs)

        with mock.patch.object(
            self.module.shutil,
            'copytree',
            side_effect=fail_while_staging_beta,
        ):
            with self.assertRaisesRegex(self.module.UpdateError, 'transaction failed'):
                self.module.update_repository(
                    project,
                    registry,
                    updated_snapshots,
                    updated_lock,
                    selected_source=None,
                )

        for name in ('alpha', 'beta'):
            self.assertIn(
                'version one',
                (project / 'skills' / name / 'SKILL.md').read_text(encoding='utf-8'),
            )

    def test_all_source_cli_failure_leaves_every_source_unchanged(self):
        project, alpha, _, _, checkouts = self.prepare_two_source_project()
        alpha_skill = alpha / 'skills/alpha/SKILL.md'
        alpha_skill.write_text(
            alpha_skill.read_text(encoding='utf-8').replace('version one', 'version two'),
            encoding='utf-8',
        )
        checkouts['acme/alpha-source'] = self.module.ResolvedCheckout(
            alpha, 'main', '3' * 40
        )

        def fail_second(source):
            if source.id == 'example/beta-source':
                raise self.module.UpdateError('injected second-source failure')
            return checkouts[source.id]

        self.assertEqual(
            self.module.main(
                ['--update', '--root', str(project)], resolver=fail_second
            ),
            2,
        )
        self.assertIn('version one', (project / 'skills/alpha/SKILL.md').read_text())
        self.assertIn('version one', (project / 'skills/beta/SKILL.md').read_text())
        lock = json.loads((project / 'vendor/external-skills.lock.json').read_text())
        self.assertEqual([item['commit'] for item in lock['sources']], ['1' * 40, '2' * 40])

    def test_focused_cli_update_and_stale_source_removal(self):
        project, alpha, _, registry, checkouts = self.prepare_two_source_project()
        alpha_skill = alpha / 'skills/alpha/SKILL.md'
        alpha_skill.write_text(
            alpha_skill.read_text(encoding='utf-8').replace('version one', 'version two'),
            encoding='utf-8',
        )
        selected = self.module.ResolvedCheckout(alpha, 'main', '4' * 40)

        def selected_only(source):
            self.assertEqual(source.id, 'acme/alpha-source')
            return selected

        self.assertEqual(
            self.module.main(
                [
                    '--update', '--source', 'acme/alpha-source',
                    '--root', str(project),
                ],
                resolver=selected_only,
            ),
            0,
        )
        self.assertIn('version two', (project / 'skills/alpha/SKILL.md').read_text())
        self.assertIn('version one', (project / 'skills/beta/SKILL.md').read_text())
        focused_lock = json.loads(
            (project / 'vendor/external-skills.lock.json').read_text()
        )
        self.assertEqual(
            [item['commit'] for item in focused_lock['sources']],
            ['4' * 40, '2' * 40],
        )

        registry['external_sources'] = registry['external_sources'][:1]
        (project / 'skills/registry.json').write_text(
            json.dumps(registry), encoding='utf-8'
        )
        self.assertEqual(
            self.module.main(
                ['--update', '--root', str(project)],
                resolver=lambda source: selected,
            ),
            0,
        )
        self.assertFalse((project / 'skills/beta').exists())
        self.assertFalse(
            (project / 'licenses/example-beta-source-LICENSE.txt').exists()
        )
        stale_lock = json.loads(
            (project / 'vendor/external-skills.lock.json').read_text()
        )
        self.assertEqual([item['id'] for item in stale_lock['sources']], ['acme/alpha-source'])

    def test_ambient_credentials_never_enter_outputs_or_diagnostics(self):
        project = self.root / 'project'
        upstream = self.root / 'upstream'
        secret = 'credential-that-must-not-leak'
        write_skill(project, 'skills/custom', 'custom', 'custom')
        write_skill(upstream, 'skills/alpha', 'alpha', 'external')
        (upstream / 'LICENSE').write_text(
            'MIT License\nPermission is hereby granted, free of charge.\n',
            encoding='utf-8',
        )
        (project / 'skills/registry.json').write_text(
            json.dumps(self.registry([self.source('acme/source', 'alpha')])),
            encoding='utf-8',
        )
        checkout = self.module.ResolvedCheckout(upstream, 'main', '5' * 40)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, {'GH_TOKEN': secret}), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            result = self.module.main(
                ['--update', '--root', str(project)], resolver=lambda source: checkout
            )
        self.assertEqual(result, 0)
        observable = stdout.getvalue() + stderr.getvalue()
        observable += (project / 'vendor/external-skills.lock.json').read_text()
        self.assertNotIn(secret, observable)

    def test_shared_ref_resolver_distinguishes_default_branch_tag_and_sha(self):
        contract = self.module.resolve_ref

        def runner(arguments):
            if arguments[1:3] == ('--symref', 'https://github.com/acme/source'):
                return 'ref: refs/heads/trunk\tHEAD\n' + 'a' * 40 + '\tHEAD'
            if '--heads' in arguments:
                return 'b' * 40 if arguments[-1] == 'feature' else ''
            if '--tags' in arguments:
                return 'c' * 40 if arguments[-1].endswith('/v1') else ''
            return ''

        default = contract('https://github.com/acme/source', None, runner)
        branch = contract('https://github.com/acme/source', 'feature', runner)
        tag = contract('https://github.com/acme/source', 'v1', runner)
        commit = contract('https://github.com/acme/source', 'd' * 40, runner)
        self.assertEqual((default.resolved_ref, default.ref_kind), ('trunk', 'branch'))
        self.assertEqual(branch.ref_kind, 'branch')
        self.assertEqual(tag.ref_kind, 'tag')
        self.assertEqual(commit.ref_kind, 'commit')

    def test_lock_rejects_destinations_outside_managed_roots(self):
        malicious = {
            'version': 1,
            'sources': [{
                'id': 'acme/skills',
                'license': {'destination': '../../outside'},
                'skills': [],
            }],
        }
        with self.assertRaisesRegex(
            self.module.UpdateError, 'invalid license destination'
        ):
            self.module._lock_sources(malicious)

    def test_rejects_an_unrecognized_spdx_license(self):
        with self.assertRaisesRegex(self.module.UpdateError, 'unsupported SPDX'):
            self.module._license_matches('GPL-3.0-only', b'GPL-3.0-only')

    def test_selected_skill_rejects_a_symlinked_ancestor(self):
        upstream = self.root / 'upstream'
        outside = self.root / 'outside'
        write_skill(outside, 'alpha', 'alpha', 'outside')
        upstream.mkdir()
        (upstream / 'skills').symlink_to(outside, target_is_directory=True)
        (upstream / 'LICENSE').write_text(
            'MIT License\nPermission is hereby granted, free of charge.\n',
            encoding='utf-8',
        )
        source = self.module.ExternalSource(
            'acme/skills',
            'https://github.com/acme/skills',
            'main',
            self.module.LicenseSpec('MIT', self.module.PurePosixPath('LICENSE')),
            (self.module.ExternalSkill(
                'acme/alpha', 'alpha', self.module.PurePosixPath('skills/alpha')
            ),),
        )
        checkout = self.module.ResolvedCheckout(upstream, 'main', 'c' * 40)
        with self.assertRaisesRegex(self.module.UpdateError, 'contains a symlink'):
            self.module.load_source_snapshot(source, checkout)


if __name__ == '__main__':
    unittest.main()
