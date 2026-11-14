import os
import shlex
import signal


def write_text(text, fd=1):
    """Escreve texto diretamente usando a chamada de sistema write."""
    data = text.encode()
    while data:
        written = os.write(fd, data)
        if written == 0:
            raise OSError("Escrita sem progresso")
        data = data[written:]


def read_command(buffer):
    """Lê um comando digitado no terminal usando read."""
    write_text("mini-shell> ")
    while b"\n" not in buffer:
        data = os.read(0, 4096)
        if not data:
            if not buffer:
                return None
            break
        buffer.extend(data)
    end = buffer.find(b"\n")
    if end == -1:
        end = len(buffer)
    line = bytes(buffer[:end])
    del buffer[:end + 1]
    return line.decode(errors="replace").strip()


def parse_command(line):
    """Divide o comando e seus argumentos."""
    try:
        return shlex.split(line)
    except ValueError as error:
        write_text(f"Erro ao interpretar comando: {error}\n")
        return []


def execute_command(args):
    """Cria um processo e executa o programa solicitado."""
    if not args:
        return

    if args[0] == "exit":
        raise SystemExit

    if args[0] == "cd":
        if len(args) > 2:
            write_text("Erro ao mudar de pasta: cd aceita apenas um argumento\n")
            return
        try:
            os.chdir(args[1] if len(args) > 1 else os.path.expanduser("~"))
        except OSError as error:
            write_text(f"Erro ao mudar de pasta: {error}\n")
        return

    # O terminal envia SIGINT ao grupo inteiro. O pai aguarda e recolhe
    # o filho; o filho restaura o comportamento padrão antes de executar.
    previous_sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        try:
            pid = os.fork()
        except OSError as error:
            write_text(f"Erro ao criar processo: {error}\n")
            return

        if pid == 0:
            # Processo filho: substitui sua execução pelo comando.
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            try:
                os.execvp(args[0], args)
            except OSError as error:
                try:
                    write_text(f"Comando não encontrado ou falha: {error}\n", 2)
                finally:
                    os._exit(127)
        else:
            # Processo pai: espera o filho terminar, inclusive após Ctrl+C.
            os.wait()
    finally:
        signal.signal(signal.SIGINT, previous_sigint)


def main():
    """Loop principal do Mini Shell."""
    write_text("Mini Shell iniciado! Digite 'exit' para sair.\n")
    buffer = bytearray()

    while True:
        try:
            line = read_command(buffer)
            if line is None:
                break

            args = parse_command(line)
            execute_command(args)
        except KeyboardInterrupt:
            buffer.clear()
            write_text("\nUse 'exit' para encerrar.\n")
        except SystemExit:
            break


if __name__ == "__main__":
    try:
        main()
    except OSError as error:
        # Sem entrada/saída utilizável, não há como continuar o laço.
        try:
            write_text(f"Erro de entrada/saída: {error}\n", 2)
        except OSError:
            pass
        raise SystemExit(1)
