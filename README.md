# 📌 Projeto 2 VARM: Marker-Based Augmented Reality

Este repositório contém o segundo projeto desenvolvido para a unidade curricular de **Visão Artificial e Realidade Mista (VARM)** do **Mestrado em Engenharia Informática e Multimédia (MEIM)** no **Instituto Superior de Engenharia de Lisboa (ISEL)**.

O objetivo principal é implementar um sistema de Realidade Aumentada baseado em marcadores fiduciários (ArUco), permitindo alinhar e registar elementos virtuais 3D com o mundo real. O projeto dispõe de uma aplicação de visualização local em OpenCV e de um sistema avançado integrado com o motor gráfico Unity3D através de uma arquitetura de comunicação em rede assíncona (UDP).

---

## 📂 Organização do Repositório

Conforme a estrutura do diretório raiz, o projeto está organizado da seguinte forma:

* **`Build/`**: Pasta que aloja o executável compilado do Unity (`VARM_Projeto2_Unity.exe`), pronto a correr de forma independente.
* **`calibracao_imagens/`**: Banco de imagens capturadas com o padrão de xadrez para o processo de calibração offline.
* **`calibracao_resultados/`**: Imagens geradas pelo script após a deteção bem-sucedida de cantos, utilizadas para validação visual.
* **`esferas/`**: Ficheiros de imagem `.png` utilizados como mapas de textura para o material das esferas virtuais no Unity.
* **`VARM_Projeto2_Unity/`**: Projeto fonte do Unity3D. Os scripts C# principais encontram-se em `Assets/Scripts/`:
  * `PoseReceiver.cs`: Responsável pela receção UDP dos dados de pose, conversão de coordenadas e posicionamento dos objetos virtuais.
  * `VideoReceiver.cs`: Responsável pela receção e reconstrução dos pacotes fragmentados de vídeo e atualização da textura de fundo.
* **`calibracao.py`**: Script de calibração de câmara que calcula a matriz de intrínsecos e os coeficientes de distorção através de um tabuleiro de xadrez ($9\times6$ cantos internos).
* **`camera_params.json`**: Ficheiro de metadados gerado pela calibração que guarda as propriedades óticas da câmara em formato offline.
* **`detecao_aruco.py`**: Aplicação de teste em OpenCV que realiza a deteção de marcadores e renderiza wireframes 3D geométricos (Cubo, Pirâmide, Casa, Obelisco, Octógono, Esfera) nativamente via `cv2.projectPoints()`.
* **`detecao_aruco_unity.py`**: Aplicação servidora em Python que captura a câmara, processa os marcadores através de `cv2.solvePnP` (com a flag `SOLVEPNP_IPPE_SQUARE`) e transmite os pacotes de dados por sockets UDP.
* **`main.py`**: Menu interativo central (CLI) que unifica e simplifica a execução de todo o ecossistema do projeto.

---

## 🛠️ Tecnologias Utilizadas e Requisitos

* **Linguagem Principal:** Python 3.10.x
* **Visão Computacional:** OpenCV (`opencv-python` v4.13.0.92)
* **Suporte Matemático:** NumPy v2.4.4
* **Motor de Renderização:** Unity3D 6000.0.x LTS (Built-in Render Pipeline)
* **Protocolo de Comunicação:** Sockets UDP assíncronos (Multithreading em C#)

> 💡 **Nota de Compatibilidade:** O ecossistema Python deste projeto foi desenvolvido e validado utilizando as distribuições mais recentes do NumPy (v2.4.4) e OpenCV (v4.13.x), garantindo a total compatibilidade da lógica de deteção ArUco e comunicação por sockets nestas versões, sem necessidade de dependências legadas.

---

## 🚀 Como Executar o Projeto

### 1. Configuração do Ambiente Python
Para garantir que o projeto funciona corretamente com as mesmas versões de dependências em qualquer máquina, o ambiente virtual (`.venv`) não foi incluído no repositório. O utilizador deve recriá-lo localmente seguindo estes passos:

```bash
# 1. Clonar o repositório e navegar até à pasta raiz do projeto
cd "C:\Caminho\Ate\Ao\Project 2"

# 2. Criar um novo ambiente virtual isolado
python -m venv .venv

# 3. Ativar o ambiente virtual
# No Windows (PowerShell):
.venv\Scripts\Activate.ps1
# No Windows (Prompt de Comando - CMD):
.venv\Scripts\activate.bat
# No Linux/MacOS:
source .venv/bin/activate

# 4. Instalar todas as dependências necessárias de forma automática
pip install -r requirements.txt 
```

### 2. Pipeline de Execução

> **Nota Crítica de Execução:** Para evitar a perda inicial de pacotes UDP e falhas de ligação nos sockets, **inicie sempre primeiro a aplicação no Unity3D** e só depois ative o servidor.

1. Certifique-se de que o ambiente virtual está ativo no seu terminal (deve aparecer `(.venv)` no início da linha de comandos) e execute o menu central:
```bash
python main.py
```
Utilize o menu interativo no terminal para gerir o ecossistema:
* **Opção 1:** Corre o pipeline de calibração (caso queira atualizar o `camera_params.json`).
* **Opção 2:** Executa o teste de deteção local com wireframes OpenCV.
* **Opção 3:** Inicia o servidor de streaming em tempo real para o Unity.
* **Opção 4:** Abre o executável Unity para a deteção ArUco.
* **Opção 0:** Sair do menu.

``` bash
=================================================================
========= MENU PRINCIPAL - PROJETO 2 VARM =======================

[Aviso] Lembra-te de abrir primeiro o Unity (Opção 4) ANTES de arrancar o servidor UDP Python (Opção 3)!
=================================================================
1. Executar Calibração da Câmara (calibracao.py)
2. Deteção ArUco - Local - Aruco lib OpenCV (detecao_aruco.py)
3. Servidor UDP para Unity (detecao_aruco_unity.py)
-----------------------------------------------------------------
4. Abrir Executável Unity (Realidade Aumentada)
0. Sair
=================================================================
Seleciona uma opção (0-4):
```

---

## 📸 Resultados do Projeto

Abaixo é possível observar a diferença entre a deteção nativa em OpenCV e a renderização sofisticada integrada com Unity3D.

<div align="center">
  <table>
    <tr>
      <td align="center"><b>Deteção Local (OpenCV)</b></td>
      <td align="center"><b>Integração Realidade Aumentada (Unity3D)</b></td>
    </tr>
    <tr>
      <td><img src="Relatorio 2 - VARM/img/detecao_aruco_local.png" width="400"></td>
      <td><img src="Relatorio 2 - VARM/img/detecao_aruco_unity_game.png" width="400"></td>
    <tr>
      <td>Wireframe geométrico renderizado nativamente.</td>
      <td>Objeto 3D com texturização alinhado ao marcador.</td>
    </tr>
  </table>
</div>