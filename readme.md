在使用时，仅需要修改以下部分即可：

```python
client=OpenAI(

    api_key="你自己的api key",

    base_url="对应的url",

)
```


二：

```python
    # 依次输入：AI名称；性格和背景；使用的模型（默认为qwen3.5-plus）；
    def __init__(self, name: str, persona: str, model: str = "qwen3.5-plus"):
```

例如：

```python
agent_a = Agent("AI科学家", "一位极度理性、注重数据和逻辑的计算机科学家，认为一切都可以用算法解释。","glm-5")
```
