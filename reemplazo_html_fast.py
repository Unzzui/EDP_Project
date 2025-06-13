import os

def reemplazar_navbar_en_html(directorio_base):
    original = "css/manager-theme.css"
    nuevo = "css/styles.css"

    for ruta_actual, _, archivos in os.walk(directorio_base):
        for archivo in archivos:
            if archivo.endswith(".html"):
                ruta_completa = os.path.join(ruta_actual, archivo)
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        contenido = f.read()

                    if original in contenido:
                        contenido_modificado = contenido.replace(original, nuevo)
                        with open(ruta_completa, 'w', encoding='utf-8') as f:
                            f.write(contenido_modificado)
                        print(f"✔ Reemplazo realizado en: {ruta_completa}")
                except Exception as e:
                    print(f"⚠ Error al procesar {ruta_completa}: {e}")

if __name__ == "__main__":
    ruta_base = os.path.expanduser("~/Documents/coding/EDP_Project/edp_mvp")
    reemplazar_navbar_en_html(ruta_base)
