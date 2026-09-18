# Preparação do arquivo Rive da Nova

Crie o arquivo `nova.riv` e coloque-o em:

`public/assets/nova.riv`

## Convenções necessárias

- Artboard: `Nova`
- State Machine: `Nova`
- Estado inicial: `idle`
- Estados: `idle`, `walking`, `talking`, `pointing`, `thinking`, `happy`, `surprised`, `sleeping`

## Inputs recomendados

- `movement`: enum ou trigger para caminhada
- `talking`: boolean
- `mood`: enum
- `pointing`: boolean
- `attention`: trigger

## Regras

- O arquivo deve conter somente o personagem e suas animações internas.
- A posição na tela continuará sendo controlada pelo React.
- Não crie uma animação diferente para cada coordenada.
- Use nomes estáveis para evitar alterações no código de integração.

Depois de adicionar o arquivo, configure:

```env
VITE_NOVA_RIVE_SRC=/assets/nova.riv
```

O runtime já possui o adaptador `MascotRive` e carregará esse asset sem alterar a API dos módulos.
