#!/data/data/com.termux/files/usr/bin/bash

echo " Instalando dependencias para RB-Multiplatform..."

# Actualizar repositorios y paquetes base
pkg update -y && pkg upgrade -y

# Instalar Python, Git y FFmpeg (Vital para el audio/video)
pkg install python ffmpeg git -y

# Instalar las librerías de Python necesarias
pip install --upgrade pip
pip install -r requirements.txt

echo "¡Instalación completada con éxito!"
echo " Ejecuta tu script con: python spotify.py"
