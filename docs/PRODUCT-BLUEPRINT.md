# Nova — blueprint do produto

Este documento transforma a ideia em uma vertical slice comercial: uma única experiência que demonstra valor real, privacidade local e evolução visível.

## Os sete pilares

1. **Companheira visual** — Nova permanece disponível no desktop, com movimento felino, humor, necessidades e feedback visual.
2. **Conversação por voz** — tecla para falar, transcrição, resposta escrita e áudio; português e inglês com troca de idioma sem perder personalidade.
3. **Memória do usuário** — memórias separadas em perfil, fatos importantes, histórico recente e conhecimento importado. Tudo editável, exportável e apagável.
4. **Ensino adaptativo** — Nova identifica idioma, nível, erros recorrentes e objetivo; responde com uma correção curta e uma próxima pergunta adequada.
5. **Assistência prática** — ferramentas para programação, automação e produtos digitais, com confirmação antes de executar ações externas ou irreversíveis.
6. **Evolução verificável** — XP, atributos, humor e aparência mudam a partir de eventos registrados, sem inventar progresso. O usuário pode consultar o motivo de cada mudança.
7. **Produto comercial** — arquitetura modular, instalação simples, modo local-first, importação/exportação de personagem e memória, testes e documentação de demonstração para GitHub/Upwork.

## Arquitetura-alvo

```text
Voz/Texto -> Orquestrador -> Memória + Conhecimento -> Provedor de IA
                 |                    |
                 v                    v
             Nova Core           Ferramentas com permissão
                 |
                 v
          Mascote / XP / Eventos / Relatórios
```

### Decisões de produto

- O estado do personagem e as memórias pertencem ao usuário.
- O modelo de IA é um provedor substituível: Ollama local primeiro; remoto apenas por escolha explícita.
- A personalidade fica em uma configuração própria; trocar o idioma não troca a identidade.
- Conhecimento não é “treinamento automático” do modelo: é memória controlada e recuperada quando necessário.
- Ações sensíveis nunca são executadas apenas porque o modelo sugeriu.
- No modo modelista, a Nova apresenta opções e o caminho recomendado antes de qualquer ação. Perguntar “como fazer” nunca autoriza escrever código, alterar arquivos ou operar o Blender.
- No modo modelista, criação, seleção, alteração e sucesso só podem ser confirmados com evidência visual atual. Sem essa evidência, a Nova deve declarar que ainda não pode confirmar.
- Quando o usuário informar que algo não funcionou ou pedir novamente como fazer, a Nova deve abandonar o raciocínio anterior, diagnosticar o estado atual e propor somente o próximo passo verificável.
- O pedido atual do usuário tem prioridade sobre o plano anterior; histórico antigo não pode obrigar a Nova a continuar uma ação que falhou.

## Ordem de entrega

### Fase 1 — fundação demonstrável

- Consolidar `core/nova_core.py` como fonte única do estado.
- Criar armazenamento local versionado e migrações simples.
- Criar interface de provedor para Ollama e um provedor remoto opcional.
- Registrar eventos, respostas, XP e erros com testes.

### Fase 2 — memória e ensino

- Memória editável com categorias e consentimento.
- Importação de notas/documentos.
- Recuperação por busca local; embeddings só depois de validar o fluxo.
- Perfil de idioma, nível, objetivos e erros recorrentes.

### Fase 3 — experiência

- Voz contínua com push-to-talk confiável.
- Resposta em áudio e texto, com idioma de fala independente do idioma da interface.
- Animações conectadas a estado, atividade, humor e evolução.

### Fase 4 — comercialização

- Ferramentas de programação/automação com permissões.
- Exportação e importação assinada do personagem sem expor memória privada.
- Demonstração reproduzível, instalador e documentação de arquitetura.
- Preparação para itens, intercâmbio e marketplace, sem misturar identidade com dados pessoais.

## Critério de pronto do MVP

Um avaliador deve conseguir instalar, iniciar Nova, conversar em português ou inglês, ver a tradução, registrar uma meta, observar uma mudança explicável no estado e exportar os próprios dados — tudo sem depender da nuvem.

## Riscos que vamos controlar

- **Áudio:** falhas de TTS/STT não podem fechar o processo; devem retornar ao modo de escuta.
- **Alucinação:** respostas devem distinguir memória, conhecimento recuperado e sugestão.
- **Privacidade:** dados pessoais ficam locais por padrão.
- **Complexidade:** cada recurso novo precisa aparecer em uma demonstração comercial ou ser adiado.
- **Custo:** modelos maiores, embeddings e serviços remotos só entram após aviso e medição.
