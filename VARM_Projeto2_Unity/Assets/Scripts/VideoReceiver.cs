using UnityEngine;
using UnityEngine.UI;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Collections.Generic;

public class VideoReceiver : MonoBehaviour
{
    public int port = 5000;
    public RawImage displayImage;
    public int imageWidth = 640;
    public int imageHeight = 480;

    private UdpClient udpClient;
    private Thread receiveThread;
    private bool isRunning = true;

    private Dictionary<int, byte[]> chunks = new Dictionary<int, byte[]>();
    private byte[] latestFrameData;
    private bool newFrameAvailable = false;

    private Texture2D videoTexture;
    private Material mat;

    void Start()
    {
        // Criação do material e textura por código conforme o guião
        videoTexture = new Texture2D(imageWidth, imageHeight, TextureFormat.RGB24, false);
        mat = new Material(Shader.Find("Unlit/Texture"));
        mat.mainTexture = videoTexture;
        displayImage.material = mat;

        udpClient = new UdpClient(port);
        receiveThread = new Thread(ReceiveLoop);
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    void ReceiveLoop()
    {
        IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
        while (isRunning)
        {
            try
            {
                byte[] data = udpClient.Receive(ref anyIP);
                
                // Reconstrução dos pacotes fragmentados (Protocolo do Guião)
                int chunkIndex = (data[0] << 8) | data[1];
                int totalChunks = (data[2] << 8) | data[3];

                byte[] payload = new byte[data.Length - 4];
                System.Array.Copy(data, 4, payload, 0, payload.Length);
                chunks[chunkIndex] = payload;

                if (chunks.Count == totalChunks)
                {
                    List<byte> fullFrame = new List<byte>();
                    for (int i = 0; i < totalChunks; i++)
                    {
                        if (chunks.ContainsKey(i)) fullFrame.AddRange(chunks[i]);
                    }
                    latestFrameData = fullFrame.ToArray();
                    newFrameAvailable = true;
                    chunks.Clear();
                }
            }
            catch { /* Ignorar erros de fecho de socket */ }
        }
    }

    void Update()
    {
        // O Unity só permite aplicar texturas na main thread
        if (newFrameAvailable && latestFrameData != null)
        {
            videoTexture.LoadImage(latestFrameData);
            videoTexture.Apply();
            newFrameAvailable = false;
        }
    }

    void OnApplicationQuit()
    {
        isRunning = false;
        if (udpClient != null) udpClient.Close();
        if (receiveThread != null) receiveThread.Abort();
    }
}