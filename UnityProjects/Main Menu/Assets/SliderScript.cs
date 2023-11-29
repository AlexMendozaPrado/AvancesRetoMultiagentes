using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class SliderScript : MonoBehaviour
{
    [SerializeField] private Slider _slider;
    [SerializeField] private TextMeshProUGUI _sliderText;
    void Start()
    {
        _slider.onValueChanged.AddListener((value)=>{
            _sliderText.text = value.ToString("0");
        });
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
