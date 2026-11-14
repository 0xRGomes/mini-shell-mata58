import errno
import importlib.util
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SHELL = Path(os.environ.get('MINI_SHELL_TEST_TARGET', ROOT / 'mini_shell.py'))
spec = importlib.util.spec_from_file_location('mini_shell', SHELL)
shell = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shell)


class RedirectedTests(unittest.TestCase):
    def run_shell(self, commands):
        return subprocess.run([sys.executable, str(SHELL)], input=commands,
                              text=True, capture_output=True, cwd=ROOT, timeout=10)

    def test_required_commands(self):
        for command, expected in [('echo Ola mundo', 'Ola mundo\n'),
                                  ('ls -d .', '.\n')]:
            with self.subTest(command=command):
                result = self.run_shell(command + '\n')
                self.assertEqual(result.returncode, 0)
                self.assertIn('mini-shell> ' + expected, result.stdout)
        result = self.run_shell('cat -n mini_shell.py\n')
        expected = subprocess.check_output(['cat', '-n', 'mini_shell.py'], cwd=ROOT, text=True)
        self.assertIn(expected, result.stdout)

    def test_cd_pwd(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_shell(f'cd {directory}\npwd\nexit\n')
            self.assertIn(directory + '\n', result.stdout)

    def test_errors_and_continuation(self):
        for command, message in [('comando_inexistente_ufba', 'Comando não encontrado ou falha'),
                                 ('echo "aberta', 'Erro ao interpretar comando'),
                                 ('cd /pasta_inexistente_ufba', 'Erro ao mudar de pasta'),
                                 ('cd / /tmp', 'cd aceita apenas um argumento')]:
            with self.subTest(command=command):
                result = self.run_shell(command + '\necho CONTINUA\nexit\n')
                self.assertIn(message, result.stdout + result.stderr)
                self.assertIn('mini-shell> CONTINUA\n', result.stdout)

    def test_empty_command(self):
        result = self.run_shell('\n   \necho OK\nexit\n')
        self.assertIn('mini-shell> OK\n', result.stdout)
        self.assertEqual(result.stderr, '')

    def test_exit(self):
        result = self.run_shell('exit\necho NAO_EXECUTAR\n')
        self.assertNotIn('NAO_EXECUTAR', result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_empty_eof(self):
        result = self.run_shell('')
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.endswith('mini-shell> '))

    def test_multiple_lines(self):
        result = self.run_shell('echo PRIMEIRO\necho SEGUNDO\nexit\n')
        self.assertIn('mini-shell> PRIMEIRO\nmini-shell> SEGUNDO\n', result.stdout)

    def test_final_without_newline(self):
        result = self.run_shell('echo PRIMEIRO\necho FINAL')
        self.assertIn('mini-shell> FINAL\n', result.stdout)

    def test_long_command_and_utf8_boundary(self):
        argument = 'a' * 4090 + 'á' * 1000
        result = self.run_shell('echo ' + argument + '\necho FIM\nexit\n')
        self.assertIn('mini-shell> ' + argument + '\nmini-shell> FIM\n', result.stdout)
        self.assertEqual(result.stderr, '')

    def test_sequential_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'marker'
            script = Path(directory) / 'child.py'
            script.write_text('import time, pathlib\ntime.sleep(0.2)\n'
                              f'pathlib.Path({str(marker)!r}).write_text("FILHO_TERMINOU")\n')
            result = self.run_shell(f'{sys.executable} {script}\ncat {marker}\nexit\n')
            self.assertIn('mini-shell> FILHO_TERMINOU', result.stdout)
            self.assertEqual(result.stderr, '')

    def test_read_error(self):
        result = subprocess.run([sys.executable, str(SHELL)], cwd=ROOT,
                                preexec_fn=lambda: os.close(0), capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'Erro de entrada/sa', result.stderr)
        self.assertNotIn(b'Traceback', result.stderr)

    def test_write_error(self):
        result = subprocess.run([sys.executable, str(SHELL)], cwd=ROOT,
                                preexec_fn=lambda: os.close(1), capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'Erro de entrada/sa', result.stderr)


class UnitTests(unittest.TestCase):
    def test_fork_failure(self):
        with patch.object(shell.os, 'fork', side_effect=OSError(errno.EAGAIN, 'indisponível')), \
             patch.object(shell, 'write_text') as output:
            shell.execute_command(['echo', 'teste'])
        self.assertIn('Erro ao criar processo', output.call_args.args[0])

    def test_cd_rejects_extra_arguments(self):
        with patch.object(shell.os, 'chdir') as chdir, \
             patch.object(shell, 'write_text') as output:
            shell.execute_command(['cd', '/', '/tmp'])
        chdir.assert_not_called()
        self.assertIn('cd aceita apenas um argumento', output.call_args.args[0])

    def test_partial_write(self):
        with patch.object(shell.os, 'write', side_effect=[2, 2]) as write:
            shell.write_text('abcd')
        self.assertEqual(write.call_args_list[1].args, (1, b'cd'))

    def test_exec_permission_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            program = Path(directory) / 'sem_permissao'
            program.write_text('echo teste\n')
            result = RedirectedTests().run_shell(f'{program}\necho CONTINUA\n')
            self.assertIn('Comando não encontrado ou falha', result.stderr)
            self.assertIn('mini-shell> CONTINUA\n', result.stdout)


class TerminalTests(unittest.TestCase):
    def setUp(self):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(ROOT)
            os.execv(sys.executable, [sys.executable, str(SHELL)])
        self.pending = b''
        self.until(b'mini-shell> ')

    def tearDown(self):
        try:
            os.kill(self.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        os.waitpid(self.pid, 0)
        os.close(self.fd)

    def until(self, token):
        deadline = time.monotonic() + 5
        while token not in self.pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.fd], [], [], max(0, remaining))[0]:
                self.fail(f'Tempo esgotado esperando {token!r}: {self.pending!r}')
            self.pending += os.read(self.fd, 65536)
        end = self.pending.index(token) + len(token)
        result, self.pending = self.pending[:end], self.pending[end:]
        return result

    def test_ctrl_c_at_prompt(self):
        os.write(self.fd, b'echo DESCARTAR')
        time.sleep(0.1)
        os.write(self.fd, b'\x03')
        self.until(b'mini-shell> ')
        os.write(self.fd, b'echo VIVO\n')
        output = self.until(b'mini-shell> ')
        self.assertIn(b'VIVO\r\n', output)
        self.assertNotIn(b'Traceback', output)

    @unittest.skipUnless(Path('/proc/self/task').exists(), 'Inspeção de filhos exige /proc Linux')
    def test_ctrl_c_child_is_reaped(self):
        os.write(self.fd, b'sleep 30\n')
        children_path = Path(f'/proc/{self.pid}/task/{self.pid}/children')
        deadline = time.monotonic() + 5
        children = ''
        while time.monotonic() < deadline:
            children = children_path.read_text().strip()
            if children:
                # Aguarda exec, para testar o programa externo já iniciado.
                if Path(f'/proc/{children}/comm').read_text().strip() == 'sleep':
                    break
            time.sleep(0.01)
        else:
            self.fail('Filho sleep não iniciou')
        os.write(self.fd, b'\x03')
        output = self.until(b'mini-shell> ')
        self.assertEqual(children_path.read_text().strip(), '')
        self.assertFalse(Path(f'/proc/{children}').exists())
        self.assertNotIn(b'Traceback', output)
        os.write(self.fd, b'echo VIVO\n')
        self.assertIn(b'VIVO\r\n', self.until(b'mini-shell> '))


if __name__ == '__main__':
    unittest.main()
