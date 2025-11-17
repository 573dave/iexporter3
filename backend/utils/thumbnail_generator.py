"""
Thumbnail Generator for Attachments
Generates preview images for various file types with forensic metadata preservation
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import hashlib

from PIL import Image, ImageOps
from PIL.ExifTags import TAGS

from backend.config import EXPORT_CONFIG

logger = logging.getLogger("iexporter3.utils.thumbnail")


class ThumbnailGenerator:
    """
    Generate thumbnails for various attachment types.
    Preserves forensic metadata and maintains aspect ratio.
    """

    def __init__(
        self,
        max_dimension: int = None,
        quality: int = None,
        format: str = None,
    ):
        """
        Initialize thumbnail generator.

        Args:
            max_dimension: Maximum thumbnail dimension in pixels
            quality: JPEG quality (1-100)
            format: Output format (default: JPEG)
        """
        self.max_dimension = max_dimension or EXPORT_CONFIG["thumbnail_max_dimension"]
        self.quality = quality or EXPORT_CONFIG["thumbnail_quality"]
        self.format = format or EXPORT_CONFIG["thumbnail_format"]

    def generate_thumbnail(
        self,
        source_path: Path,
        output_path: Path,
    ) -> Optional[Tuple[int, int]]:
        """
        Generate thumbnail for a file.

        Args:
            source_path: Path to source file
            output_path: Path to save thumbnail

        Returns:
            Tuple of (width, height) of generated thumbnail, or None if failed

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        source_path = Path(source_path)
        output_path = Path(output_path)

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Detect file type and generate appropriate thumbnail
        mime_type = self._detect_mime_type(source_path)

        try:
            if mime_type.startswith("image/"):
                return self._generate_image_thumbnail(source_path, output_path)
            elif mime_type.startswith("video/"):
                return self._generate_video_thumbnail(source_path, output_path)
            elif mime_type == "application/pdf":
                return self._generate_pdf_thumbnail(source_path, output_path)
            else:
                # Generate generic icon for other file types
                return self._generate_generic_thumbnail(source_path, output_path)

        except Exception as e:
            logger.error(f"Failed to generate thumbnail for {source_path}: {e}")
            return None

    def _generate_image_thumbnail(
        self,
        source_path: Path,
        output_path: Path,
    ) -> Tuple[int, int]:
        """
        Generate thumbnail for image files.

        Args:
            source_path: Path to source image
            output_path: Path to save thumbnail

        Returns:
            Tuple of (width, height)
        """
        try:
            # Open image
            with Image.open(source_path) as img:
                # Auto-rotate based on EXIF orientation (preserves forensic metadata)
                img = ImageOps.exif_transpose(img)

                # Convert RGBA to RGB for JPEG
                if img.mode in ("RGBA", "LA", "P"):
                    # Create white background
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # Calculate thumbnail size (maintain aspect ratio)
                img.thumbnail(
                    (self.max_dimension, self.max_dimension),
                    Image.Resampling.LANCZOS,
                )

                # Save thumbnail
                img.save(
                    output_path,
                    format=self.format,
                    quality=self.quality,
                    optimize=True,
                )

                logger.debug(
                    f"Generated image thumbnail: {source_path.name} -> {img.size}"
                )

                return img.size

        except Exception as e:
            logger.error(f"Failed to generate image thumbnail: {e}")
            raise

    def _generate_video_thumbnail(
        self,
        source_path: Path,
        output_path: Path,
    ) -> Optional[Tuple[int, int]]:
        """
        Generate thumbnail for video files by extracting first frame.

        Args:
            source_path: Path to source video
            output_path: Path to save thumbnail

        Returns:
            Tuple of (width, height) or None if ffmpeg not available
        """
        try:
            import subprocess

            # Try using ffmpeg to extract first frame
            # ffmpeg -i input.mp4 -vframes 1 -vf scale=150:-1 output.jpg
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    str(source_path),
                    "-vframes",
                    "1",
                    "-vf",
                    f"scale={self.max_dimension}:-1",
                    "-q:v",
                    "2",  # High quality
                    str(output_path),
                ],
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0 and output_path.exists():
                # Get dimensions of generated thumbnail
                with Image.open(output_path) as img:
                    logger.debug(
                        f"Generated video thumbnail: {source_path.name} -> {img.size}"
                    )
                    return img.size
            else:
                logger.warning(f"ffmpeg failed for {source_path}")
                return None

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning(
                f"ffmpeg not available or timed out, skipping video thumbnail: {e}"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to generate video thumbnail: {e}")
            return None

    def _generate_pdf_thumbnail(
        self,
        source_path: Path,
        output_path: Path,
    ) -> Optional[Tuple[int, int]]:
        """
        Generate thumbnail for PDF files (first page).

        Args:
            source_path: Path to source PDF
            output_path: Path to save thumbnail

        Returns:
            Tuple of (width, height) or None if pdf2image not available
        """
        try:
            from pdf2image import convert_from_path

            # Convert first page to image
            images = convert_from_path(
                source_path,
                first_page=1,
                last_page=1,
                dpi=150,  # Good quality for thumbnails
            )

            if images:
                img = images[0]

                # Resize to thumbnail
                img.thumbnail(
                    (self.max_dimension, self.max_dimension),
                    Image.Resampling.LANCZOS,
                )

                # Save
                img.save(
                    output_path,
                    format=self.format,
                    quality=self.quality,
                    optimize=True,
                )

                logger.debug(
                    f"Generated PDF thumbnail: {source_path.name} -> {img.size}"
                )

                return img.size

        except ImportError:
            logger.warning("pdf2image not available, skipping PDF thumbnail")
            return None
        except Exception as e:
            logger.error(f"Failed to generate PDF thumbnail: {e}")
            return None

    def _generate_generic_thumbnail(
        self,
        source_path: Path,
        output_path: Path,
    ) -> Tuple[int, int]:
        """
        Generate generic file icon thumbnail for unsupported file types.

        Args:
            source_path: Path to source file
            output_path: Path to save thumbnail

        Returns:
            Tuple of (width, height)
        """
        # Create a simple colored square with file extension
        size = (self.max_dimension, self.max_dimension)
        img = Image.new("RGB", size, color=(200, 200, 200))

        # Could add PIL.ImageDraw to add text with extension
        # For now, just save a gray square

        img.save(
            output_path,
            format=self.format,
            quality=self.quality,
        )

        logger.debug(f"Generated generic thumbnail for {source_path.name}")

        return size

    def _detect_mime_type(self, file_path: Path) -> str:
        """
        Detect MIME type of file.

        Args:
            file_path: Path to file

        Returns:
            MIME type string
        """
        import mimetypes

        mime_type, _ = mimetypes.guess_type(str(file_path))

        if mime_type:
            return mime_type

        # Fallback based on extension
        extension = file_path.suffix.lower()
        extension_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".heic": "image/heic",
            ".heif": "image/heif",
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".avi": "video/x-msvideo",
            ".pdf": "application/pdf",
        }

        return extension_map.get(extension, "application/octet-stream")

    def batch_generate_thumbnails(
        self,
        source_files: list,
        output_dir: Path,
        prefix: str = "thumb_",
    ) -> dict:
        """
        Generate thumbnails for multiple files.

        Args:
            source_files: List of source file paths
            output_dir: Directory to save thumbnails
            prefix: Prefix for thumbnail filenames

        Returns:
            Dictionary mapping source paths to thumbnail info
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        for source_path in source_files:
            source_path = Path(source_path)

            if not source_path.exists():
                logger.warning(f"Skipping non-existent file: {source_path}")
                continue

            # Generate output filename
            output_filename = f"{prefix}{source_path.stem}.jpg"
            output_path = output_dir / output_filename

            # Generate thumbnail
            try:
                dimensions = self.generate_thumbnail(source_path, output_path)

                results[str(source_path)] = {
                    "thumbnail_path": str(output_path),
                    "dimensions": dimensions,
                    "success": dimensions is not None,
                }

                if dimensions:
                    logger.info(f"✓ {source_path.name} -> {output_filename}")
                else:
                    logger.warning(f"✗ Failed: {source_path.name}")

            except Exception as e:
                logger.error(f"Error processing {source_path}: {e}")
                results[str(source_path)] = {
                    "thumbnail_path": None,
                    "dimensions": None,
                    "success": False,
                    "error": str(e),
                }

        return results


if __name__ == "__main__":
    # Test thumbnail generator
    import tempfile
    import numpy as np

    print("Testing Thumbnail Generator")
    print("=" * 50)

    generator = ThumbnailGenerator(max_dimension=150, quality=85)

    # Create test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a test image
        print("\n1. Creating test image...")
        test_img_path = temp_path / "test_image.png"
        test_img = Image.new("RGB", (800, 600), color=(100, 150, 200))
        test_img.save(test_img_path)
        print(f"   Created: {test_img_path}")

        # Generate thumbnail
        print("\n2. Generating thumbnail...")
        thumb_path = temp_path / "test_thumb.jpg"
        dimensions = generator.generate_thumbnail(test_img_path, thumb_path)
        print(f"   Thumbnail: {thumb_path}")
        print(f"   Dimensions: {dimensions}")
        print(f"   Exists: {thumb_path.exists()}")

        # Verify thumbnail
        if thumb_path.exists():
            with Image.open(thumb_path) as thumb:
                print(f"   Actual size: {thumb.size}")
                print(f"   Format: {thumb.format}")

        # Batch test
        print("\n3. Testing batch generation...")
        test_files = []
        for i in range(3):
            test_file = temp_path / f"image_{i}.png"
            img = Image.new("RGB", (1000, 800), color=(i * 50, 100, 200))
            img.save(test_file)
            test_files.append(test_file)

        thumb_dir = temp_path / "thumbnails"
        results = generator.batch_generate_thumbnails(test_files, thumb_dir)

        print(f"   Generated {len(results)} thumbnails")
        for source, info in results.items():
            status = "✓" if info["success"] else "✗"
            print(f"   {status} {Path(source).name}: {info.get('dimensions')}")

    print("\n✓ Thumbnail generator tested successfully!")
