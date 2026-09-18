# Nova Mascot Runtime

Runtime React isolado para o personagem interativo da Nova. O projeto começa com um placeholder e está preparado para receber um arquivo Rive sem alterar a API dos módulos.

## Arquitetura

- `MascotProvider`: estado global, fala e persistência.
- `MascotController`: limites, destinos e coordenadas responsivas.
- `MascotLayer`: camada fixa sobre a interface.
- `MascotCharacter`: placeholder ou adaptador Rive.
- `MascotRive`: integração com `@rive-app/react-canvas`.
- `MascotSpeech`: balão de fala.
- `useMascot()`: API para módulos da aplicação.
- `MascotCommandRouter`: valida comandos externos antes da execução.
- `src/index.ts`: entrada pública para integração pelos módulos.
- `mascot.config.ts`: configuração central do arquivo Rive e da State Machine.

## Comandos

```ts
const mascot = useMascot();

await mascot.runSequence([
  { action: "moveToTarget", target: "english-input" },
  { action: "say", text: "Write a sentence here." },
  { action: "pointTo", target: "english-input" },
]);
```

Um destino é identificado por:

```html
<input data-mascot-target="english-input" />
```

Comandos vindos da IA devem passar por `parseMascotCommand` ou `parseMascotJson`. O router rejeita ações desconhecidas antes que elas cheguem ao frontend.

## Rive

Quando o arquivo `.riv` estiver pronto, o componente pode ser usado com `MascotRive`, mantendo a movimentação física fora do arquivo de animação. A State Machine esperada inicialmente é `Nova`.

Para ativar o asset sem alterar o código, copie `.env.example` para `.env.local` e preencha `VITE_NOVA_RIVE_SRC`.

## Desenvolvimento

```bash
npm install
npm run dev
npm run lint
npm run build
```
