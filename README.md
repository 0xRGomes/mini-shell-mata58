# Mini Shell — Projeto Integrador de Sistemas Operacionais

Implementação acadêmica de um interpretador de comandos simplificado (**Mini Shell**) em Python, destinada ao estudo de processos e chamadas de sistema em ambiente Linux.

> **Estado do projeto:** implementação inicial recuperada do documento `Explicacao_Projeto_Mini_Shell_Organizado.pdf`, com correções pontuais na branch `develop`. A lógica e a separação de funções foram preservadas; a indentação original foi normalizada na transcrição do PDF. Os testes automatizados foram executados em Linux/WSL2; a revisão e a validação manual pelo grupo ainda estão pendentes.

## Ambiente e execução

- **Sistema:** Linux (Ubuntu no WSL2, ou outra distribuição Linux compatível).
- **Linguagem:** Python 3.
- **Bibliotecas utilizadas:** `os`, `shlex` e `signal`, todas incluídas na biblioteca padrão do Python. Não é necessário instalar pacotes Python adicionais para o código atual.

Verifique se o Python está disponível, em um terminal **Ubuntu/WSL2**:

```bash
python3 --version
```

Na pasta do repositório, execute:

```bash
python3 mini_shell.py
```

Por ser um programa Python, **não há etapa de compilação** para executar a versão atual. O programa mostra `mini-shell> ` e aguarda comandos. Digite `exit` e pressione Enter para encerrá-lo.

> Os comandos de execução acima devem ser usados dentro do Linux/WSL2: `os.fork()` não é suportado no Python executado nativamente no Windows.

## Como funciona

1. `read_command(buffer)` exibe o prompt e acumula bytes com `os.read()`. Retira uma linha por vez, preservando o restante para a próxima leitura; no EOF, entrega também a última linha sem `\n`. A decodificação ocorre depois de reunir a linha, inclusive quando um caractere UTF-8 atravessa blocos de leitura.
2. `parse_command()` interpreta os argumentos com `shlex.split()`.
3. `execute_command()` trata os comandos internos `exit` e `cd` ou cria um processo filho para comandos externos.
4. No processo filho, `os.execvp()` executa o programa solicitado.
5. No processo pai, `os.wait()` aguarda e recolhe o filho antes do próximo prompt. Durante criação/espera, o pai ignora SIGINT; o filho restaura SIGINT padrão antes de `execvp`. Assim, Ctrl+C do terminal interrompe o comando externo e o pai continua esperando seu recolhimento. Depois, restaura o tratamento anterior de SIGINT.
6. `main()` controla o laço principal.

## Chamadas de sistema utilizadas

| Operação | Uso no código | Finalidade |
| --- | --- | --- |
| Leitura (`read`) | `os.read(0, 4096)` | Lê bytes da entrada padrão. |
| Escrita (`write`) | `os.write(fd, data)` com `fd=1` ou `fd=2` | Escreve mensagens na saída padrão e de erro. |
| Criação de processo (`fork`) | `os.fork()` | Cria o processo filho. |
| Execução de programa (`execvp`) | `os.execvp(args[0], args)` | Substitui o programa executado pelo filho. |
| Espera (`wait`) | `os.wait()` | Aguarda a finalização do processo filho. |

`write_text()` repete `os.write()` quando há escrita parcial. Falhas de leitura/escrita encerram o shell com status 1 e uma mensagem em stderr, se essa saída estiver disponível; insistir no laço com um descritor inválido não permitiria interação. Falhas em `fork`, `execvp`, interpretação e `cd` permitem continuar. `cd` rejeita mais de um argumento para evitar mudar silenciosamente para uma pasta ignorando os demais.

O código também utiliza `os.chdir()` para o comando interno `cd` e `os._exit()` para encerrar o processo filho caso a execução do comando falhe.

## Exemplos de comandos e saídas

As saídas de `echo`, `ls` e `cat` foram confirmadas pelos testes automatizados no WSL2. As transcrições mostram os comandos junto ao prompt como em um terminal; na entrada redirecionada, o shell não ecoa o texto digitado. O conteúdo de `cat` depende da versão do arquivo, e as mensagens do sistema podem variar com idioma e ambiente.

**1. `echo` com argumento**

```text
mini-shell> echo Ola mundo
Ola mundo
mini-shell>
```

**2. `ls` com argumento**

```text
mini-shell> ls -d .
.
mini-shell>
```

**3. `cat` com argumento** (o conteúdo mostrado é apenas o início da saída; o arquivo completo será exibido)

```text
mini-shell> cat -n mini_shell.py
     1	import os
     2	import shlex
     3	import signal
...
mini-shell>
```

**4. Comando inexistente** (mensagem confirmada no ambiente de teste; o idioma pode variar)

```text
mini-shell> comando_inexistente
Comando não encontrado ou falha: [Errno 2] No such file or directory
mini-shell>
```

## Limitações conhecidas

- Não há tratamento dedicado de **histórico/edição da linha de comando** com setas e tecla Delete; esse comportamento precisa ser verificado no terminal de apresentação.
- O buffer aceita comandos maiores que 4096 bytes na entrada redirecionada. No terminal em modo canônico, o próprio driver pode limitar a linha (tipicamente 4096 bytes no Linux); o teste de linha longa usa entrada redirecionada. Não há continuação de aspas entre linhas. Bytes inválidos em UTF-8 são substituídos na decodificação.
- Não há implementação própria para pipes (`|`), redirecionamentos (`>` e `<`), expansão de variáveis ou execução em segundo plano (`&`). Esses recursos **não aparecem como requisitos mínimos** do enunciado.
- O shell aguarda comandos externos de forma sequencial e não apresenta explicitamente o código de retorno do processo filho.
- Ctrl+C foi validado com PTY no prompt e durante `sleep`, incluindo ausência de filhos pendentes após a espera. Não há controle de jobs nem grupos de processos separados: depende-se do SIGINT enviado pelo terminal ao grupo em primeiro plano. Não há garantia de interromper um programa que ignore SIGINT; enviar SIGINT somente ao PID do pai não equivale a Ctrl+C no terminal.

## Testes e validação

Execute a partir da raiz do repositório, sem instalar dependências:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Resultado em 14/11/2026: **18 testes aprovados, sem testes ignorados**, com Python 3.14.4 e kernel `6.18.54.1-microsoft-standard-WSL2`. Compatibilidade com outras versões de Python/Ubuntu deve ser confirmada no ambiente de entrega.

- **Entrada redirecionada (`subprocess`):** `echo Ola mundo`, `ls -d .`, saída completa de `cat -n mini_shell.py` comparada com `cat` direto, `cd` seguido de `pwd`, comando inexistente, linha vazia, aspas não fechadas, diretório inexistente, argumentos extras em `cd`, `exit`, EOF vazio, várias linhas juntas, última linha sem quebra, linha maior que 4096 bytes com UTF-8 atravessando blocos e execução sequencial. O teste sequencial cria um arquivo após uma pausa no filho e o lê no comando seguinte. Também foram fechados descritores para provocar erros reais de leitura/escrita e executado arquivo sem permissão para provocar falha em `execvp`.
- **Testes isolados (`unittest.mock`):** falha de `fork` simulada (sem esgotar processos do sistema), rejeição de argumentos extras em `cd` e escrita parcial simulada. Não foi provocada exaustão real de recursos.
- **Terminal PTY (`pty.fork`):** Ctrl+C durante a leitura, continuidade com `echo` e Ctrl+C durante `sleep 30`. O teste consulta `/proc` para confirmar que o filho desapareceu e que o pai não tem filhos pendentes antes do próximo comando. PTY é um terminal controlado pelo teste; não substitui a avaliação visual/manual no terminal da apresentação. A inspeção de filhos requer `/proc` Linux.

Comparação com o código original: várias linhas eram executadas como um só comando; linhas longas eram partidas entre leituras; `cd / /tmp` ignorava o segundo argumento; erros de descritor produziam traceback. Em PTY, Ctrl+C durante `sleep` deixou um filho em estado `Z (zombie)`, confirmado por `/proc`, pois o pai abandonava `os.wait()`. Ctrl+C no prompt já mantinha o shell ativo. Comando inexistente, aspas malformadas, EOF vazio e os três comandos externos isolados já tinham tratamento básico; as correções preservam esse comportamento. A ausência de inspeção do status retornado por `os.wait()` foi mantida: exibir códigos de saída não é requisito e o filho é recolhido mesmo sem apresentá-los.

Para a conferência manual no Ubuntu/WSL2 da apresentação, execute `python3 mini_shell.py`, repita os exemplos, use `cd /tmp` e `pwd`, pressione Ctrl+C no prompt e durante `sleep 30`, confirme que `echo` ainda funciona e encerre com `exit`. Em outra sessão, confirme EOF com Ctrl+D no prompt vazio. Confira também as limitações de edição com setas/Delete nesse terminal.

## Entrega e apresentação

Conforme o enunciado da disciplina, a entrega inclui o código-fonte, este README (com execução, chamadas de sistema, comandos testados e limitações) e **um vídeo de demonstração de até 5 minutos, ainda pendente de produção**.

Na apresentação, o grupo deve explicar o contexto, as chamadas de sistema, a estrutura do código, realizar uma demonstração, relatar dificuldades e aprendizados e concluir com espaço para perguntas.

## Origem e autoria

A implementação inicial foi desenvolvida por uma integrante do grupo e registrada no documento `Explicacao_Projeto_Mini_Shell_Organizado.pdf`. O arquivo `mini_shell.py` foi transcrito desse documento para disponibilizar o código executável, preservando sua lógica original. A identificação da autoria e dos demais integrantes deverá ser preenchida e confirmada pelo grupo.

### Pendências antes da entrega

- [ ] Confirmar autoria e integrantes no repositório.
- [x] Executar e registrar os testes automatizados no Linux/WSL2.
- [ ] Repetir a validação manual no terminal da apresentação e revisar `develop` antes de integrar à `main`.
- [x] Atualizar as saídas confirmadas dos comandos no README.
- [ ] Revisar as limitações observadas na prática.
- [ ] Gravar o vídeo demonstrativo (até 5 minutos).
