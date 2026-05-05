# agents/agent_factory.py
from functools import partial
from agents.react_agent import run_react_agent, run_with_reflexion

# Bước 1: Registry dict — key là tên strategy, value là function
# Dùng dict thay vì if/else để dễ mở rộng: thêm strategy mới chỉ cần thêm 1 dòng vào đây
STRATEGY_REGISTRY = {
    "react":      run_react_agent,
    "reflexion":  run_with_reflexion,
}


# Bước 2: list_strategies — chỉ cần trả về keys của registry
def list_strategies() -> list[str]:
    """Trả về danh sách tên các strategy có sẵn."""
    return list(STRATEGY_REGISTRY.keys())


# Bước 3: create_agent — lookup registry, đóng gói tools vào function trả về
def create_agent(strategy: str, tools: dict):
    """
    Trả về callable: agent_fn(task) -> str

    Args:
        strategy: "react" | "reflexion"
        tools: dict of tool functions
    Returns:
        function nhận task string, trả về answer string
    Raises:
        ValueError nếu strategy không tồn tại
    """
    if strategy not in STRATEGY_REGISTRY:
        available = list_strategies()
        raise ValueError(
            f"Strategy '{strategy}' không tồn tại. "
            f"Các strategy có sẵn: {available}"
        )

    strategy_fn = STRATEGY_REGISTRY[strategy]
    # partial "đóng gói" tools vào strategy_fn
    # Kết quả: agent_fn(task) thay vì strategy_fn(task, tools)
    return partial(strategy_fn, tools=tools)


def run_unit_tests():
    """Test logic factory — không gọi LLM, chạy nhanh."""
    from tools.basic_tools import TOOLS

    # 1. list_strategies trả về đúng danh sách
    assert list_strategies() == ["react", "reflexion"], "list_strategies sai"

    # 2. create_agent trả về callable
    agent_fn = create_agent("react", TOOLS)
    assert callable(agent_fn), "create_agent phải trả về callable"

    # 3. partial object có .func và .keywords để kiểm tra nội dung bên trong
    #    mà không cần gọi LLM
    assert agent_fn.func is run_react_agent, "func phải là run_react_agent"
    assert agent_fn.keywords["tools"] is TOOLS, "tools phải được đóng gói đúng"

    # 4. reflexion tương tự
    agent_fn = create_agent("reflexion", TOOLS)
    assert agent_fn.func is run_with_reflexion

    # 5. strategy không hợp lệ phải raise ValueError với message rõ ràng
    try:
        create_agent("invalid_strategy", TOOLS)
        assert False, "Phải raise ValueError"
    except ValueError as e:
        assert "invalid_strategy" in str(e)
        assert "react" in str(e)   # error message phải gợi ý option hợp lệ

    print("✓ Unit tests passed (0 LLM calls)")


def run_integration_tests():
    """Test end-to-end với LLM thật — chạy có chủ đích, tốn token."""
    from tools.basic_tools import TOOLS

    print("\n[Integration] react agent...")
    react_agent = create_agent("react", TOOLS)
    answer = react_agent("Bây giờ là mấy giờ?")
    print(f"  Answer: {answer}")

    print("\n[Integration] reflexion agent...")
    reflexion_agent = create_agent("reflexion", TOOLS)
    answer = reflexion_agent("Bây giờ là mấy giờ?")
    print(f"  Answer: {answer}")

    print("✓ Integration tests passed")


if __name__ == "__main__":
    import sys
    # Mặc định chỉ chạy unit test — nhanh, free
    # Muốn chạy integration: python agent_factory.py --integration
    run_unit_tests()
    if "--integration" in sys.argv:
        run_integration_tests()
