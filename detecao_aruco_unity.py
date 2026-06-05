import cv2
import numpy as np
import json
import socket

# ==============================================================================
# CONFIGURAÇÕES DE REDE (UDP)
# ==============================================================================
UNITY_IP = '127.0.0.1' # IP local
PORT_FRAME = 5000      # Porta para enviar as imagens (Vídeo)
PORT_POSE = 5001       # Porta para enviar os dados de Pose (JSON)
MAX_UDP = 60000        # Limite seguro de tamanho de pacote UDP

# Criação dos sockets UDP
sock_frame = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_pose = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def sendFrame(sock, frame, ip, port):
    """Comprime a imagem em JPEG e divide em pacotes UDP (chunks) para enviar ao Unity."""
    # Comprime a imagem (qualidade 60 para não pesar muito na rede)
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
    data = buffer.tobytes()
    num_chunks = (len(data) + MAX_UDP - 1) // MAX_UDP
    
    for i in range(num_chunks):
        chunk = data[i * MAX_UDP : (i + 1) * MAX_UDP]
        # Cabeçalho: 2 bytes para o índice do chunk + 2 bytes para o total de chunks
        header = i.to_bytes(2, 'big') + num_chunks.to_bytes(2, 'big')
        sock.sendto(header + chunk, (ip, port))

# ==============================================================================
# CONFIGURAÇÕES INICIAIS ARUCO E CÂMARA
# ==============================================================================
with open("camera_params.json", "r") as f:
    params = json.load(f)
mtx = np.array(params["camera_matrix"])
dist = np.array(params["dist_coeff"])

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters()
# refinamento para evitar que o marcador "pisque" quando está de frente
parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX 
parameters.cornerRefinementWinSize = 5

detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

marker_size = 0.05 
s = marker_size / 2

# Eixo Z positivo não é necessário para calcular a pose base, usamos a definição padrão
obj_points = np.array([
    [-s,  s, 0], [ s,  s, 0], [ s, -s, 0], [-s, -s, 0]
], dtype=np.float32)

# ==============================================================================
# LOOP PRINCIPAL
# ==============================================================================
cap = cv2.VideoCapture(0)
# Forçar resolução de calibração (HD) por conta dos dados em JSON que confirmam a resolução
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print("A iniciar servidor Python... A aguardar Unity.")
print("A enviar vídeo na porta 5000 e pose na porta 5001. Pressiona 'q' para sair.")

while True:
    ret, frame = cap.read()
    if not ret: break

    corners, ids, rejected = detector.detectMarkers(frame)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        for i in range(len(ids)):
            # Usa-se o SOLVEPNP_IPPE_SQUARE para maior estabilidade matemática
            sucesso, rvec, tvec = cv2.solvePnP(obj_points, corners[i][0], mtx, dist, flags=cv2.SOLVEPNP_IPPE_SQUARE)
            
            if sucesso:
                id_atual = int(ids[i][0])
                
                # --------------------------------------------------------------
                # ENVIAR DADOS DE POSE PARA O UNITY (Porta 5001)
                # --------------------------------------------------------------
                pose_data = {
                    'id': id_atual,
                    'rvec': rvec.flatten().tolist(),
                    'tvec': tvec.flatten().tolist()
                }
                # Formata em JSON sem espaços extra para facilitar a leitura no C#
                msg = json.dumps(pose_data, separators=(',', ':')).encode('utf-8')
                sock_pose.sendto(msg, (UNITY_IP, PORT_POSE))
                
                # Descomentar se quiseres ver os eixos no ecrã do Python
                # cv2.drawFrameAxes(frame, mtx, dist, rvec, tvec, 0.03)

    # --------------------------------------------------------------------------
    # ENVIAR FRAME DE VÍDEO PARA O UNITY (Porta 5000)
    # --------------------------------------------------------------------------
    # Envia a imagem (já com os contornos dos marcadores desenhados)
    sendFrame(sock_frame, frame, UNITY_IP, PORT_FRAME)

    cv2.imshow('Servidor Python (UDP)', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()