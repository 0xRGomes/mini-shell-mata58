import os
import shlex


def write_text(text):
    """Escreve texto diretamente usando a chamada de sistema write."""
    os.write(1, text.encode())


def read_command():
    """Lê um comando digitado no terminal usando read."""
    write_text("mini-shell> ")
    data = os.read(0, 4096)
    if not data:
        return None
    return data.decode().strip()


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
        try:
            os.chdir(args[1] if len(args) > 1 else os.path.expanduser("~"))
        except OSError as error:
            write_text(f"Erro ao mudar de pasta: {error}\n")
        return

    try:
        pid = os.fork()
    except OSError as error:
        write_text(f"Erro ao criar processo: {error}\n")
        return

    if pid == 0:
        # Processo filho: substitui sua execução pelo comando.
        try:
            os.execvp(args[0], args)
        except OSError as error:
            os.write(2, f"Comando não encontrado ou falha: {error}\n".encode())
            os._exit(127)
    else:
        # Processo pai: espera o filho terminar.
        os.wait()


def main():
    """Loop principal do Mini Shell."""
    write_text("Mini Shell iniciado! Digite 'exit' para sair.\n")

    while True:
        try:
            line = read_command()
            if line is None:
                break

            args = parse_command(line)
            execute_command(args)
        except KeyboardInterrupt:
            write_text("\nUse 'exit' para encerrar.\n")
        except SystemExit:
            break


if __name__ == "__main__":
    main()
