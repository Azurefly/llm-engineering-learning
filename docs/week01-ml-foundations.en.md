# Week 1 — Math & Machine Learning Foundations

> Goal: learn only the math and machine-learning foundations required to understand embeddings, neural networks, and attention. The objective is engineering fluency, not a full mathematics curriculum.

Recommended time: 6–8 hours.

---

## 1. Final Capabilities for This Week

- [ ] Distinguish scalar / vector / matrix / tensor.
- [ ] Explain shape, transpose, and matrix multiplication.
- [ ] Compute a simple dot product manually.
- [ ] Implement cosine similarity from scratch.
- [ ] Explain derivative, partial derivative, and gradient.
- [ ] Explain gradient descent.
- [ ] Explain what happens when the learning rate is too large or too small.
- [ ] Explain the roles of train / validation / test sets.
- [ ] Explain overfitting / underfitting.
- [ ] Explain regression / classification.
- [ ] Read and explain `X @ W + b`.
- [ ] Implement minimal linear regression using NumPy.

---

# 2. Learning Resources

## Required

1. [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course)
2. [Dive into Deep Learning](https://d2l.ai/)
3. [D2L Preliminaries](https://d2l.ai/chapter_preliminaries/index.html)

## Recommended for Intuition

- [3Blue1Brown](https://www.3blue1brown.com/)

Search for:

- Essence of Linear Algebra
- Gradient Descent
- Neural Networks

---

# 3. Day 1 — Vectors & Matrices

Recommended time: 60–90 minutes.

## Theory

Study:

- scalar
- vector
- dimension
- matrix
- tensor
- shape
- transpose
- element-wise operations
- dot product
- matrix multiplication

You should answer:

1. How many dimensions does `[1,2,3]` have as a vector?
2. What could a shape of `(32, 768)` represent?
3. Why is `(32,768) @ (768,3072)` valid? What is the output shape?
4. What is the difference between dot product and element-wise multiplication?

## Lab

Create:

```text
week01_ml/01_vector_matrix.py
```

Requirements:

- [ ] Create a one-dimensional vector.
- [ ] Create a two-dimensional matrix.
- [ ] Print shapes.
- [ ] Transpose a matrix.
- [ ] Perform element-wise multiplication.
- [ ] Perform matrix multiplication.
- [ ] Deliberately trigger a shape mismatch and record the error.

---

# 4. Day 2 — Cosine Similarity

## Theory

Formula:

```text
cos(A,B) = A·B / (||A|| ||B||)
```

Understand:

- Dot product is affected by both direction and magnitude.
- Cosine similarity focuses on directional similarity.
- Embedding systems often use cosine similarity or normalized dot product for semantic comparison.

## Lab

Create:

```text
week01_ml/02_cosine.py
```

Do not use sklearn in the first implementation.

Implement:

```python
def cosine_similarity(a, b):
    ...
```

Test:

```text
[1,0] vs [1,0]   → approximately 1
[1,0] vs [0,1]   → approximately 0
[1,0] vs [-1,0]  → approximately -1
```

Failure cases:

- [ ] What should happen with a zero vector?
- [ ] What should happen if dimensions differ?
- [ ] What should happen if input contains NaN?

---

# 5. Day 3 — Derivatives, Gradients & Gradient Descent

## Only Learn What You Need

- function
- derivative
- partial derivative
- chain rule
- gradient
- gradient descent

Do not spend this week on advanced integration techniques.

## Core Intuition

Think of the loss function as a landscape.

The gradient points toward the direction of fastest increase, so parameter updates normally move in the opposite direction:

```text
parameter = parameter - learning_rate * gradient
```

## Questions

- Why is there a minus sign?
- Why cannot the learning rate be arbitrarily large?
- Does gradient = 0 always mean the global optimum has been found?

## Lab

Create:

```text
week01_ml/03_gradient_descent.py
```

Optimize:

```text
f(x) = (x - 3)^2
```

Start from:

```text
x = 100
```

and move x toward 3.

Test:

- [ ] lr = 0.001
- [ ] lr = 0.1
- [ ] lr = 1
- [ ] lr = 10

Record the behavior of each learning rate.

---

# 6. Day 4 — Basic Machine Learning Workflow

Study:

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

## Questions

1. Why should the test set not be used repeatedly for tuning during training?
2. What does low training loss but high validation loss usually indicate?
3. Why are very small datasets more vulnerable to overfitting?
4. Is accuracy appropriate for every classification problem?

---

# 7. Day 5 — Mini Linear Regression

Goal: understand training without depending on a deep-learning framework.

True function:

```text
y = 2x + 1 + noise
```

Learnable parameters:

```text
w
b
```

Prediction:

```text
y_hat = w*x + b
```

Loss: MSE.

Requirements:

- [ ] Randomly initialize w and b.
- [ ] Implement forward calculation.
- [ ] Compute loss.
- [ ] Compute gradients.
- [ ] Update parameters.
- [ ] Train for at least 500 steps.
- [ ] Final w should be close to 2.
- [ ] Final b should be close to 1.
- [ ] Record loss values over time.

File:

```text
week01_ml/04_linear_regression.py
```

---

# 8. Debugging Practice

Deliberately create these problems:

- [ ] Matrix shape mismatch.
- [ ] Learning rate too large, causing divergence.
- [ ] Learning rate too small, causing almost no progress.
- [ ] Input data containing NaN.
- [ ] Compare training before and after normalization.

For every problem, write:

```text
Symptom:
Cause:
How I located it:
Fix:
Why the fix works:
```

---

# 9. Weekly Test

## Theory

- [ ] What is vector dimensionality?
- [ ] What does a dot product compute?
- [ ] Why does cosine similarity focus on direction rather than absolute distance?
- [ ] Is a gradient a scalar or a vector?
- [ ] Why can gradient descent oscillate?
- [ ] What happens when the learning rate is too small?
- [ ] Why does a validation set exist?
- [ ] What is overfitting?
- [ ] What is generalization?
- [ ] What is a typical output difference between regression and classification?

## Coding

Without sklearn, implement cosine similarity and linear regression.

## Architecture Question

If you need to compare one query embedding against one million stored embeddings, why is a Python `for` loop over all vectors usually not the right production solution? What technologies or indexing strategies would you consider next?

---

# 10. Acceptance Criteria

Mark Week 1 complete only when all conditions are met:

- [ ] Theory score ≥ 80%.
- [ ] Cosine similarity implemented independently.
- [ ] Linear regression implemented independently.
- [ ] At least three debugging scenarios completed.
- [ ] Can explain `X @ W + b`.
- [ ] Can explain gradient descent.
- [ ] Score recorded in `PROGRESS.en.md`.
