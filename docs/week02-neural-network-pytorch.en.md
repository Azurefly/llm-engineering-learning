# Week 2 — Neural Networks & PyTorch

> Goal: understand the complete neural-network training loop and independently write a PyTorch training script without treating high-level abstractions as a black box.

Recommended time: 8–10 hours.

---

## 1. Final Capabilities for This Week

- [ ] Understand neurons, weights, and biases.
- [ ] Understand linear layers.
- [ ] Explain why activation functions are necessary.
- [ ] Understand typical uses of ReLU, sigmoid, and softmax.
- [ ] Understand forward → loss → backward → optimizer step.
- [ ] Understand autograd.
- [ ] Implement a Dataset and DataLoader.
- [ ] Implement an `nn.Module`.
- [ ] Train, validate, save, and reload a model.
- [ ] Debug common shape, dtype, and device problems.

---

# 2. Learning Resources

## Required

- [PyTorch Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)
- [PyTorch Tensors](https://docs.pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html)
- [PyTorch Autograd](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)
- [PyTorch Build Model](https://docs.pytorch.org/tutorials/beginner/basics/buildmodel_tutorial.html)

## Strongly Recommended

- [Karpathy — Neural Networks: Zero to Hero](https://karpathy.ai/zero-to-hero.html)

At minimum, understand the `micrograd` section so the computation graph and backpropagation are not mysterious abstractions.

---

# 3. Day 1 — Neurons & Linear Layers

Core expression:

```text
y = xW + b
```

Learn:

- Weights represent how input features influence outputs.
- Bias provides an additive offset.
- Multiple neurons form a layer.
- Stacking linear transformations without nonlinear activations still collapses into an overall linear transformation.

## Questions

1. Why is bias needed?
2. Why can a useful neural network not consist only of linear layers without nonlinear activations?
3. How many weight parameters and bias parameters does `Linear(768, 3072)` contain?
4. Does changing batch size change the number of model parameters? Why?

## Lab

```text
week02_nn/01_linear.py
```

Requirements:

- [ ] Implement `y = xW + b` manually.
- [ ] Reimplement it with `torch.nn.Linear`.
- [ ] Compare input/output shapes.
- [ ] Print parameter counts.
- [ ] Deliberately trigger a dimension mismatch.

---

# 4. Day 2 — Activations & Loss Functions

Study:

- ReLU
- Sigmoid
- Softmax
- MSE
- Cross Entropy

## Understand the Typical Roles

- ReLU: common nonlinearity in hidden layers.
- Sigmoid: common for binary probabilities and gating mechanisms.
- Softmax: converts multiple logits into a normalized distribution.
- Cross Entropy: common classification loss.

## Lab

For logits:

```text
[2.0, 1.0, 0.1]
```

calculate softmax manually, then compare with PyTorch.

## Debugging Questions

- [ ] Why can directly applying `exp()` to very large logits cause numerical overflow?
- [ ] Why does PyTorch `CrossEntropyLoss` usually not require manually applying softmax first?

---

# 5. Day 3 — Backpropagation & Autograd

Study the full chain:

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

You must understand:

- `requires_grad`
- computation graph
- `.grad`
- `.backward()`
- `optimizer.zero_grad()`

## Questions

1. Why does PyTorch accumulate gradients by default?
2. What happens if `zero_grad()` is forgotten?
3. Why is `torch.no_grad()` normally used during inference?
4. When can `detach()` be useful?

## Lab

```text
week02_nn/02_autograd.py
```

Print:

- initial parameter values
- forward output
- loss
- gradients
- parameter values after the optimizer step

Be able to explain why every value changes.

---

# 6. Day 4 — Dataset / DataLoader / Model

Project structure:

```text
week02_nn/
├── dataset.py
├── model.py
├── train.py
├── evaluate.py
└── README.md
```

Requirements:

- [ ] Implement a custom `Dataset`.
- [ ] Use a `DataLoader`.
- [ ] Shuffle training data.
- [ ] Avoid accidentally using training behavior during validation.
- [ ] Correctly use `model.train()` / `model.eval()`.
- [ ] Build a custom MLP.

Suggested model:

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

# 7. Day 5 — Complete Training Loop

Independently write:

```python
for epoch in range(...):
    model.train()
    for x, y in train_loader:
        ...

    model.eval()
    with torch.no_grad():
        ...
```

Record:

- training loss
- validation loss
- accuracy or another suitable metric
- epoch duration

Save the model:

```python
torch.save(model.state_dict(), ...)
```

Then reload it and run inference.

---

# 8. Device & dtype Basics

Study:

- CPU tensors
- CUDA tensors
- device
- dtype
- basic FP32 / FP16 / BF16 concepts

Your code should support at least:

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
```

Deliberately create:

- [ ] Model on GPU while tensor remains on CPU.
- [ ] Wrong input dtype.
- [ ] Wrong classification-label dtype.
- [ ] Wrong input shape.

Record the exception, root cause, and fix for each failure.

---

# 9. Day 6 — Observe Overfitting

Prepare a deliberately small dataset.

Increase model capacity or training epochs and observe the common pattern:

```text
Training Loss ↓
Validation Loss ↓ then ↑
```

Think about:

- [ ] Why can training continue improving while validation gets worse?
- [ ] What problem does early stopping address?
- [ ] What kinds of techniques are weight decay and dropout?
- [ ] Why does adding more high-quality data often help?

Only understand the core intuition this week; advanced regularization theory can wait.

---

# 10. Debugging Practice

You must deliberately complete at least these five failure cases:

- [ ] Shape mismatch.
- [ ] dtype mismatch.
- [ ] CPU/GPU device mismatch.
- [ ] Forgotten `zero_grad()`.
- [ ] Learning rate so large that loss becomes unstable.

Optional additions:

- [ ] Input containing NaN.
- [ ] Invalid label range.
- [ ] Incompatible model architecture during checkpoint loading.

For every issue, write:

```text
Symptom:
Exception:
Root cause:
Debugging process:
Fix:
Prevention:
```

---

# 11. Weekly Test

## Theory

- [ ] What roles do weights and biases play?
- [ ] Why are nonlinear activation functions needed?
- [ ] What does ReLU do?
- [ ] What is the difference between logits and probabilities?
- [ ] What does softmax do?
- [ ] What is the difference between a loss function and a metric?
- [ ] What does `backward()` calculate?
- [ ] Why do gradients accumulate?
- [ ] What is the purpose of `model.train()` and `model.eval()`?
- [ ] What does `state_dict` contain?

## Coding

Without consulting a full tutorial, start from empty files and implement a two-layer MLP with:

- Dataset
- Model
- Training loop
- Validation
- Save
- Load
- Inference

## Debugging Question

Given:

```text
Expected all tensors to be on the same device
```

explain:

1. Likely causes.
2. How to determine which tensor is on the wrong device.
3. How to structure code so the problem is less likely to recur.

## Architecture Question

Why should a production training project separate:

```text
Dataset
Model
Training
Evaluation
Checkpoint
Logging
```

instead of placing everything into one large `train.py` file?

---

# 12. Weekly Scoring

| Area | Max |
|---|---:|
| Concepts | 20 |
| Principles | 20 |
| Implementation | 30 |
| Debugging | 15 |
| Architecture | 15 |
| **Total** | **100** |

Pass: ≥80.

---

# 13. Acceptance Criteria

- [ ] Theory score ≥80%.
- [ ] Complete training loop implemented independently.
- [ ] Model can be saved and restored.
- [ ] At least five debugging scenarios completed.
- [ ] Can explain Forward → Loss → Backward → Update.
- [ ] Can explain `train()` / `eval()` / `no_grad()`.
- [ ] `PROGRESS.en.md` updated.

After completing these requirements, continue to Week 3: Tokenizers & Language Modeling.
