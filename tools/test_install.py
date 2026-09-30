#!/usr/bin/env python3
"""Install contract tests: install.sh and update.sh agree, and a fresh install validates.

The first test reads both scripts and checks that every CCGG-owned tools file
update.sh syncs is one install.sh copies (the probe lists are installed once and
never synced, by design). The second runs install.sh into an empty `git init`
repository and asserts the validator passes there on the first run — F002's
fresh-install criterion, previously stated and never tested.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_env  # noqa: E402  (the bash that runs shell code; never the WSL launcher)

BASH = audit_env.bash_path()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL_FILE_RE = re.compile(r"tools/[A-Za-z0-9_]+\.(?:py|json|txt)")


_GUIDE_COPY: str | None = None


def guide_copy() -> str:
    """This working tree, copied to a temporary git repository with no remote.

    update.sh first refreshes the clone it lives in: with CCGG_REF unset that is a
    `git pull --ff-only`. Run from ROOT, it pulled the checkout under test forward to
    its upstream's tip in the middle of the suite — CI re-run on db59dc1 then read
    #108's validate.py from disk while the imported module was db59dc1's, and failed
    on a check that commit does not have (2026-09-30). A copy with no remote has
    nothing to pull, and still carries uncommitted changes, which a clone would not.
    """
    global _GUIDE_COPY
    if _GUIDE_COPY is None:
        import atexit
        import shutil
        dest = tempfile.mkdtemp(prefix="ccgg-guide-copy-")
        atexit.register(shutil.rmtree, dest, True)
        listing = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                                 cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
        for rel in filter(None, listing.split("\0")):
            src = os.path.join(ROOT, rel)
            if os.path.isfile(src):
                os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
                shutil.copy2(src, os.path.join(dest, rel))
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@local",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@local")
        for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "commit", "-q", "-m", "guide copy"]):
            subprocess.run(cmd, cwd=dest, env=env, check=True, capture_output=True)
        _GUIDE_COPY = dest
    return _GUIDE_COPY


def update_sh() -> str:
    return os.path.join(guide_copy(), "update.sh")


def tool_files(script: str) -> set[str]:
    with open(os.path.join(ROOT, script), encoding="utf-8") as fh:
        body = "\n".join(ln for ln in fh.read().splitlines() if not ln.lstrip().startswith("#"))
    return set(TOOL_FILE_RE.findall(body))


class InstallSetTests(unittest.TestCase):
    def test_update_syncs_only_what_install_copies(self):
        installed = tool_files("install.sh")
        synced = tool_files("update.sh")
        self.assertTrue(synced <= installed, f"update.sh syncs files install.sh never copies: {sorted(synced - installed)}")
        self.assertEqual(installed, synced,
                         "every tools file install.sh copies is also handled by update.sh "
                         "(synced, or for the probe contracts installed once when absent)")

    def test_probe_contracts_are_installed_once_never_overwritten(self):
        # The project's own contracts: update.sh may create them for a project
        # wired before they existed, but never replaces an existing copy.
        with open(os.path.join(ROOT, "update.sh"), encoding="utf-8") as fh:
            body = fh.read()
        block = body[body.index("tools/probes.txt tools/redteam_probes.txt"):]
        block = block[: block.index("done")]
        self.assertIn('[ ! -e "$TARGET/$f" ]', block, "probe contracts are copied only when absent")
        self.assertNotIn("sync_file", block, "probe contracts are never passed to sync_file")

    def test_hook_count_label_matches_hooks_shipped(self):
        hooks = [f for f in os.listdir(os.path.join(ROOT, ".claude", "hooks")) if f.endswith(".sh")]
        with open(os.path.join(ROOT, "install.sh"), encoding="utf-8") as fh:
            label = re.search(r'\.claude/hooks/ \((\d+) hooks', fh.read())
        self.assertIsNotNone(label, "install.sh names the hook count it copies")
        self.assertEqual(int(label.group(1)), len(hooks))


class FreshInstallTests(unittest.TestCase):
    def test_fresh_install_validates_on_first_run(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-install-") as tmp:
            target = os.path.join(tmp, "project")
            os.makedirs(target)
            env = dict(os.environ, HOME=os.path.join(tmp, "home"), GIT_CONFIG_NOSYSTEM="1",
                       GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@local", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@local")
            os.makedirs(env["HOME"])
            subprocess.run(["git", "init", "-q"], cwd=target, env=env, check=True)
            install = subprocess.run([BASH, os.path.join(ROOT, "install.sh"), target], env=env,
                                     capture_output=True, text=True)
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
            self.assertNotIn("validator reported findings", install.stdout)
            subprocess.run(["git", "add", "-A"], cwd=target, env=env, check=True)
            gate = subprocess.run([sys.executable, "tools/validate.py"], cwd=target, env=env, capture_output=True, text=True)
            self.assertEqual(gate.returncode, 0, gate.stdout)
            for rel in (".claude/skills/ccgg-audit/SKILL.md", ".claude/agents/audit-verifier.md",
                        ".claude/hooks/audit-verifier-guard.sh", "tools/probes.txt", "tools/audit_vocab.json",
                        "tools/audit_headless.py", "tools/audit_agents_json.py",
                        ".github/workflows/audit.yml"):
                self.assertTrue(os.path.exists(os.path.join(target, rel)), rel)
            for rel in (".claude/skills/gbb/SKILL.md", ".claude/skills/gbb/design-intent.md",
                        ".claude/skills/gbb/design-council.md", ".claude/skills/gbb/design-ownership.md",
                        ".claude/skills/gbb/gbb-ladder.md", ".claude/skills/gbb/research-protocol.md"):
                self.assertTrue(os.path.exists(os.path.join(target, rel)),
                                f"{rel} — a skill's companions ship with it or the skill is broken downstream")


class SkillDeliveryTests(unittest.TestCase):
    """Skills arrive one directory at a time, so a project with a skill of its own
    still gets the rest.

    install.sh used to test for the .claude/skills directory and skip the whole
    set when it existed. Any project that had written a single skill of its own
    therefore received no skills at all, which is the drop-in contract failing
    on exactly the projects most likely to adopt this.
    """

    def _install_into(self, tmp, existing: str | None):
        target = os.path.join(tmp, "project")
        if existing:
            d = os.path.join(target, ".claude", "skills", existing)
            os.makedirs(d)
            open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8").write(
                f"---\nname: {existing}\ndescription: THEIRS\n---\n\nTheir body.\n")
        else:
            os.makedirs(target)
        env = dict(os.environ, HOME=os.path.join(tmp, "home"))
        os.makedirs(env["HOME"], exist_ok=True)
        proc = subprocess.run([BASH, os.path.join(ROOT, "install.sh"), target], env=env,
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return target, proc.stdout

    def _shipped(self) -> set[str]:
        root = os.path.join(ROOT, ".claude", "skills")
        return {n for n in os.listdir(root) if os.path.isdir(os.path.join(root, n))}

    def test_a_project_with_its_own_skill_still_gets_every_ccgg_skill(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-skills-") as tmp:
            target, _ = self._install_into(tmp, "design-critic")
            delivered = set(os.listdir(os.path.join(target, ".claude", "skills")))
            self.assertTrue(self._shipped() <= delivered,
                            f"missing after install: {sorted(self._shipped() - delivered)}")
            self.assertIn("design-critic", delivered, "the project's own skill is left in place")

    def test_a_name_collision_keeps_the_projects_version(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-skills-") as tmp:
            target, out = self._install_into(tmp, "debug")
            body = open(os.path.join(target, ".claude", "skills", "debug", "SKILL.md"),
                        encoding="utf-8").read()
            self.assertIn("THEIRS", body, "a skill the project already has under our name is theirs")
            self.assertIn("the project already has", out, "the installer says what it left alone")

    def test_an_empty_project_gets_everything(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-skills-") as tmp:
            target, _ = self._install_into(tmp, None)
            delivered = set(os.listdir(os.path.join(target, ".claude", "skills")))
            self.assertEqual(delivered, self._shipped())


class UpdateReportsTests(unittest.TestCase):
    """update.sh says which of the two happened, because it advises a different fix.

    Every non-zero exit from the catalog tool used to read as "tables are
    stale", so a project whose own skill the tool could not parse was told to
    run a command that failed the same way.
    """

    def _project(self, tmp):
        target = os.path.join(tmp, "project")
        os.makedirs(target)
        env = dict(os.environ, HOME=os.path.join(tmp, "home"), GIT_CONFIG_NOSYSTEM="1",
                   GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@local",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@local")
        os.makedirs(env["HOME"])
        subprocess.run(["git", "init", "-q"], cwd=target, env=env, check=True)
        install = subprocess.run([BASH, os.path.join(ROOT, "install.sh"), target], env=env,
                                 capture_output=True, text=True)
        self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
        return target, env

    def _update(self, target, env):
        proc = subprocess.run([BASH, update_sh(), target], env=env,
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc.stdout + proc.stderr

    def _project_skill(self, target, *, house_keys: bool, description: bool = True) -> None:
        d = os.path.join(target, ".claude", "skills", "project-only")
        os.makedirs(d, exist_ok=True)
        body = "---\nname: project-only\n" + ("description: a skill this project wrote\n" if description else "")
        if house_keys:
            body += 'when_to_use: local\nargument-hint: "[x]"\npurpose: "A skill this project wrote"\n'
        body += "---\n\nBody.\n"
        open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8").write(body)

    def test_unparsable_project_skill_is_not_reported_as_stale(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-update-") as tmp:
            target, env = self._project(tmp)
            self._project_skill(target, house_keys=False, description=False)
            out = self._update(target, env)
            self.assertIn("could not read every skill", out)
            self.assertIn("project-only", out)
            self.assertNotIn("STALE", out)
            self.assertNotIn("--write", out)

    def test_stale_table_is_reported_as_stale(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-update-") as tmp:
            target, env = self._project(tmp)
            self._project_skill(target, house_keys=True)
            out = self._update(target, env)
            self.assertIn("STALE", out)
            self.assertIn("--write", out)
            self.assertNotIn("could not read every skill", out)

    def test_current_project_reports_neither(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-update-") as tmp:
            target, env = self._project(tmp)
            out = self._update(target, env)
            self.assertNotIn("STALE", out)
            self.assertNotIn("could not read every skill", out)

    def test_the_advised_command_actually_repairs_it(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-update-") as tmp:
            target, env = self._project(tmp)
            self._project_skill(target, house_keys=True)
            self.assertIn("STALE", self._update(target, env))
            fix = subprocess.run([sys.executable, "tools/catalog.py", "--write"], cwd=target,
                                 env=env, capture_output=True, text=True)
            self.assertEqual(fix.returncode, 0, fix.stdout + fix.stderr)
            self.assertNotIn("STALE", self._update(target, env))


def _git_env(tmp):
    env = dict(os.environ, HOME=os.path.join(tmp, "home"), GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@local",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@local")
    os.makedirs(env["HOME"], exist_ok=True)
    return env


def _git(target, env, *args):
    return subprocess.run(["git", *args], cwd=target, env=env, capture_output=True,
                          text=True, check=True).stdout


def _install(target, env):
    proc = subprocess.run([BASH, os.path.join(ROOT, "install.sh"), target], env=env,
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout


def _hook_modes(target, env):
    return {line.split("\t")[1]: line.split()[0]
            for line in _git(target, env, "ls-files", "-s", ".claude/hooks").splitlines()}


class TestsNeverPullTheCheckoutTests(unittest.TestCase):
    """update.sh pulls the clone it lives in. The suite must never run it from the
    checkout under test, or a re-run of an old commit tests a mix of old and new."""

    def test_the_guide_copy_has_nothing_to_pull_from(self):
        remotes = subprocess.run(["git", "remote"], cwd=guide_copy(), capture_output=True, text=True).stdout
        self.assertEqual(remotes.strip(), "")

    def test_the_guide_copy_carries_the_working_tree(self):
        with open(os.path.join(ROOT, "update.sh"), "rb") as a, open(update_sh(), "rb") as b:
            self.assertEqual(a.read(), b.read(), "uncommitted edits are what a test run should exercise")

    def test_running_update_leaves_the_checkout_where_it_was(self):
        head = lambda: subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout
        before = head()
        with tempfile.TemporaryDirectory(prefix="ccgg-nopull-") as tmp:
            env = dict(_git_env(tmp), CLAUDE_CONFIG_DIR=os.path.join(tmp, "config"))
            subprocess.run([BASH, update_sh(), "--user"], env=env, capture_output=True, text=True)
        self.assertEqual(head(), before)

    def test_no_test_file_runs_update_sh_from_the_checkout(self):
        here = os.path.dirname(os.path.abspath(__file__))
        for name in sorted(os.listdir(here)):
            if not (name.startswith("test_") and name.endswith(".py")):
                continue
            with open(os.path.join(here, name), encoding="utf-8") as fh:
                text = fh.read()
            with self.subTest(file=name):
                self.assertNotRegex(text, r'\[BASH, os\.path\.join\(ROOT, "update\.sh"\)')


class PersonalInstallTests(unittest.TestCase):
    """S3-1: personal skills override every project's same-named copy, and a stale set
    kept running /ship and /deploy in every wired project. The run says so."""

    def test_a_personal_install_warns_that_it_overrides_projects(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-user-") as tmp:
            env = dict(_git_env(tmp), CLAUDE_CONFIG_DIR=os.path.join(tmp, "config"))
            proc = subprocess.run([BASH, update_sh(), "--user"], env=env,
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("override same-named project skills", proc.stdout)
            self.assertTrue(os.path.isfile(os.path.join(tmp, "config", "skills", "commit", "SKILL.md")))


class ProjectOwnSkillTests(unittest.TestCase):
    """S4-1 end to end: an installed project adds an ordinary Claude Code skill — name
    and description only — and its own gate still passes once the catalog is
    regenerated. It used to fail on three house keys and a catalog refusal."""

    def test_a_plain_project_skill_passes_the_installed_gate(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-s41-") as tmp:
            target = os.path.join(tmp, "project")
            os.makedirs(target)
            env = _git_env(tmp)
            _git(target, env, "init", "-q")
            _install(target, env)
            d = os.path.join(target, ".claude", "skills", "release-notes")
            os.makedirs(d)
            with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as fh:
                fh.write("---\nname: release-notes\ndescription: Draft release notes. Use on tags.\n---\n\nBody.\n")
            write = subprocess.run([sys.executable, "tools/catalog.py", "--write"], cwd=target,
                                   env=env, capture_output=True, text=True)
            self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
            _git(target, env, "add", "-A")
            gate = subprocess.run([sys.executable, "tools/validate.py"], cwd=target, env=env,
                                  capture_output=True, text=True)
            self.assertEqual(gate.returncode, 0, gate.stdout)
            with open(os.path.join(target, "AGENTS.md"), encoding="utf-8") as fh:
                self.assertIn("| `/release-notes` | Draft release notes. |", fh.read())


class InstallTouchesOnlyItsOwnFilesTests(unittest.TestCase):
    """S5-1: the validator step marked every untracked file intent-to-add, so the
    owner's next `git commit -a` committed whatever sat there — a .env.local included."""

    def _repo(self, tmp, *, filemode=True):
        target = os.path.join(tmp, "project")
        os.makedirs(target)
        env = _git_env(tmp)
        _git(target, env, "init", "-q")
        if not filemode:
            _git(target, env, "config", "core.filemode", "false")
        return target, env

    def test_an_unrelated_untracked_file_stays_untracked(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-s51-") as tmp:
            target, env = self._repo(tmp)
            with open(os.path.join(target, ".env.local"), "w", encoding="utf-8") as fh:
                fh.write("SECRET=1\n")
            _install(target, env)
            self.assertNotIn(".env.local", _git(target, env, "ls-files"))
            self.assertIn("?? .env.local", _git(target, env, "status", "--porcelain"))

    def test_a_commit_all_after_install_leaves_the_secret_out(self):
        """The failure the finding describes, end to end."""
        with tempfile.TemporaryDirectory(prefix="ccgg-s51-") as tmp:
            target, env = self._repo(tmp)
            with open(os.path.join(target, ".env.local"), "w", encoding="utf-8") as fh:
                fh.write("SECRET=1\n")
            _install(target, env)
            _git(target, env, "commit", "-qam", "install")
            committed = _git(target, env, "show", "--name-only", "--format=", "HEAD")
            self.assertNotIn(".env.local", committed)
            self.assertIn("AGENTS.md", committed, "what install copied is what the commit carries")

    def test_hooks_are_executable_in_the_index_with_filemode_off(self):
        """S4-8: core.filemode=false is every Windows clone; chmod never reached git."""
        with tempfile.TemporaryDirectory(prefix="ccgg-s48-") as tmp:
            target, env = self._repo(tmp, filemode=False)
            _install(target, env)
            modes = _hook_modes(target, env)
            self.assertTrue(modes, "the hooks are in the index")
            self.assertEqual(set(modes.values()), {"100755"}, modes)

    def test_a_catch_all_eol_rule_is_accepted_for_the_hooks(self):
        """W-5: `* text=auto eol=lf` pins the hooks as well as a `*.sh` rule does."""
        with tempfile.TemporaryDirectory(prefix="ccgg-w5-") as tmp:
            target, env = self._repo(tmp)
            with open(os.path.join(target, ".gitattributes"), "w", encoding="utf-8") as fh:
                fh.write("* text=auto eol=lf\n")
            out = _install(target, env)
            self.assertNotIn("without a *.sh rule", out)

    def test_a_gitattributes_without_any_eol_rule_is_still_reported(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-w5-") as tmp:
            target, env = self._repo(tmp)
            with open(os.path.join(target, ".gitattributes"), "w", encoding="utf-8") as fh:
                fh.write("*.png binary\n")
            self.assertIn("without a *.sh rule", _install(target, env))


class UpdateWritesLfTests(unittest.TestCase):
    """W-2: a guide clone with CRLF in its working tree must not put CRLF into projects.

    Found twice on 2026-09-30: a guide clone checked out under core.autocrlf=true
    delivered 842 CRLF lines of audit_facts.py into every project it synced.
    """

    REL = ".claude/references/dialogue.md"

    def _setup(self, tmp):
        guide = os.path.join(tmp, "guide")
        shutil.copytree(guide_copy(), guide)
        target = os.path.join(tmp, "project")
        os.makedirs(os.path.join(target, ".claude", "references"))
        env = dict(os.environ, HOME=os.path.join(tmp, "home"), GIT_CONFIG_NOSYSTEM="1")
        os.makedirs(env["HOME"])
        subprocess.run(["git", "init", "-q"], cwd=target, env=env, check=True)
        return guide, target, env

    def _update(self, guide, target, env):
        proc = subprocess.run([BASH, os.path.join(guide, "update.sh"), target], env=env,
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc.stdout + proc.stderr

    def test_a_crlf_guide_file_arrives_lf(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-lf-") as tmp:
            guide, target, env = self._setup(tmp)
            with open(os.path.join(guide, self.REL), "wb") as fh:
                fh.write(b"# one\r\ntwo\r\n")
            self._update(guide, target, env)
            with open(os.path.join(target, self.REL), "rb") as fh:
                self.assertEqual(fh.read(), b"# one\ntwo\n")

    def test_a_crlf_probe_contract_arrives_lf(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-lf-") as tmp:
            guide, target, env = self._setup(tmp)
            with open(os.path.join(guide, "tools", "probes.txt"), "wb") as fh:
                fh.write(b"# probes\r\n")
            self._update(guide, target, env)
            with open(os.path.join(target, "tools", "probes.txt"), "rb") as fh:
                self.assertEqual(fh.read(), b"# probes\n")

    def test_a_crlf_checkout_of_the_same_content_is_left_alone(self):
        """A project cloned with autocrlf=true holds the same file; rewriting it every
        session start would report a change that is not one."""
        with tempfile.TemporaryDirectory(prefix="ccgg-lf-") as tmp:
            guide, target, env = self._setup(tmp)
            with open(os.path.join(guide, self.REL), "wb") as fh:
                fh.write(b"# one\ntwo\n")
            with open(os.path.join(target, self.REL), "wb") as fh:
                fh.write(b"# one\r\ntwo\r\n")
            out = self._update(guide, target, env)
            self.assertNotIn(self.REL, out)
            with open(os.path.join(target, self.REL), "rb") as fh:
                self.assertEqual(fh.read(), b"# one\r\ntwo\r\n")

    def test_a_real_change_still_lands(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-lf-") as tmp:
            guide, target, env = self._setup(tmp)
            with open(os.path.join(guide, self.REL), "wb") as fh:
                fh.write(b"# one\ntwo changed\n")
            with open(os.path.join(target, self.REL), "wb") as fh:
                fh.write(b"# one\r\ntwo\r\n")
            out = self._update(guide, target, env)
            self.assertIn(self.REL, out)
            with open(os.path.join(target, self.REL), "rb") as fh:
                self.assertEqual(fh.read(), b"# one\ntwo changed\n")


class UpdateRegistersNewHooksTests(unittest.TestCase):
    """W-1: update.sh delivered a new hook file and never registered it, so it never
    ran. It now appends the guide's registration for a hook it delivers for the first
    time — and only then, so a registration the owner took out stays out."""

    GUARD = ".claude/hooks/context-guard.sh"

    def _wired_before_the_guard(self, tmp, *, filemode=True):
        """An installed project from before context-guard.sh existed."""
        target = os.path.join(tmp, "project")
        os.makedirs(target)
        env = _git_env(tmp)
        _git(target, env, "init", "-q")
        if not filemode:
            _git(target, env, "config", "core.filemode", "false")
        _install(target, env)
        os.remove(os.path.join(target, self.GUARD))
        settings = self._settings(target)
        for event in list(settings["hooks"]):
            settings["hooks"][event] = [b for b in settings["hooks"][event]
                                        if not any("context-guard" in h.get("command", "")
                                                   for h in b.get("hooks", []))]
            if not settings["hooks"][event]:
                del settings["hooks"][event]
        settings["env"] = {"PROJECT_OWN": "kept"}
        self._write_settings(target, settings)
        _git(target, env, "add", "-A")
        _git(target, env, "commit", "-qm", "wired")
        return target, env

    def _settings(self, target):
        with open(os.path.join(target, ".claude", "settings.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def _write_settings(self, target, data):
        with open(os.path.join(target, ".claude", "settings.json"), "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def _update(self, target, env):
        proc = subprocess.run([BASH, update_sh(), target], env=env,
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc.stdout + proc.stderr

    def _guard_events(self, target):
        return sorted(event for event, blocks in self._settings(target).get("hooks", {}).items()
                      for b in blocks for h in b.get("hooks", [])
                      if "context-guard" in h.get("command", ""))

    def test_a_new_hook_is_delivered_and_registered_on_both_events(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-w1-") as tmp:
            target, env = self._wired_before_the_guard(tmp)
            out = self._update(target, env)
            self.assertTrue(os.path.exists(os.path.join(target, self.GUARD)))
            self.assertEqual(self._guard_events(target), ["UserPromptExpansion", "UserPromptSubmit"])
            self.assertIn("registered 2 new hook entries", out)

    def test_the_projects_own_settings_survive_the_merge(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-w1-") as tmp:
            target, env = self._wired_before_the_guard(tmp)
            before = self._settings(target)
            self._update(target, env)
            after = self._settings(target)
            self.assertEqual(after["env"], {"PROJECT_OWN": "kept"})
            for event, blocks in before["hooks"].items():
                self.assertEqual(after["hooks"][event][: len(blocks)], blocks, event)

    def test_a_second_update_adds_nothing(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-w1-") as tmp:
            target, env = self._wired_before_the_guard(tmp)
            self._update(target, env)
            once = self._settings(target)
            out = self._update(target, env)
            self.assertEqual(self._settings(target), once)
            self.assertNotIn("registered", out)

    def test_a_registration_the_owner_removed_stays_removed(self):
        """The hook file is already there, so this run is not its first delivery."""
        with tempfile.TemporaryDirectory(prefix="ccgg-w1-") as tmp:
            target, env = self._wired_before_the_guard(tmp)
            with open(os.path.join(ROOT, self.GUARD), "rb") as src, \
                    open(os.path.join(target, self.GUARD), "wb") as dst:
                dst.write(src.read())
            self._update(target, env)
            self.assertEqual(self._guard_events(target), [])

    def test_an_unreadable_settings_file_is_left_alone_and_reported(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-w1-") as tmp:
            target, env = self._wired_before_the_guard(tmp)
            path = os.path.join(target, ".claude", "settings.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{ not json")
            out = self._update(target, env)
            with open(path, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "{ not json")
            self.assertIn("could not be read", out)

    def test_the_new_hook_is_executable_in_the_index_with_filemode_off(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-w1-") as tmp:
            target, env = self._wired_before_the_guard(tmp, filemode=False)
            self._update(target, env)
            self.assertEqual(_hook_modes(target, env).get(self.GUARD), "100755")

    def test_update_does_not_mark_unrelated_files(self):
        with tempfile.TemporaryDirectory(prefix="ccgg-w1-") as tmp:
            target, env = self._wired_before_the_guard(tmp)
            with open(os.path.join(target, ".env.local"), "w", encoding="utf-8") as fh:
                fh.write("SECRET=1\n")
            self._update(target, env)
            self.assertNotIn(".env.local", _git(target, env, "ls-files"))


if __name__ == "__main__":
    unittest.main()
