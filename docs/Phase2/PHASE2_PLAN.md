# 🚀 DevScope Phase 2 实施计划

**创建日期**: 2024-12-18  
**版本**: v1.0  
**状态**: 📋 规划完成，开始实施  

---

## 📋 Phase 2 目标

Phase 2 的核心目标是**实现数学建模层（Mathematical Modeling）**，在 Phase 1 数据抓取和预置的基础上，构建开发者行为预测和技术画像的统计模型。

**关键原则**：
- ✅ **可解释性优先**：所有预测必须基于统计学原理，严禁使用黑箱 ML/DL 模型
- ✅ **数学公式驱动**：每个函数都有清晰的数学公式和 Docstring
- ✅ **异常处理完善**：对数据不足、拟合失败等情况有 Fallback 机制
- ✅ **纯函数设计**：便于测试和维护

---

## 🎯 核心功能清单

### 1. 技术倾向性预测 (`calculate_topic_probability`)

**数学原理**：基于多项分布的拉普拉斯平滑

**公式**：
$$P(T_i) = \frac{n_i + \alpha}{N + \alpha K}$$

其中：
- $n_i$: 技术领域 $T_i$ 的项目数
- $N$: 总项目数
- $K$: 技术类别总数
- $\alpha$: 平滑参数（通常取 1）

**输入**：
```python
topics: List[str]  # 用户项目的话题/语言列表
alpha: float = 1.0  # 拉普拉斯平滑参数
```

**输出**：
```python
{
    "Python": {
        "probability": 0.42,
        "count": 12,
        "explanation": "基于历史数据，该开发者参与 Python 项目的概率为 42%"
    },
    "JavaScript": {...},
    ...
}
```

**特殊处理**：
- 冷启动场景（$N < 5$）：融合社区均值
- 空数据：返回均匀分布

---

### 2. 活跃时间分布拟合 (`fit_time_distribution`)

**数学原理**：基于时间间隔序列的连续概率分布拟合

#### 方案 A：Weibull 分布（推荐）
$$f(t) = \frac{k}{\lambda} \left(\frac{t}{\lambda}\right)^{k-1} e^{-(t/\lambda)^k}$$

- 参数：$k$ (形状参数), $\lambda$ (尺度参数)
- 适用场景：活跃率随时间变化

#### 方案 B：指数分布（备选）
$$f(t) = \lambda e^{-\lambda t}$$

- 参数：$\lambda$ (率参数)
- 适用场景：无记忆随机过程

**输入**：
```python
timestamps: List[str]  # ISO 格式时间戳列表
# 例如：["2024-01-15T10:30:00Z", "2024-02-20T14:20:00Z", ...]
```

**输出**：
```python
{
    "distribution_type": "Weibull",  # 或 "Exponential"
    "params": {
        "shape": 1.35,  # Weibull k 参数
        "scale": 45.2,  # Weibull λ 参数（天）
    },
    "expected_interval_days": 42.5,  # 期望间隔
    "next_active_prob_30d": 0.58,   # 未来30天活跃概率
    "intervals": [35, 42, 50, ...],  # 实际间隔序列（天）
    "explanation": "基于 Weibull 分布拟合，预测下次活跃时间约为 42.5 天"
}
```

**拟合逻辑**：
1. 计算时间间隔序列 $\Delta t_i = t_{i+1} - t_i$（单位：天）
2. 使用 `scipy.stats.weibull_min.fit()` 拟合参数
3. 计算 CDF: $P(T \le 30) = 1 - e^{-(30/\lambda)^k}$
4. 如果 Weibull 拟合失败，降级为指数分布
5. 如果间隔数 < 3，返回社区均值参数

---

### 3. 匹配度打分模型 (`calculate_match_score`)

**数学原理**：技术倾向 + 活跃概率的加权组合

**公式**：
$$\text{Score} = P_{tendency} \times 0.7 + P_{active} \times 0.3$$

**输入**：
```python
tech_tendency: Dict[str, float]  # 技术倾向分布
target_tech: str                 # 目标技术栈，如 "Python"
active_prob_30d: float           # 未来30天活跃概率
```

**输出**：
```python
{
    "score": 0.85,           # 0.0 - 1.0
    "level": "极高匹配",      # 匹配等级
    "tech_contribution": 0.595,  # 技术倾向贡献 (0.85 * 0.7)
    "active_contribution": 0.255, # 活跃概率贡献 (0.85 * 0.3)
    "explanation": "该开发者与 Python 技术栈极高匹配（85分），技术倾向强（0.85）且近期活跃度高（0.85）"
}
```

**匹配等级**：
- `>= 0.8`: "极高匹配"
- `>= 0.6`: "高度匹配"
- `>= 0.4`: "中等匹配"
- `>= 0.2`: "低度契合"
- `< 0.2`: "不匹配"

---

### 4. 权重融合函数增强 (`blend_user_and_community` - 已在 Phase 1)

Phase 1 已实现基础版本，Phase 2 需要确保与新功能的集成。

---

## 📁 文件结构

### Phase 2 新增/修改文件

```
backend/
├── modeling.py                    # 🆕 扩展：添加 Phase 2 核心建模函数
├── test_modeling_phase2.py        # 🆕 Phase 2 建模功能测试
├── verify_phase2_complete.py     # 🆕 Phase 2 综合验证脚本
├── PHASE2_MODELING_GUIDE.md      # 🆕 Phase 2 建模详细指南
├── PHASE2_SUMMARY.md             # 🆕 Phase 2 完成总结
├── QUICK_REFERENCE.md            # 🔄 更新：添加 Phase 2 API 快速参考
└── README.md                      # 🔄 更新：添加 Phase 2 使用说明
```

---

## 🔧 实施步骤

### Step 1: 扩展 `modeling.py`

在现有 Phase 1 的 `modeling.py` 基础上，添加以下函数：

#### 1.1 技术倾向性预测
```python
def calculate_topic_probability(
    topics: List[str],
    alpha: float = 1.0,
    community_average: Optional[Dict[str, float]] = None,
    confidence_weight: float = 1.0,
) -> Dict[str, Dict[str, Any]]:
    """
    计算技术倾向概率（拉普拉斯平滑）
    """
    # 实现拉普拉斯平滑
    # 融合社区均值（如果冷启动）
    # 生成解释文本
    pass
```

#### 1.2 时间分布拟合
```python
def fit_time_distribution(
    timestamps: List[str],
    fallback_to_exponential: bool = True,
) -> Dict[str, Any]:
    """
    拟合活跃时间分布（Weibull 或 Exponential）
    """
    # 解析时间戳
    # 计算间隔
    # 拟合 Weibull
    # 计算 CDF
    # 异常处理 + Fallback
    pass
```

#### 1.3 匹配度打分
```python
def calculate_match_score(
    tech_tendency: Dict[str, float],
    target_tech: str,
    active_prob_30d: float,
    tech_weight: float = 0.7,
    active_weight: float = 0.3,
) -> Dict[str, Any]:
    """
    计算开发者与技术栈的匹配度
    """
    # 加权计算
    # 分级判断
    # 生成解释
    pass
```

#### 1.4 辅助函数
```python
def parse_timestamps_to_intervals(timestamps: List[str]) -> List[float]:
    """将 ISO 时间戳转换为间隔序列（天）"""
    pass

def get_distribution_explanation(dist_type: str, params: Dict) -> str:
    """生成分布解释文本"""
    pass

def get_match_level(score: float) -> str:
    """根据分数返回匹配等级"""
    pass
```

---

### Step 2: 编写测试脚本

创建 `test_modeling_phase2.py`，测试所有新功能：

```python
# 测试用例：
# 1. 拉普拉斯平滑 - 正常场景
# 2. 拉普拉斯平滑 - 冷启动场景
# 3. Weibull 拟合 - 充分数据
# 4. Weibull 拟合 - Fallback 到指数分布
# 5. 匹配度打分 - 各种分数段
# 6. 时间戳解析 - 边界条件
```

---

### Step 3: 创建文档

#### 3.1 `PHASE2_MODELING_GUIDE.md`
- 数学原理详解
- 函数 API 文档
- 使用示例
- 常见问题

#### 3.2 `PHASE2_SUMMARY.md`
- Phase 2 完成情况总结
- 测试结果汇总
- 与 Phase 1 的集成说明

#### 3.3 更新 `README.md`
- 添加 Phase 2 使用示例
- 更新安装依赖说明

#### 3.4 更新 `QUICK_REFERENCE.md`
- 添加 Phase 2 函数快速参考

---

### Step 4: 验证与测试

创建 `verify_phase2_complete.py`，验证：

1. ✅ 所有 Phase 2 函数可调用
2. ✅ 数学公式计算正确
3. ✅ 异常处理有效
4. ✅ 与 Phase 1 集成无误
5. ✅ 文档完整齐全

---

## 📊 依赖库

Phase 2 需要的 Python 库（应已在 Phase 1 安装）：

```txt
scipy>=1.9.0        # Weibull/指数分布拟合
numpy>=1.23.0       # 数值计算
pandas>=1.5.0       # 数据处理（可选）
python-dateutil     # 时间戳解析
```

如需新增，更新 `requirements.txt`。

---

## ⚠️ 关键注意事项

### 1. 数学公式规范
- 所有函数 Docstring 必须包含 LaTeX 格式的数学公式
- 公式必须与 Prompt_context.md 一致

### 2. 可解释性
- 每个预测结果都要生成自然语言解释
- 使用"倾向于"、"概率为"等词汇，避免确定性表述

### 3. 异常处理
- 数据不足（< 5 项目）：触发冷启动
- 拟合失败：降级为指数分布或社区均值
- 无效输入：返回友好错误信息

### 4. 纯函数设计
- 所有建模函数应为纯函数（无副作用）
- 便于单元测试和调试

### 5. 性能考虑
- Weibull 拟合可能耗时，考虑缓存
- 大批量计算时可使用向量化

---

## 🎯 成功标准

Phase 2 完成的判定标准：

- ✅ `modeling.py` 包含所有 4 个核心函数
- ✅ 所有函数通过单元测试
- ✅ 与 Phase 1 代码集成测试通过
- ✅ 文档完整（至少 3 个 MD 文件）
- ✅ 验证脚本 100% 通过
- ✅ 可以对真实 GitHub 用户生成完整画像

---

## 📅 时间规划

| 步骤 | 预计时间 |
|------|---------|
| Step 1: 扩展 modeling.py | 60分钟 |
| Step 2: 编写测试脚本 | 30分钟 |
| Step 3: 创建文档 | 30分钟 |
| Step 4: 验证与测试 | 20分钟 |
| **总计** | **~2.5小时** |

---

## 🚀 开始实施

准备开始 Phase 2 实施！

**下一步**：扩展 `modeling.py`，实现技术倾向性预测函数。
