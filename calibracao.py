import numpy as np
import cv2
import glob
import json
import os

# ==========================================
# 1. Configurações Iniciais
# ==========================================
# Define o número de cantos internos do tabuleiro de xadrez
# não é o número de quadrados, pois um tabuleiro normal de 8x8 quadrados tem 7x7 cantos internos.
# O padrão de calibração comum do OpenCV costuma ter 9x6 cantos.
LARGURA_XADREZ = 9
ALTURA_XADREZ = 6
tamanho_quadrado_mm = 20.0 # Tamanho do lado de cada quadrado no mundo real

# Critérios de terminação para refinar a deteção dos cantos (cornerSubPix)
# Isto diz ao algoritmo para parar de procurar quando atingir a precisão desejada ou um limite de iterações.
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Preparar os pontos 3D no mundo real, ex: (0,0,0), (1,0,0), (2,0,0) ....,(8,5,0)
# Multiplicamos pelo tamanho do quadrado para termos unidades reais.
objp = np.zeros((ALTURA_XADREZ * LARGURA_XADREZ, 3), np.float32)
objp[:, :2] = np.mgrid[0:LARGURA_XADREZ, 0:ALTURA_XADREZ].T.reshape(-1, 2) * tamanho_quadrado_mm

# Arrays para guardar os pontos de todas as imagens
objpoints = [] # Pontos 3D no mundo real
imgpoints = [] # Pontos 2D no plano da imagem (onde a câmara viu os cantos)

# ==========================================
# 2. Processamento das Imagens
# ==========================================
# Carregar todas as imagens jpg da pasta
imagens = glob.glob('calibracao_imagens/*.jpg')

# Criar uma pasta para guardar os resultados
pasta_resultados = 'calibracao_resultados'
if not os.path.exists(pasta_resultados):
    os.makedirs(pasta_resultados)

print(f"Encontradas {len(imagens)} imagens. A iniciar a deteção de cantos...")

for fname in imagens:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Encontrar os cantos do tabuleiro de xadrez na imagem
    ret, corners = cv2.findChessboardCorners(gray, (LARGURA_XADREZ, ALTURA_XADREZ), None)

    # Se forem encontrados, adiciona os pontos
    if ret == True:
        objpoints.append(objp)

        # Refinar a precisão dos cantos para sub-píxeis (essencial para uma boa calibração)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)

        # Desenhar e mostrar os cantos para verificação visual
        cv2.drawChessboardCorners(img, (LARGURA_XADREZ, ALTURA_XADREZ), corners2, ret)

        # Guardar a imagem com os cantos detectados
        nome_base = os.path.basename(fname)
        caminho_guardar = os.path.join(pasta_resultados, f"cantos_{nome_base}")
        cv2.imwrite(caminho_guardar, img)

        cv2.imshow('Cantos Detetados', img)
        cv2.waitKey(500) # Mostra a imagem durante 500ms

cv2.destroyAllWindows()

# ==========================================
# 3. Calibração Matemática
# ==========================================
print("A calcular os parâmetros da câmara...")
# Função que cruza o mundo 3D (objpoints) com a imagem 2D (imgpoints)
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

print("\n--- Resultados da Calibração ---")
print("Matriz da Câmara (Intrínsecos - C):")
print(mtx)
print("\nCoeficientes de Distorção:")
print(dist)

# ==========================================
# 4. Guardar para uso futuro (Offline)
# ==========================================
# parâmetros a serem guardados para serem usados na deteção ArUco
parametros_camera = {
    "camera_matrix": mtx.tolist(),
    "dist_coeff": dist.tolist()
}

with open("camera_params.json", "w") as f:
    json.dump(parametros_camera, f, indent=4)

print("\nCalibração concluída! Parâmetros guardados em 'camera_params.json'.")