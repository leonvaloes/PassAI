"""
Basic test file
"""

def test_import():
    """Test that package can be imported"""
    import src
    assert src.__version__ == "0.1.0"


def test_config_loading():
    """Test configuration loading"""
    from src.utils.config import load_config
    
    config = load_config()
    assert config is not None
    assert 'llm' in config
    assert 'audio' in config
