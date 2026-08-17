# Week 2 — 神经网络与 PyTorch

> 本周目标：理解神经网络训练的完整闭环，并能独立写出一个 PyTorch 训练脚本，不把高级封装当作黑盒。

建议时间：8～10 小时。

---

## 1. 本周最终能力

- [ ] 理解 neuron / weight / bias。
- [ ] 理解 linear layer。
- [ ] 理解 activation function 为什么存在。
- [ ] 理解 ReLU / Sigmoid / Softmax 的典型用途。
- [ ] 理解 forward / loss / backward / optimizer step。
- [ ] 理解 autograd。
- [ ] 能自己写 Dataset / DataLoader。
- [ ] 能自己写 `nn.Module`。
- [ ] 能完成训练、验证、保存和加载。
- [ ] 能排查 shape / dtype / device 常见错误。

---

# 2. 学习资料

## 必读

- [PyTorch Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)
- [PyTorch Tensors](https://docs.pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html)
- [PyTorch Autograd](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- [PyTorch Build Model](https://docs.pytorch.org/tutorials/beginner/basics/buildmodel_tutorial.html)

## 强烈推荐

- [Karpathy - Neural Networks: Zero to Hero](https://karpathy.ai/zero-to-hero.html)

建议至少理解 `micrograd` 部分，真正理解计算图和反向传播。

---

# 3. Day 1 — 神经元与线性层

核心表达：

```text
y = xW + b
```

学习：

- Weight 表示输入特征对输出的影响。
- Bias 提供平移能力。
- 多个 neuron 组成一层。
- 多层线性变换如果没有非线性激活，本质仍可折叠为单个线性变换。

## 必答

1. 为什么需要 bias？
2. 为什么神经网络不能只有 Linear Layer 而没有 Activation？
3. 一个 `Linear(768, 3072)` 有多少 weight 参数？bias 有多少？
4. Batch Size 改变时，参数数量会不会变化？为什么？

## 实验

```text
week02_nn/01_linear.py
```

要求：

- [ ] 手动实现 `y = xW + b`。
- [ ] 再使用 `torch.nn.Linear` 实现。
- [ ] 对比输入输出 shape。
- [ ] 打印参数数量。
- [ ] 故意构造一个矩阵维度错误。

---

# 4. Day 2 — Activation 与 Loss

学习：

- ReLU
- Sigmoid
- Softmax
- MSE
- Cross Entropy

## 理解边界

- ReLU：隐藏层常见非线性。
- Sigmoid：二分类概率、门控等场景常见。
- Softmax：把多个 logits 转换为归一化分布。
- Cross Entropy：分类任务常见 Loss。

## 实验

对 logits：

```text
[2.0, 1.0, 0.1]
```

自己先按公式计算 Softmax，再与 PyTorch 输出对比。

## Debug 思考

- [ ] logits 很大时为什么直接 `exp()` 容易溢出？
- [ ] 为什么 PyTorch 的 CrossEntropyLoss 通常不需要自己先做 Softmax？

---

# 5. Day 3 — Backpropagation 与 Autograd

学习完整链路：

```text
forward
 ↓
loss
 ↓
backward
 ↓
gradients
 ↓
optimizer.step
```

必须理解：

- `requires_grad`
- computational graph
- `.grad`
- `.backward()`
- `optimizer.zero_grad()`

## 必答

1. 为什么 PyTorch 默认会累积 gradient？
2. 忘记 `zero_grad()` 会发生什么？
3. inference 为什么通常使用 `torch.no_grad()`？
4. 什么情况下需要 `detach()`？

## 实验

```text
week02_nn/02_autograd.py
```

打印：

- 参数初始值
- Forward 输出
- Loss
- Gradient
- Optimizer 更新后的参数值

要求能说明每一步为什么发生变化。

---

# 6. Day 4 — Dataset / DataLoader / Model

项目结构：

```text
week02_nn/
├── dataset.py
├── model.py
├── train.py
├── evaluate.py
└── README.md
```

要求：

- [ ] 自定义 `Dataset`。
- [ ] 使用 `DataLoader`。
- [ ] Training Data 支持 shuffle。
- [ ] Validation 阶段不错误使用训练状态。
- [ ] 正确使用 `model.train()` / `model.eval()`。
- [ ] 自定义 MLP。

模型建议：

```text
Input
 ↓
Linear
 ↓
ReLU
 ↓
Linear
 ↓
Output
```

---

# 7. Day 5 — 完整 Training Loop

必须独立写出：

```python
for epoch in range(...):
    model.train()
    for x, y in train_loader:
        ...

    model.eval()
    with torch.no_grad():
        ...
```

要求记录：

- training loss
- validation loss
- accuracy 或适合任务的指标
- 每个 epoch 耗时

保存模型：

```python
torch.save(model.state_dict(), ...)
```

然后重新加载，并完成 inference。

---

# 8. Device / dtype 基础

学习：

- CPU Tensor
- CUDA Tensor
- device
- dtype
- FP32 / FP16 / BF16 基础概念

代码至少支持：

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
```

主动制造：

- [ ] Model 在 GPU，Tensor 在 CPU。
- [ ] 输入 dtype 错误。
- [ ] 分类 label dtype 错误。
- [ ] 输入 shape 错误。

记录每个错误的异常信息、根因和修复方式。

---

# 9. Day 6 — 过拟合观察实验

准备一个很小的数据集。

逐渐增大模型容量或训练 epoch，观察：

```text
Training Loss ↓
Validation Loss 先 ↓ 后 ↑
```

思考：

- [ ] 为什么训练集继续变好，但验证集变差？
- [ ] Early Stopping 能解决什么？
- [ ] Weight Decay / Dropout 是什么方向的手段？
- [ ] 更多数据为什么往往有效？

本周只理解基本思想，不要求深入正则化理论。

---

# 10. Debug 训练

必须主动完成至少以下 5 类错误：

- [ ] Shape mismatch。
- [ ] dtype mismatch。
- [ ] CPU / GPU device mismatch。
- [ ] 忘记 `zero_grad()`。
- [ ] Learning Rate 太大导致 Loss 异常。

可选追加：

- [ ] 输入包含 NaN。
- [ ] label 范围不正确。
- [ ] 保存和加载模型结构不一致。

对每个问题写：

```text
症状：
异常信息：
根因：
定位过程：
修复方式：
如何预防：
```

---

# 11. 周测

## 理论题

- [ ] Weight 和 Bias 分别解决什么？
- [ ] 为什么需要非线性 Activation？
- [ ] ReLU 的作用是什么？
- [ ] Logits 和 Probability 有什么区别？
- [ ] Softmax 做了什么？
- [ ] Loss 与 Metric 的区别是什么？
- [ ] `backward()` 计算的是什么？
- [ ] 为什么 gradient 会累积？
- [ ] `model.train()` 和 `model.eval()` 有什么区别？
- [ ] `state_dict` 保存了什么？

## 编程题

不查看完整教程，从空文件开始实现一个两层 MLP 的：

- Dataset
- Model
- Training Loop
- Validation
- Save
- Load
- Inference

## Debug 题

给你一个报错：

```text
Expected all tensors to be on the same device
```

要求解释：

1. 可能原因。
2. 如何定位是哪一个 Tensor 在错误设备。
3. 如何设计代码避免问题再次发生。

## 架构思考题

为什么在生产训练系统中，需要把：

```text
Dataset
Model
Training
Evaluation
Checkpoint
Logging
```

拆成不同模块，而不是全部写在一个 `train.py` 中？

---

# 12. 本周评分

| 项目 | 满分 |
|---|---:|
| 基础概念 | 20 |
| 原理理解 | 20 |
| 编程实现 | 30 |
| Debug | 15 |
| Architecture | 15 |
| **总分** | **100** |

通过：≥80。

---

# 13. 本周验收

- [ ] 理论测试 ≥80%。
- [ ] 独立写出完整训练循环。
- [ ] 能保存和恢复模型。
- [ ] 至少完成 5 个 Debug 场景。
- [ ] 能解释 Forward → Loss → Backward → Update。
- [ ] 能解释 `train()` / `eval()` / `no_grad()`。
- [ ] 已更新 `PROGRESS.md`。

完成后再进入 Week 3：Tokenizer 与 Language Modeling。
