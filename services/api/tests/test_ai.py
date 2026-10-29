from app.ai import AiAnalyzer


def test_ai_detects_price_size_and_sale() -> None:
    result = AiAnalyzer().extract_product_data("Nike LeBron talla 42 Bs 450 vendido")
    assert result.brand == "Nike"
    assert result.size == "42"
    assert result.price == 450
    assert result.availability == "sold"
    assert any(signal["kind"] == "sale" for signal in result.signals)

