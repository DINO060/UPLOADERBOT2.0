"""
Opérations sur les fichiers
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, BinaryIO
from PIL import Image
import aiofiles


async def save_file(
    file_data: bytes,
    directory: str,
    filename: str
) -> str:
    """
    Sauvegarde un fichier sur le disque
    
    Args:
        file_data: Données du fichier
        directory: Répertoire de destination
        filename: Nom du fichier
    
    Returns:
        Chemin complet du fichier sauvegardé
    """
    # Créer le répertoire si nécessaire
    Path(directory).mkdir(parents=True, exist_ok=True)
    
    filepath = os.path.join(directory, filename)
    
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(file_data)
    
    return filepath


async def read_file(filepath: str) -> bytes:
    """
    Lit un fichier depuis le disque
    
    Args:
        filepath: Chemin du fichier
    
    Returns:
        Données du fichier
    """
    async with aiofiles.open(filepath, 'rb') as f:
        return await f.read()


def delete_file(filepath: str) -> bool:
    """
    Supprime un fichier
    
    Args:
        filepath: Chemin du fichier
    
    Returns:
        True si supprimé avec succès
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception:
        return False


def get_file_size(filepath: str) -> int:
    """
    Obtient la taille d'un fichier
    
    Args:
        filepath: Chemin du fichier
    
    Returns:
        Taille en bytes
    """
    try:
        return os.path.getsize(filepath)
    except:
        return 0


def get_file_hash(filepath: str, algorithm: str = "md5") -> str:
    """
    Calcule le hash d'un fichier
    
    Args:
        filepath: Chemin du fichier
        algorithm: Algorithme de hash (md5, sha1, sha256)
    
    Returns:
        Hash hexadécimal
    """
    hash_func = getattr(hashlib, algorithm)()
    
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def get_mime_type(filepath: str) -> str:
    """
    Détermine le type MIME d'un fichier
    
    Args:
        filepath: Chemin du fichier
    
    Returns:
        Type MIME
    """
    mime_type, _ = mimetypes.guess_type(filepath)
    return mime_type or "application/octet-stream"


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier
    
    Args:
        filename: Nom de fichier à nettoyer
    
    Returns:
        Nom de fichier sécurisé
    """
    # Caractères interdits
    invalid_chars = '<>:"/\\|?*'
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limiter la longueur
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]
    
    return name + ext


def generate_unique_filename(
    base_name: str,
    directory: str
) -> str:
    """
    Génère un nom de fichier unique
    
    Args:
        base_name: Nom de base
        directory: Répertoire de destination
    
    Returns:
        Nom de fichier unique
    """
    name, ext = os.path.splitext(base_name)
    counter = 0
    filename = base_name
    
    while os.path.exists(os.path.join(directory, filename)):
        counter += 1
        filename = f"{name}_{counter}{ext}"
    
    return filename


async def create_thumbnail(
    image_path: str,
    output_path: str,
    size: Tuple[int, int] = (320, 320)
) -> bool:
    """
    Crée une miniature d'une image
    
    Args:
        image_path: Chemin de l'image source
        output_path: Chemin de sortie
        size: Taille de la miniature (largeur, hauteur)
    
    Returns:
        True si créé avec succès
    """
    try:
        with Image.open(image_path) as img:
            # Conserver le ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Sauvegarder
            img.save(output_path, optimize=True, quality=85)
            
        return True
    except Exception:
        return False


async def add_watermark(
    image_path: str,
    watermark_text: str,
    output_path: str,
    position: str = "bottom-right",
    opacity: float = 0.7
) -> bool:
    """
    Ajoute un watermark à une image
    
    Args:
        image_path: Chemin de l'image
        watermark_text: Texte du watermark
        output_path: Chemin de sortie
        position: Position du watermark
        opacity: Opacité (0-1)
    
    Returns:
        True si ajouté avec succès
    """
    try:
        from PIL import ImageDraw, ImageFont
        
        with Image.open(image_path) as img:
            # Créer une couche pour le watermark
            watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # Essayer de charger une police
            try:
                font_size = int(img.height * 0.05)  # 5% de la hauteur
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculer la position
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            margin = 10
            if position == "bottom-right":
                x = img.width - text_width - margin
                y = img.height - text_height - margin
            elif position == "bottom-left":
                x = margin
                y = img.height - text_height - margin
            elif position == "top-right":
                x = img.width - text_width - margin
                y = margin
            elif position == "top-left":
                x = margin
                y = margin
            else:  # center
                x = (img.width - text_width) // 2
                y = (img.height - text_height) // 2
            
            # Dessiner le texte
            draw.text(
                (x, y),
                watermark_text,
                fill=(255, 255, 255, int(255 * opacity)),
                font=font
            )
            
            # Fusionner les images
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, watermark)
            img = img.convert('RGB')
            
            # Sauvegarder
            img.save(output_path, optimize=True, quality=90)
            
        return True
    except Exception:
        return False


def get_video_info(video_path: str) -> Optional[dict]:
    """
    Obtient les informations d'une vidéo
    
    Args:
        video_path: Chemin de la vidéo
    
    Returns:
        Dictionnaire avec les infos (durée, résolution, etc.)
    """
    try:
        import cv2
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            "duration": int(duration),
            "width": width,
            "height": height,
            "fps": fps,
            "frame_count": int(frame_count)
        }
    except:
        return None


def clean_temp_files(directory: str, max_age_hours: int = 24) -> int:
    """
    Nettoie les fichiers temporaires
    
    Args:
        directory: Répertoire à nettoyer
        max_age_hours: Âge maximum des fichiers en heures
    
    Returns:
        Nombre de fichiers supprimés
    """
    import time
    
    if not os.path.exists(directory):
        return 0
    
    deleted = 0
    max_age_seconds = max_age_hours * 3600
    current_time = time.time()
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        if os.path.isfile(filepath):
            file_age = current_time - os.path.getmtime(filepath)
            
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                    deleted += 1
                except:
                    pass
    
    return deleted
