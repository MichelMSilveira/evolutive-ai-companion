# Evolutive AI Companion

Um pet-assistente local que conversa por voz, ajuda o usuário e evolui conforme sua interação.

## Visão

O usuário começa com um personagem-base. Conversas, estudos, cuidados e escolhas alteram atributos como inteligência, criatividade, energia e sociabilidade. No futuro, itens e aparências poderão ser exportados, trocados ou vendidos, enquanto memórias pessoais permanecem sob controle do dono.

## Protótipo atual

- `voice-engine/`: assistente local com Ollama, Vosk e voz do Windows.
- `english-flow/`: protótipo visual com mascote e fluxo de prática profissional em inglês.

## Primeiro personagem

O protótipo começa com Nova, um gato virtual de forma simples e neutra. Ele começa com atributos equilibrados e evolui a partir das interações do usuário. O estado inicial está documentado em `character-base.json`.

## Próxima evolução

Unificar voz, personagem, atributos, salvamento local e evolução visual em uma pequena experiência desktop.

## Privacidade

O projeto segue uma abordagem local-first: dados pessoais e memórias devem permanecer no dispositivo do usuário, com exportação e compartilhamento controlados explicitamente.
