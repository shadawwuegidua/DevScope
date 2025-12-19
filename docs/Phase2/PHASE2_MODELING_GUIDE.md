# 📊 DevScope Phase 2 - 建模与统计分析指南

**版本**: Phase 2 v1.0  
**更新日期**: 2024-12-18  

---

## 1. 概述

Phase 2 实现了 DevScope 的核心数学建模层。本模块负责将原始的 GitHub 行为数据转化为可解释的概率预测。

**核心原则**：
- 严禁使用黑箱模型（如神经网络）。
- 所有预测基于统计分布（多项分布、Weibull 分布）。
- 必须提供自然语言解释。

---

## 2. 核心模型详解

### 2.1 技术倾向性预测 (Tendency Prediction)

**目标**：预测开发者未来参与某一技术主题的概率。

**数学模型**：多项分布 + 拉普拉斯平滑 (Laplace Smoothing)

$$P(T_i) = \frac{n_i + \alpha}{N + \alpha K}$$

- **$n_i$**: 历史项目中属于技术 $T_i$ 的数量。
- **$N$**: 总项目数。
- **$K$**: 技术类别的总数。
- **$\alpha$**: 平滑参数（防止零概率，默认取 1）。

**代码实现**: `modeling.calculate_topic_probability`

**示例输出**:
```json
{
    "Python": {
        "probability": 0.42,
        "explanation": "基于历史数据(12次)，参与概率为 42.0%"
    }
}
```

### 2.2 活跃时间分布拟合 (Time Distribution)

**目标**：预测开发者下一次活跃的时间间隔。

**数学模型**：Weibull 分布 (首选)

$$f(t) = \frac{k}{\lambda} \left(\frac{t}{\lambda}\right)^{k-1} e^{-(t/\lambda)^k}$$

- **$k$ (Shape)**: 形状参数。$k < 1$ 表示活跃率随时间降低（早期容易活跃），$k > 1$ 表示活跃率随时间增加。
- **$\lambda$ (Scale)**: 尺度参数，代表特征时间间隔。

**Fallback 机制**:
若 Weibull 拟合失败，自动降级为 **指数分布 (Exponential Distribution)**：
$$f(t) = \lambda e^{-\lambda t}$$

**代码实现**: `modeling.fit_time_distribution`

### 2.3 匹配度打分 (Match Score)

**目标**：量化开发者与特定技术栈的契合度。

**公式**:
$$Score = (P_{tendency} \times 0.7) + (P_{active} \times 0.3)$$

- **$P_{tendency}$**: 目标技术栈的倾向概率。
- **$P_{active}$**: 未来 30 天内的活跃概率。

**评级标准**:
- 0.8 - 1.0: 极高匹配
- 0.6 - 0.8: 高度匹配
- 0.4 - 0.6: 中等匹配
- < 0.4: 低度契合/不匹配

---

## 3. API 使用示例

### Python 调用

```python
from modeling import calculate_topic_probability, fit_time_distribution

# 1. 技术倾向
topics = ["Python", "Python", "JavaScript", "Go"]
probs = calculate_topic_probability(topics)
print(probs["Python"]["probability"]) # -> 0.4286

# 2. 时间预测
timestamps = [
    "2024-01-01T10:00:00Z",
    "2024-01-05T14:00:00Z",
    "2024-01-15T09:00:00Z"
]
time_pred = fit_time_distribution(timestamps)
print(time_pred["expected_interval_days"]) # -> 期望间隔天数
```

---

## 4. 异常处理规范

| 场景 | 处理方式 |
|------|---------|
| 项目数 < 5 | 触发冷启动，融合社区均值 |
| 时间戳 < 2 个 | 返回 "Insufficient Data"，无法预测 |
| 间隔 < 3 个 | 返回简单平均值 (Simple Mean) |
| 拟合报错 | 捕获异常，降级为指数分布或均值 |

---

## 5. 依赖库

- `scipy`: 用于 `weibull_min` 和 `expon` 分布拟合。
- `numpy`: 用于数值计算。
- `python-dateutil`: 用于 ISO 时间戳解析。
