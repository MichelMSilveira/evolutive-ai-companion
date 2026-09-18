# Inicialização automática

O arquivo `start_nova.bat` inicia o servidor local do Ollama, o pet desktop e os motores locais de voz e visão. Se o Ollama já estiver rodando, ele não é iniciado novamente. Voz e visão rodam em segundo plano, sem abrir abas de terminal; o pet permanece visível na área de trabalho.

Para iniciar automaticamente com o Windows, o atalho deve ficar na pasta `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`.

Para encerrar o pet, pressione `Esc`. Os motores ocultos podem ser finalizados pelo Gerenciador de Tarefas encerrando os processos `pythonw.exe` correspondentes.
