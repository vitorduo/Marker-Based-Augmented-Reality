import cv2
import numpy as np
import json

# ==============================================================================
# 1. FUNÇÕES AUXILIARES PARA DESENHAR AS 6 FORMAS 3D (Wireframes)
# ==============================================================================
def desenhar_cubo(img, pontos, cor):
    pts = np.int32(pontos).reshape(-1, 2)
    cv2.drawContours(img, [pts[:4]], -1, cor, 2) # Base
    cv2.drawContours(img, [pts[4:]], -1, cor, 2) # Topo
    for i in range(4): cv2.line(img, tuple(pts[i]), tuple(pts[i+4]), cor, 2)

def desenhar_piramide(img, pontos, cor):
    pts = np.int32(pontos).reshape(-1, 2)
    cv2.drawContours(img, [pts[:4]], -1, cor, 2) # Base
    for i in range(4): cv2.line(img, tuple(pts[i]), tuple(pts[4]), cor, 2)

def desenhar_casa_ou_obelisco(img, pontos, cor):
    pts = np.int32(pontos).reshape(-1, 2)
    cv2.drawContours(img, [pts[:4]], -1, cor, 2) # Base
    cv2.drawContours(img, [pts[4:8]], -1, cor, 2) # Teto (Base do telhado)
    for i in range(4): cv2.line(img, tuple(pts[i]), tuple(pts[i+4]), cor, 2) # Paredes
    for i in range(4): cv2.line(img, tuple(pts[i+4]), tuple(pts[8]), cor, 2) # Telhado

def desenhar_octogono(img, pontos, cor):
    pts = np.int32(pontos).reshape(-1, 2)
    cv2.drawContours(img, [pts[:8]], -1, cor, 2) # Base octogonal
    cv2.drawContours(img, [pts[8:]], -1, cor, 2) # Topo octogonal
    for i in range(8): cv2.line(img, tuple(pts[i]), tuple(pts[i+8]), cor, 2)

def desenhar_esfera(img, pontos, cor):
    pts = np.int32(pontos).reshape(-1, 2)
    # A esfera é composta por 3 círculos (equador, meridiano X, meridiano Y) de 30 pontos cada
    cv2.polylines(img, [pts[0:30]], True, cor, 2)
    cv2.polylines(img, [pts[30:60]], True, cor, 2)
    cv2.polylines(img, [pts[60:90]], True, cor, 2)

# ==============================================================================
# 2. CONFIGURAÇÕES INICIAIS ARUCO E CÂMARA
# ==============================================================================
with open("camera_params.json", "r") as f:
    params = json.load(f)
mtx = np.array(params["camera_matrix"])
dist = np.array(params["dist_coeff"])

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters()

parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX # Refina os cantos do ArUco a nível de sub-píxel
parameters.cornerRefinementWinSize = 5

detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

marker_size = 0.05 
s = marker_size / 2

obj_points = np.array([
    [-s,  s, 0], [ s,  s, 0], [ s, -s, 0], [-s, -s, 0]
], dtype=np.float32)

# ==============================================================================
# 3. DEFINIÇÃO MATEMÁTICA DOS VÉRTICES (PONTOS 3D) PARA CADA OBJETO
# Eixo Z positivo para os objetos saírem do papel na direção da câmara
# ==============================================================================

# ID 0: CUBO
v_cubo = np.float32([
    [-s, s, 0], [s, s, 0], [s, -s, 0], [-s, -s, 0],              # Base
    [-s, s, marker_size], [s, s, marker_size], [s, -s, marker_size], [-s, -s, marker_size] # Topo
])

# ID 1: PIRÂMIDE
v_piramide = np.float32([
    [-s, s, 0], [s, s, 0], [s, -s, 0], [-s, -s, 0],              # Base
    [0, 0, marker_size * 1.5]                                    # Topo
])

# ID 2: CASA (Cubo com telhado em cima)
v_casa = np.float32([
    [-s, s, 0], [s, s, 0], [s, -s, 0], [-s, -s, 0],              # Chão
    [-s, s, marker_size], [s, s, marker_size], [s, -s, marker_size], [-s, -s, marker_size], # Teto
    [0, 0, marker_size * 1.8]                                    # Ponta do telhado
])

# ID 3: OBELISCO EM PÉ (Base estreita, muito alto e pontiagudo)
so = s / 2 # Obelisco é mais estreito que o marcador
v_obelisco = np.float32([
    [-so, so, 0], [so, so, 0], [so, -so, 0], [-so, -so, 0],      # Base estreita
    [-so, so, marker_size*2], [so, so, marker_size*2], [so, -so, marker_size*2], [-so, -so, marker_size*2], # Tronco
    [0, 0, marker_size * 2.5]                                    # Ponta
])

# ID 4: PRISMA OCTOGONAL
angulos = np.linspace(0, 2 * np.pi, 8, endpoint=False)
base_oct = [[s * np.cos(a), s * np.sin(a), 0] for a in angulos]
topo_oct = [[s * np.cos(a), s * np.sin(a), marker_size] for a in angulos]
v_octogono = np.float32(base_oct + topo_oct)

# ID 5: ESFERA (3 anéis orbitais centrados no meio do marcador, mas puxados para cima)
angulos_esf = np.linspace(0, 2 * np.pi, 30)
r = s # Raio da esfera
esf_xy = [[r * np.cos(a), r * np.sin(a), r] for a in angulos_esf]           # Equador (plano XY)
esf_xz = [[r * np.cos(a), 0, r * np.sin(a) + r] for a in angulos_esf]       # Meridiano 1 (plano XZ)
esf_yz = [[0, r * np.cos(a), r * np.sin(a) + r] for a in angulos_esf]       # Meridiano 2 (plano YZ)
v_esfera = np.float32(esf_xy + esf_xz + esf_yz)

# ==============================================================================
# 4. LOOP PRINCIPAL DE DETEÇÃO
# ==============================================================================
cap = cv2.VideoCapture(0)
print("A iniciar câmara... Pressiona 'q' para sair.")

while True:
    ret, frame = cap.read()
    if not ret: break

    corners, ids, rejected = detector.detectMarkers(frame)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        for i in range(len(ids)):
            id_atual = ids[i][0]
            sucesso, rvec, tvec = cv2.solvePnP(obj_points, corners[i][0], mtx, dist, flags=cv2.SOLVEPNP_IPPE_SQUARE)
            
            if sucesso:
                # ----------------------------------------------------------------------
                # PROJETAR E DESENHAR FORMAS CONSOANTE O ID
                # Cores em formato (B, G, R)
                # ----------------------------------------------------------------------
                if id_atual == 0:
                    pts, _ = cv2.projectPoints(v_cubo, rvec, tvec, mtx, dist)
                    desenhar_cubo(frame, pts, (0, 0, 255)) # Cubo Vermelho
                    
                elif id_atual == 1:
                    pts, _ = cv2.projectPoints(v_piramide, rvec, tvec, mtx, dist)
                    desenhar_piramide(frame, pts, (0, 255, 0)) # Pirâmide Verde
                    
                elif id_atual == 2:
                    pts, _ = cv2.projectPoints(v_casa, rvec, tvec, mtx, dist)
                    desenhar_casa_ou_obelisco(frame, pts, (255, 0, 0)) # Casa Azul
                    
                elif id_atual == 3:
                    pts, _ = cv2.projectPoints(v_obelisco, rvec, tvec, mtx, dist)
                    desenhar_casa_ou_obelisco(frame, pts, (0, 255, 255)) # Obelisco Amarelo
                    
                elif id_atual == 4:
                    pts, _ = cv2.projectPoints(v_octogono, rvec, tvec, mtx, dist)
                    desenhar_octogono(frame, pts, (255, 0, 255)) # Octógono Magenta
                    
                elif id_atual == 5:
                    pts, _ = cv2.projectPoints(v_esfera, rvec, tvec, mtx, dist)
                    desenhar_esfera(frame, pts, (255, 255, 0)) # Esfera Ciano
                
                # Descomentar a linha abaixo se quiseres ver os eixos originais
                # cv2.drawFrameAxes(frame, mtx, dist, rvec, tvec, 0.03)

    cv2.imshow('Deteção ArUco e Pose', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()