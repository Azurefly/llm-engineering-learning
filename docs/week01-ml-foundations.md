# Week 1 — 数学与机器学习基础

> 本周目标：只补后续 LLM 工程真正需要的数学和机器学习基础。完成后应能看懂 Embedding、神经网络、Attention 中的向量/矩阵运算，并理解训练到底在做什么。

建议时间：6～8 小时。

---

## 1. 本周最终能力

- [ ] 能区分 scalar / vector / matrix / tensor。
- [ ] 能解释 shape、transpose、matrix multiplication。
- [ ] 能手算简单 dot product。
- [ ] 能自己实现 cosine similarity。
- [ ] 能解释 derivative、partial derivative、gradient。
- [ ] 能解释 gradient descent。
- [ ] 能解释 learning rate 太大/太小的表现。
- [ ] 能解释 train / validation / test 的用途。
- [ ] 能解释 overfitting / underfitting。
- [ ] 能解释 regression / classification。
- [ ] 能看懂 `X @ W + b`。
- [ ] 能用 NumPy 写最小线性回归训练。

---

# 2. 学习资料

## 必读

1. [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course)
2. [动手学深度学习 D2L 中文版](https://zh.d2l.ai/)
3. [D2L 预备知识](https://zh.d2l.ai/chapter_preliminaries/index.html)

## 推荐直觉课程

- [3Blue1Brown](https://www.3blue1brown.com/)

重点搜索：

- Essence of Linear Algebra
- Gradient Descent
- Neural Networks

---

# 3. Day 1 — 向量与矩阵

建议 60～90 分钟。

## 理论

学习：

- scalar
- vector
- dimension
- matrix
- tensor
- shape
- transpose
- element-wise operation
- dot product
- matrix multiplication

必须自己回答：

1. `[1,2,3]` 是几维向量？
2. `(32, 768)` 可能表示什么？
3. 为什么 `(32,768) @ (768,3072)` 合法？结果 shape 是多少？
4. Dot Product 与 element-wise multiply 有什么区别？

## 实验

创建：

```text
week01_ml/01_vector_matrix.py
```

要求：

- [ ] 创建一维 vector。
- [ ] 创建二维 matrix。
- [ ] 输出 shape。
- [ ] transpose。
- [ ] element-wise multiply。
- [ ] matrix multiply。
- [ ] 故意制造一次 shape mismatch 并记录错误。

---

# 4. Day 2 — Cosine Similarity

## 理论

公式：

```text
cos(A,B) = A·B / (||A|| ||B||)
```

理解：

- Dot Product 同时受到方向和长度影响。
- Cosine 更关注方向相似性。
- Embedding 常常使用 cosine / normalized dot product 比较语义。

## 实验

文件：

```text
week01_ml/02_cosine.py
```

禁止第一版直接调用 sklearn。

自己实现：

```python
def cosine_similarity(a, b):
    ...
```

测试：

```text
[1,0] vs [1,0]   → 约 1
[1,0] vs [0,1]   → 约 0
[1,0] vs [-1,0]  → 约 -1
```

异常测试：

- [ ] 零向量怎么办？
- [ ] 两个向量维度不同怎么办？
- [ ] 输入包含 NaN 怎么处理？

---

# 5. Day 3 — 导数、梯度和梯度下降

## 只需要理解这些

- function
- derivative
- partial derivative
- chain rule
- gradient
- gradient descent

不要把时间花在复杂积分。

## 核心直觉

把 Loss 看成地形高度。

Gradient 指向“增长最快”的方向，因此参数更新通常走：

```text
parameter = parameter - learning_rate * gradient
```

## 必答

- 为什么是减号？
- learning rate 为什么不能无限大？
- gradient=0 是否一定找到全局最优？

## 实验

```text
week01_ml/03_gradient_descent.py
```

对：

```text
f(x) = (x - 3)^2
```

从：

```text
x = 100
```

逐渐优化到接近 3。

分别测试：

- [ ] lr = 0.001
- [ ] lr = 0.1
- [ ] lr = 1
- [ ] lr = 10

记录每种学习率的行为。

---

# 6. Day 4 — 机器学习基本流程

学习：

- dataset
- feature
- label
- train set
- validation set
- test set
- regression
- classification
- loss
- metric
- generalization
- overfitting
- underfitting

## 必答问题

1. 为什么 Test Set 不能在训练过程中反复调参？
2. Training Loss 很低但 Validation Loss 很高意味着什么？
3. 数据量非常少时为什么更容易过拟合？
4. Accuracy 是否适合所有分类问题？

---

# 7. Day 5 — Mini Linear Regression

目标：不依赖深度学习框架理解训练。

真实函数：

```text
y = 2x + 1 + noise
```

待学习参数：

```text
w
b
```

预测：

```text
y_hat = w*x + b
```

Loss：MSE。

要求：

- [ ] 随机初始化 w/b。
- [ ] forward。
- [ ] loss。
- [ ] gradient。
- [ ] update。
- [ ] 训练至少 500 step。
- [ ] 最终 w 接近 2。
- [ ] 最终 b 接近 1。
- [ ] 输出 loss 曲线数据。

文件：

```text
week01_ml/04_linear_regression.py
```

---

# 8. Debug 训练

本周主动制造以下问题：

- [ ] Matrix shape mismatch。
- [ ] learning rate 过大导致发散。
- [ ] learning rate 过小导致训练几乎不动。
- [ ] 输入数据包含 NaN。
- [ ] 标准化前后训练速度变化。

每个问题写：

```text
症状：
原因：
定位方法：
修复方式：
为什么这样修：
```

---

# 9. 周测

## 理论题

- [ ] 什么是向量维度？
- [ ] Dot Product 在计算什么？
- [ ] Cosine Similarity 为什么不直接比较绝对距离？
- [ ] Gradient 是标量还是向量？
- [ ] Gradient Descent 为什么可能震荡？
- [ ] Learning Rate 太小有什么表现？
- [ ] Validation Set 为什么存在？
- [ ] 什么是 Overfitting？
- [ ] 什么是 Generalization？
- [ ] Regression 与 Classification 的输出有什么典型差异？

## 编程题

不用 sklearn，完成 cosine similarity + linear regression。

## 架构思考题

如果未来要比较 100 万个 Embedding 与一个 Query 的相似度，为什么不能简单 Python `for` 逐条计算？下一步需要什么技术？

---

# 10. 本周验收

满足全部条件才勾选 Week 1 完成：

- [ ] 理论测试 ≥ 80%。
- [ ] cosine similarity 独立实现。
- [ ] linear regression 独立实现。
- [ ] 至少完成 3 个 Debug 场景。
- [ ] 能解释 `X @ W + b`。
- [ ] 能解释 Gradient Descent。
- [ ] 已把分数记录到 `PROGRESS.md`。
