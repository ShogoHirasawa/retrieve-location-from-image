import os
import base64
import csv
import sys
import pyheif
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def get_exif_data(img):
    exif_data = {}
    try:
        info = img._getexif()
        if info:
            for tag, value in info.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_tag_name = GPSTAGS.get(t, t)
                        gps_data[sub_tag_name] = value[t]
                    exif_data[tag_name] = gps_data
                else:
                    exif_data[tag_name] = value
    except Exception as e:
        print(f"EXIFデータ取得中にエラー: {e}")
    return exif_data

def get_coordinates(gps_info):
    def convert_to_degrees(value):
        try:
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        except Exception as e:
            print(f"度数変換エラー: {e}")
            return None

    lat, lon = None, None
    try:
        if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
            lat = convert_to_degrees(gps_info['GPSLatitude'])
            lon = convert_to_degrees(gps_info['GPSLongitude'])
            
            # 北緯・南緯、東経・西経の判定
            if gps_info['GPSLatitudeRef'] != 'N':
                lat = -lat
            if gps_info['GPSLongitudeRef'] != 'E':
                lon = -lon
    except Exception as e:
        print(f"緯度・経度取得中にエラー: {e}")
    return lon, lat

def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Base64変換中にエラー: {e}")
        return None

def load_image(file_path):
    try:
        if file_path.lower().endswith(".heic"):
            heif_file = pyheif.read(file_path)
            return Image.frombytes(
                heif_file.mode, heif_file.size, heif_file.data, "raw", heif_file.mode, heif_file.stride
            )
        return Image.open(file_path)
    except Exception as e:
        print(f"画像読み込みエラー: {e}")
        return None

def main():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        file_paths = filedialog.askopenfilenames(
            title="画像を選択してください",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("JPEG files", "*.jpeg"),
                ("All files", "*.*")
            ]
        )
    except Exception as e:
        file_paths = input("画像ファイルのパス: ").split(",")
        file_paths = [path.strip() for path in file_paths if path.strip()]

    if not file_paths:
        print("ファイルが選択されませんでした。")
        return

    output_data = []
    image_id = 1

    for file_path in file_paths:
        try:
            img = load_image(file_path)
            if img:
                exif_data = get_exif_data(img)
                gps_info = exif_data.get("GPSInfo", {})
                lon, lat = get_coordinates(gps_info)
                base64_image = image_to_base64(file_path)
                output_data.append({
                    "id": image_id,
                    "image_base64": f"data:image/jpeg;base64,{base64_image}",
                    "lon": lon,
                    "lat": lat
                })
                image_id += 1
        except Exception as e:
            print(f"{file_path} の処理中にエラー: {e}")
            
    csv_file = "output_images_data.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "image_base64", "lon", "lat"])
        writer.writeheader()
        writer.writerows(output_data)

    print(f"データが {csv_file} に書き出されました。")

if __name__ == "__main__":
    main()