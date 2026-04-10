import pytest
from unittest.mock import patch
from backend.core.semantic_cache import get_cache, set_cached, INDEX_KEY

@pytest.fixture
def mock_redis():
    """Mock redis to use a local dictionary so we can test the cache logic in isolation."""
    with patch("backend.core.semantic_cache.redis") as mock_r:
        memory = {}
        
        async def fake_get(key):
            return memory.get(key)
            
        async def fake_setex(key, ttl, value):
            memory[key] = value
            
        mock_r.get.side_effect = fake_get
        mock_r.setex.side_effect = fake_setex
        yield mock_r

@pytest.mark.asyncio
async def test_semantic_cache_flow(mock_redis):
    res1 = await get_cache("what is deep learning?")
    assert res1 is None, "Empty cache should return None"

    fake_result = {"answer": "Deep learning is a subset of machine learning."}
    await set_cached("What is deep learning?", fake_result)

    assert mock_redis.setex.call_count == 2 
    exact_res = await get_cache("What is deep learning?")
    assert exact_res == fake_result, "Exact match should hit the cache"

    similar_res = await get_cache("Can you explain what deep learning is?")
    assert similar_res == fake_result, "Semantically similar query should hit the cache"

    dissimilar_res = await get_cache("How do I bake a chocolate cake?")
    assert dissimilar_res is None, "Dissimilar query should miss the cache"

@pytest.mark.asyncio
async def test_similarity_threshold_boundary(mock_redis):
    """Specifically tests the SIMILARITY_THRESHOLDE value."""
    await set_cached("Baseline text", {"answer": "Some baseline answer"})
    
    with patch("backend.core.semantic_cache.cosine_similarity") as mock_sim:
        
        mock_sim.return_value = 0.849
        miss_res = await get_cache("Another text")
        assert miss_res is None, "Score of 0.849 should be rejected (below threshold)"
        mock_sim.return_value = 0.851
        hit_res = await get_cache("Another text")
        assert hit_res is not None, "Score of 0.851 should be accepted (above threshold)"
        assert hit_res == {"answer": "Some baseline answer"}
