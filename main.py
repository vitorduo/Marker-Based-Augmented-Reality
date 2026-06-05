import subprocess
import sys
import os

def executar_script(nome_ficheiro):
    """Executa um script Python bloqueando o menu até que o script feche."""
    if not os.path.exists(nome_ficheiro):
        print(f"\n[Erro] O ficheiro '{nome_ficheiro}' não foi encontrado na pasta atual.")
        return

    print(f"\n[{nome_ficheiro}] A iniciar (pressiona 'q' ou fecha a janela da câmara para voltar ao menu)...")
    try:
        # sys.executable garante que usamos o mesmo interpretador Python
        subprocess.run([sys.executable, nome_ficheiro])
    except KeyboardInterrupt:
        print(f"\n[{nome_ficheiro}] Execução interrompida pelo utilizador.")
    except Exception as e:
        print(f"\n[Erro] Falha ao executar {nome_ficheiro}: {e}")

def abrir_unity_build():
    """Abre o executável final do Unity (Build)."""
    # Caminho relativo: procura a pasta 'Build' ao lado deste main.py
    nome_executavel = "VARM_Projeto2_Unity.exe"
    caminho_build = os.path.join("Build", nome_executavel)

    if not os.path.exists(caminho_build):
        print(f"\n[Erro] Executável não encontrado em: {caminho_build}")
        print("Verifica se o ficheiro se chama exatamente 'VARM_Projeto2_Unity.exe' e se está dentro da pasta 'Build'.")
        return

    print(f"\n[Unity] A iniciar a aplicação de Realidade Aumentada...")
    # Popen não bloqueia o terminal, permitindo voltar ao menu imediatamente
    subprocess.Popen([caminho_build])

def menu():
    while True:
        print("\n" + "="*65)
        print(" MENU PRINCIPAL - PROJETO 2 VARM ".center(65, "="))
        print("\n[Aviso] Lembra-te de abrir primeiro o Unity (Opção 4) ANTES de arrancar o servidor UDP Python (Opção 3)!")
        print("="*65)
        print("1. Executar Calibração da Câmara (calibracao.py)")
        print("2. Deteção ArUco - Local - Aruco lib OpenCV (detecao_aruco.py)")
        print("3. Servidor UDP para Unity (detecao_aruco_unity.py)")
        print("-" * 65)
        print("4. Abrir Executável Unity (Realidade Aumentada)")
        print("0. Sair")
        print("="*65)

        escolha = input("Seleciona uma opção (0-4): ")

        if escolha == '1':
            executar_script('calibracao.py')
        elif escolha == '2':
            executar_script('detecao_aruco.py')
        elif escolha == '4':
            abrir_unity_build()
        elif escolha == '3':
            # Aviso importante para a arquitetura cliente-servidor
            print("\n[Aviso] Lembra-te de abrir primeiro o Unity (Opção 4) ANTES de arrancar o servidor Python!")
            executar_script('detecao_aruco_unity.py')
        elif escolha == '0':
            print("\nA sair... Até à próxima!")
            sys.exit()
        else:
            print("\n[Aviso] Opção inválida. Tenta novamente.")

if __name__ == "__main__":
    menu()