import os
import zipfile
import subprocess
from pathlib import Path
import pytest
from core.bridge_client import WordPressBridgeClient

BASE_DIR = Path(__file__).resolve().parent.parent

def test_php_syntax():
    php_path = BASE_DIR / "wordpress-plugin/unicam-seo-bridge/unicam-seo-bridge.php"
    assert php_path.exists(), f"Plugin PHP file does not exist at {php_path}"
    
    result = subprocess.run(["php", "-l", str(php_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"PHP Syntax error: {result.stderr or result.stdout}"

def test_plugin_zip_archive():
    zip_path = BASE_DIR / "wordpress-plugin/unicam-seo-bridge.zip"
    assert zip_path.exists(), f"Plugin zip does not exist at {zip_path}"
    
    with zipfile.ZipFile(str(zip_path), 'r') as z:
        namelist = z.namelist()
        assert any("unicam-seo-bridge.php" in name for name in namelist)

def test_bridge_client_initialization():
    client = WordPressBridgeClient()
    assert client.timeout == 25
