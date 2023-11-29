using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using System.Collections;
using System.Text;
using System.Collections.Generic;
using SimpleJSON;

public class ButtonHandler : MonoBehaviour
{
    public Slider almacenesSlider;
    public Slider cajasSlider;
    public Slider robotsSlider;

    public void OnButtonClicked()
    {
        float almacenesValue = almacenesSlider.value;
        float cajasValue = cajasSlider.value;
        float robotsValue = robotsSlider.value;

        // Imprime los valores y envía los datos
        Debug.Log("Almacenes: " + almacenesValue + ", Cajas: " + cajasValue + ", Robots: " + robotsValue);
        SendData(almacenesValue, cajasValue, robotsValue); // Llama a SendData para enviar los valores
        Debug.Log("Datos enviados");
    }

    public void SendData(float almacenesValue, float cajasValue, float robotsValue)
    {
        StartCoroutine(PostRequest("http://localhost:5000/send_data", almacenesValue, cajasValue, robotsValue));
    }

    IEnumerator PostRequest(string url, float almacenes, float cajas, float robots)
    {
        JSONNode json = new JSONObject();
        json["almacenes"] = almacenes;
        json["cajas"] = cajas;
        json["robots"] = robots;

        Debug.Log(json);

        using (UnityWebRequest www = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json.ToString());
            www.uploadHandler = (UploadHandler)new UploadHandlerRaw(bodyRaw);
            www.downloadHandler = (DownloadHandler)new DownloadHandlerBuffer();
            www.SetRequestHeader("Content-Type", "application/json");

            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.Log(www.error);
            }
            else
            {
                Debug.Log("Response: " + www.downloadHandler.text);
            }
        }
    }
}