import os
import gradio as gr
from batdetect2 import api, plot
import matplotlib.pyplot as plt
import pandas as pd
import librosa
import tempfile

# Inicjalizacja: batdetect2 automatycznie pobierze wagi modelu przy pierwszym uruchomieniu.

def analyze_bat_audio(file_obj, threshold):
    """
    Główna funkcja analizująca plik audio WAV.
    Zwraca: (Spektrogram, Tabela wyników, Plik CSV, Komunikat statusu)
    """
    if file_obj is None:
        return None, None, None, "### Status: Proszę wybrać plik WAV."

    file_path = file_obj.name
    
    # Walidacja rozszerzenia
    if not file_path.lower().endswith('.wav'):
        return None, None, None, "### Status: Błąd! Obsługiwane są tylko pliki .WAV."

    try:
        # Sprawdzenie częstotliwości próbkowania (SR)
        y, sr = librosa.load(file_path, sr=None)
        if sr < 44100:
            return None, None, None, f"### Status: Błąd! Zbyt niska częstotliwość próbkowania ({sr} Hz). Minimalna to 44.1 kHz."

        # Załadowanie audio przez API batdetect2
        audio = api.load_audio(file_path)
        
        # Proces detekcji i klasyfikacji
        # Pobranie domyślnej konfiguracji i aktualizacja progu detekcji
        cfg = api.get_config()
        cfg['detection_threshold'] = threshold
        
        detections, features, spec = api.process_audio(audio, config=cfg)

        # Generowanie sonogramu
        fig = plt.figure(figsize=(12, 6), dpi=100)
        plot.plot_spectrogram(spec, detections=detections)
        plt.title(f"Sonogram: {os.path.basename(file_path)} (Próg: {threshold})")
        plt.tight_layout()
        
        csv_path = None
        # Przygotowanie danych do tabeli
        if len(detections) > 0:
            results_data = []
            for det in detections:
                results_data.append({
                    "Gatunek": str(det.get('class_name', 'Nieznany')),
                    "Pewność (%)": float(round(det.get('det_prob', 0) * 100, 2)),
                    "Start (s)": float(round(det.get('start_time', 0), 4)),
                    "Koniec (s)": float(round(det.get('end_time', 0), 4)),
                    "Częst. min (kHz)": float(round(det.get('low_freq', 0) / 1000, 1)),
                    "Częst. max (kHz)": float(round(det.get('high_freq', 0) / 1000, 1))
                })
            df_results = pd.DataFrame(results_data)
            
            # Tworzenie tymczasowego pliku CSV do pobrania
            temp_dir = tempfile.gettempdir()
            csv_path = os.path.join(temp_dir, f"BatIDPro_Results_{os.path.basename(file_path)}.csv")
            df_results.to_csv(csv_path, index=False)
            
            status_msg = f"### Status: Sukces! Wykryto {len(detections)} sygnałów."
        else:
            df_results = pd.DataFrame(columns=["Gatunek", "Pewność (%)", "Start (s)", "Koniec (s)", "Częst. min (kHz)", "Częst. max (kHz)"])
            status_msg = "### Status: Nie wykryto głosów nietoperzy przy wybranej czułości."

        return fig, df_results, csv_path, status_msg

    except Exception as e:
        return None, None, None, f"### Status: Wystąpił błąd krytyczny: {str(e)}"

# Custom CSS for a more professional "non-AI" look
css = """
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
#title-header {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
    color: white;
    border-radius: 12px;
    margin-bottom: 25px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
#title-header h1 {
    margin: 0;
    font-weight: 800;
    letter-spacing: -1px;
}
.main-button {
    background: #10b981 !important;
    border: none !important;
    font-weight: 600 !important;
}
.secondary-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 15px;
}
"""

# Definicja nowoczesnego motywu wizualnego
theme = gr.themes.Default(
    primary_hue="emerald",
    secondary_hue="zinc",
    neutral_hue="slate",
).set(
    block_radius="lg",
    button_primary_background_fill="*primary_600",
    button_primary_background_fill_hover="*primary_700",
)

# Budowa interfejsu Gradio
with gr.Blocks(theme=theme, css=css, title="Bat ID Pro - System Analizy", analytics_enabled=False) as demo:
    with gr.Column(elem_id="title-header"):
        gr.Markdown("# 🦇 Bat ID Pro")
        gr.Markdown("Ekspercki system monitoringu i bioakustyki nietoperzy")
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                audio_input = gr.File(label="Wgraj nagranie bioakustyczne", file_types=[".wav"])
                
                sensitivity_slider = gr.Slider(
                    minimum=0.1, 
                    maximum=0.9, 
                    value=0.5, 
                    step=0.05, 
                    label="Czułość detekcji (Threshold)",
                    info="Im niższa wartość, tym czulszy model (więcej detekcji, ale i szumu)."
                )
                
                analyze_btn = gr.Button("🔍 ROZPOCZNIJ ANALIZĘ", variant="primary", elem_classes="main-button")
            
            with gr.Group(elem_classes="secondary-box"):
                status_output = gr.Markdown("### Status\nOczekiwanie na dane...")
                download_output = gr.File(label="Pobierz wyniki (CSV)", interactive=False)

            gr.Markdown(
                """
                ### 💡 Wskazówki techniczne
                - **Optymalne SR:** > 250 kHz
                - **Silnik:** BatDetect2 (Pytorch)
                - **Klasyfikacja:** Gatunki europejskie i północnoamerykańskie.
                """
            )

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("Wizualizacja"):
                    output_plot = gr.Plot(label="Analiza spektralna (Sonogram)")
                with gr.TabItem("Tabela Gatunków"):
                    output_table = gr.Dataframe(
                        headers=["Gatunek", "Pewność (%)", "Start (s)", "Koniec (s)", "Częst. min (kHz)", "Częst. max (kHz)"],
                        datatype=["str", "number", "number", "number", "number", "number"],
                        interactive=False,
                        wrap=True
                    )

    analyze_btn.click(
        fn=analyze_bat_audio,
        inputs=[audio_input, sensitivity_slider],
        outputs=[output_plot, output_table, download_output, status_output]
    )

    gr.Markdown(
        "<div style='text-align: center; color: #64748b; font-size: 0.8em; margin-top: 20px;'>"
        "Bat ID Pro v1.1 | Profesjonalne narzędzie do analizy bioakustycznej"
        "</div>"
    )

if __name__ == "__main__":
    demo.queue(api_open=False)
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=True,
        share=True,
        show_error=True,
        show_api=False
    )
