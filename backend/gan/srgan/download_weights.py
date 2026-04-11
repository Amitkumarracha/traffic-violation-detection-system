"""
RealESRGAN Weight Downloader
Downloads pre-trained model weights from GitHub releases
"""

import os
from pathlib import Path
import urllib.request
from urllib.error import URLError
import logging

logger = logging.getLogger(__name__)


def download_weights(
    url: str = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
    output_path: str = None,
    min_size_mb: float = 60.0
) -> bool:
    """
    Download RealESRGAN model weights from GitHub releases.
    
    Args:
        url: GitHub release URL
        output_path: Where to save the weights (default: backend/gan/srgan/weights/)
        min_size_mb: Minimum expected file size in MB (for validation)
    
    Returns:
        True if download successful, False otherwise
    """
    
    # Set default output path
    if output_path is None:
        module_dir = Path(__file__).parent
        output_path = module_dir / "weights" / "RealESRGAN_x4plus.pth"
    else:
        output_path = Path(output_path)
    
    # Create directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if already exists and is valid
    if output_path.exists():
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        if file_size_mb >= min_size_mb:
            logger.info(f"✓ Model weights already exist: {output_path}")
            return True
        else:
            logger.warning(f"Existing file too small ({file_size_mb:.1f}MB), re-downloading...")
            output_path.unlink()
    
    logger.info(f"Downloading model weights from GitHub...")
    logger.info(f"URL: {url}")
    logger.info(f"Destination: {output_path}")
    
    try:
        # Download with progress bar
        def download_with_progress(url, filepath):
            try:
                from tqdm import tqdm
            except ImportError:
                logger.warning("tqdm not installed, download progress unavailable")
                tqdm = None
            
            try:
                response = urllib.request.urlopen(url)
            except URLError as e:
                logger.error(f"Failed to connect to GitHub: {e}")
                logger.info("Check your internet connection and try again")
                return False
            
            # Get total file size
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                logger.warning("Could not determine file size from headers")
                tqdm = None
            
            chunk_size = 1024 * 1024  # 1MB chunks
            downloaded = 0
            
            # Create progress bar if available
            if tqdm:
                pbar = tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc="Downloading"
                )
            
            with open(filepath, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if tqdm:
                        pbar.update(len(chunk))
            
            if tqdm:
                pbar.close()
            
            return True
        
        # Execute download
        success = download_with_progress(url, str(output_path))
        
        if not success:
            return False
        
        # Verify file
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"✓ Downloaded: {file_size_mb:.1f}MB")
        
        if file_size_mb < min_size_mb:
            logger.error(
                f"Downloaded file too small ({file_size_mb:.1f}MB < {min_size_mb:.1f}MB). "
                f"Download may have failed. Deleting..."
            )
            output_path.unlink()
            return False
        
        logger.info("✓ Model weights downloaded and verified successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Download failed: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def check_weights(weights_path: str = None) -> bool:
    """
    Check if model weights exist and are valid.
    
    Args:
        weights_path: Path to weights file (default: backend/gan/srgan/weights/RealESRGAN_x4plus.pth)
    
    Returns:
        True if weights exist and are valid
    """
    
    if weights_path is None:
        module_dir = Path(__file__).parent
        weights_path = module_dir / "weights" / "RealESRGAN_x4plus.pth"
    else:
        weights_path = Path(weights_path)
    
    if not weights_path.exists():
        return False
    
    file_size_mb = weights_path.stat().st_size / (1024 * 1024)
    return file_size_mb >= 60.0


def main():
    """Download weights when run as script"""
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    print("""
╔═══════════════════════════════════════════════════╗
║  RealESRGAN Model Weight Downloader               ║
║  License Plate Super-Resolution (4×)              ║
╚═══════════════════════════════════════════════════╝
    """)
    
    success = download_weights()
    
    if success:
        print("\n✅ Download completed successfully!")
        return 0
    else:
        print("\n❌ Download failed!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
