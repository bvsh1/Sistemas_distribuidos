import os
import zipfile
from kaggle.api.kaggle_api_extended import KaggleApi

def download_dataset():
    # Configurar API
    api = KaggleApi()
    api.authenticate()
    
    # Descargar dataset
    dataset = "jarupula/yahoo-answers-dataset"
    download_path = "datasets"
    
    os.makedirs(download_path, exist_ok=True)
    os.makedirs(os.path.join(download_path, "raw"), exist_ok=True)
    
    print("Descargando dataset...")
    api.dataset_download_files(dataset, path=download_path, unzip=False)
    
    # Descomprimir
    zip_file = os.path.join(download_path, "yahoo-answers-dataset.zip")
    if os.path.exists(zip_file):
        print("Descomprimiendo...")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(os.path.join(download_path, "raw"))
        os.remove(zip_file)
        print("Descarga completada")
    else:
        print("No se pudo descargar el dataset")

if __name__ == "__main__":
    download_dataset()
