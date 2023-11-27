using UnityEngine;
using UnityEngine.UI;

public class SliderController : MonoBehaviour
{
    public Slider almacenesSlider;
    public Slider cajasSlider;

    void Start()
    {
        // Inicializa los sliders aquí si no los asignaste en el editor
        almacenesSlider.onValueChanged.AddListener(delegate { UpdateMaxCajas(); });
        UpdateMaxCajas(); // Para establecer el valor inicial
    }

    void UpdateMaxCajas()
    {
        cajasSlider.maxValue = almacenesSlider.value * 3;
    }
}
