using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Text;
using System.Collections.Generic;

[System.Serializable]
public class MarkerPose
{
    public int id;
    public float[] rvec;
    public float[] tvec;
}

public class PoseReceiver : MonoBehaviour
{
    public int port = 5001;
    public GameObject[] arPivots; // Array 6 Pivots (Do ID 0 ao ID 5)
    
    [Header("Intrínsecos da Câmara (Calibração)")]
    public float fx;
    public float fy;
    public float cx;
    public float cy;

    public float imageWidth = 1280;
    public float imageHeight = 720;
    public float markerTimeout = 0.3f;

    private UdpClient udpClient;
    private Thread receiveThread;
    private bool isRunning = true;

    // FILA THREAD-SAFE para garantir que NENHUM marcador é descartado
    private Queue<string> jsonQueue = new Queue<string>();
    private object queueLock = new object();
    
    private Dictionary<int, float> lastSeenTimes = new Dictionary<int, float>();

    void Start()
    {
        SetupVirtualCamera();

        udpClient = new UdpClient(port);
        receiveThread = new Thread(ReceiveLoop);
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    void SetupVirtualCamera()
    {
        Camera cam = Camera.main;
        float near = cam.nearClipPlane;
        float far = cam.farClipPlane;
        float w = imageWidth;
        float h = imageHeight;

        Matrix4x4 projMatrix = Matrix4x4.zero;
        projMatrix[0, 0] = 2f * fx / w;
        projMatrix[0, 2] = 1f - 2f * cx / w;
        projMatrix[1, 1] = 2f * fy / h;
        projMatrix[1, 2] = -1f + 2f * cy / h;
        projMatrix[2, 2] = -(far + near) / (far - near);
        projMatrix[2, 3] = -2f * far * near / (far - near);
        projMatrix[3, 2] = -1f;

        cam.projectionMatrix = projMatrix;
    }

    void ReceiveLoop()
    {
        IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
        while (isRunning)
        {
            try
            {
                byte[] data = udpClient.Receive(ref anyIP);
                string jsonString = Encoding.UTF8.GetString(data);
                
                // Enfileira o pacote de forma segura bloqueando acessos simultâneos
                lock (queueLock)
                {
                    jsonQueue.Enqueue(jsonString);
                }
            }
            catch { }
        }
    }

    void Update()
    {
        // PROCESSAR TODOS OS PACOTES RECEBIDOS NESTE FRAME
        lock (queueLock)
        {
            while (jsonQueue.Count > 0)
            {
                string nextJson = jsonQueue.Dequeue();
                ProcessPose(nextJson);
            }
        }

        // Esconder objetos se o marcador desaparecer da câmara (Timeout)
        for (int i = 0; i < arPivots.Length; i++)
        {
            if (arPivots[i] != null && arPivots[i].activeSelf)
            {
                if (Time.time - lastSeenTimes.GetValueOrDefault(i, 0) > markerTimeout)
                {
                    arPivots[i].SetActive(false);
                }
            }
        }
    }

    void ProcessPose(string jsonString)
    {
        MarkerPose pose = JsonUtility.FromJson<MarkerPose>(jsonString);
        if (pose == null || pose.id < 0 || pose.id >= arPivots.Length) return;

        GameObject target = arPivots[pose.id]; // Alvo é o Pivot respetivo
        if (target == null) return;

        // Converter Translação (Inverter eixo Y) - Uso de coordenadas locais para precisão ótica
        Vector3 position = new Vector3(pose.tvec[0], -pose.tvec[1], pose.tvec[2]);

        // Converter Rotação (Fórmula de Rodrigues -> Matriz R -> Quaternion)
        float lat_rx = pose.rvec[0];
        float lat_ry = pose.rvec[1];
        float lat_rz = pose.rvec[2];

        float angle = Mathf.Sqrt(lat_rx * lat_rx + lat_ry * lat_ry + lat_rz * lat_rz);
        if (angle > 0.001f)
        {
            float ax = lat_rx / angle;
            float ay = lat_ry / angle;
            float az = lat_rz / angle;

            float c = Mathf.Cos(angle);
            float s = Mathf.Sin(angle);
            float t = 1f - c;

            float r00 = t * ax * ax + c;
            float r01 = t * ax * ay - s * az;
            float r02 = t * ax * az + s * ay;

            float r10 = t * ax * ay + s * az;
            float r11 = t * ay * ay + c;
            float r12 = t * ay * az - s * ax;

            float r20 = t * ax * az - s * ay;
            float r21 = t * ay * az + s * ax;
            float r22 = t * az * az + c;

            Matrix4x4 mat = Matrix4x4.identity;
            mat[0, 0] = r00;  mat[0, 1] = -r01; mat[0, 2] = r02;
            mat[1, 0] = -r10; mat[1, 1] = r11;  mat[1, 2] = -r12;
            mat[2, 0] = r20;  mat[2, 1] = -r21; mat[2, 2] = r22;

            Quaternion rotation = mat.rotation;
            
            // Rotação perpendicular ao plano do marcador
            //Quaternion initialRotation = Quaternion.Euler(90f, 0f, 0f);
            Quaternion initialRotation = Quaternion.Euler(90f, 0f, 0f);

            //  Aplicar em espaço local do Pivot para evitar derivas na rotação
            target.transform.localPosition = position;
            target.transform.localRotation = rotation * initialRotation;

            target.SetActive(true);
            lastSeenTimes[pose.id] = Time.time;
        }
    }

    void OnApplicationQuit()
    {
        isRunning = false;
        if (udpClient != null) udpClient.Close();
        if (receiveThread != null) receiveThread.Abort();
    }
}