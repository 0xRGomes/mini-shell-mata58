# Mini Shell — Projeto Integrador de Sistemas Operacionais

Implementação acadêmica de um interpretador de comandos simplificado (**Mini Shell**) em Python, destinada ao estudo de processos e chamadas de sistema em ambiente Linux.

> **Estado do projeto:** versão inicial recuperada do documento `Explicacao_Projeto_Mini_Shell_Organizado.pdf`. A lógica foi preservada; a indentação foi normalizada porque a formatação do PDF não mantém a indentação Python de modo consistente. O comportamento ainda precisa ser validado pelo grupo no WSL2 antes da entrega.

## Ambiente e execução

- **Sistema:** Linux (Ubuntu no WSL2, ou outra distribuição Linux compatível).
- **Linguagem:** Python 3.
- **Bibliotecas utilizadas:** `os` e `shlex`, ambas incluídas na biblioteca padrão do Python. Não é necessário instalar pacotes Python adicionais para o código atual.

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

1. `read_command()` exibe o prompt e lê a entrada com `os.read()`.
2. `parse_command()` interpreta os argumentos com `shlex.split()`.
3. `execute_command()` trata os comandos internos `exit` e `cd` ou cria um processo filho para comandos externos.
4. No processo filho, `os.execvp()` executa o programa solicitado.
5. No processo pai, `os.wait()` aguarda a conclusão do filho antes do próximo prompt.
6. `main()` controla o laço principal.

## Chamadas de sistema utilizadas

| Operação | Uso no código | Finalidade |
| --- | --- | --- |
| Leitura (`read`) | `os.read(0, 4096)` | Lê bytes da entrada padrão. |
| Escrita (`write`) | `os.write(1, ...)` e `os.write(2, ...)` | Escreve mensagens na saída padrão e de erro. |
| Criação de processo (`fork`) | `os.fork()` | Cria o processo filho. |
| Execução de programa (`execvp`) | `os.execvp(args[0], args)` | Substitui o programa executado pelo filho. |
| Espera (`wait`) | `os.wait()` | Aguarda a finalização do processo filho. |

O código também utiliza `os.chdir()` para o comando interno `cd` e `os._exit()` para encerrar o processo filho caso a execução do comando falhe.

## Exemplos de comandos e saídas

Os exemplos abaixo ilustram a saída esperada. **Executar e confirmar os três comandos no Ubuntu/WSL2 antes da entrega e atualizar esta seção com os resultados reais.**

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
     1  import os
     2  import shlex
...
mini-shell>
```

**4. Comando inexistente** (texto exato do erro varia com o sistema)

```text
mini-shell> comando_inexistente
Comando não encontrado ou falha: ...
mini-shell>
```

## Limitações conhecidas

- Não há tratamento dedicado de **histórico/edição da linha de comando** com setas e tecla Delete; esse comportamento precisa ser verificado no terminal de apresentação.
- Cada chamada de leitura utiliza `os.read(0, 4096)`; comandos grandes ou entradas com várias linhas não têm tratamento especializado.
- Não há implementação própria para pipes (`|`), redirecionamentos (`>` e `<`), expansão de variáveis ou execução em segundo plano (`&`). Esses recursos **não aparecem como requisitos mínimos** do enunciado.
- O shell aguarda comandos externos de forma sequencial e não apresenta explicitamente o código de retorno do processo filho.
- O comportamento de `Ctrl+C` durante a execução de comandos externos ainda precisa ser testado.

## Entrega e apresentação

Conforme o enunciado da disciplina, a entrega inclui o código-fonte, este README (com execução, chamadas de sistema, comandos testados e limitações) e **um vídeo de demonstração de até 5 minutos**.

Na apresentação, o grupo deve explicar o contexto, as chamadas de sistema, a estrutura do código, realizar uma demonstração, relatar dificuldades e aprendizados e concluir com espaço para perguntas.

## Origem e autoria

A implementação inicial foi desenvolvida por uma integrante do grupo e registrada no documento `Explicacao_Projeto_Mini_Shell_Organizado.pdf`. O arquivo `mini_shell.py` foi transcrito desse documento para disponibilizar o código executável, preservando sua lógica original. A identificação da autoria e dos demais integrantes deverá ser preenchida e confirmada pelo grupo.

### Pendências antes da entrega

- [ ] Confirmar autoria e integrantes no repositório.
- [ ] Executar e registrar os testes no Ubuntu/WSL2.
- [ ] Atualizar as saídas reais dos comandos no README.
- [ ] Revisar as limitações observadas na prática.
- [ ] Gravar o vídeo demonstrativo (até 5 minutos).
